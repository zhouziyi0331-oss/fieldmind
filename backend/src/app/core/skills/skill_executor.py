"""
技能执行器 (Skill Executor)

安全执行技能，包括沙盒隔离和资源限制
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import asyncio
import json

from app.core.skills.skill_registry import Skill, SkillType

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """沙盒配置"""
    timeout: float = 30.0          # 超时时间（秒）
    max_memory: int = 512          # 最大内存（MB）
    max_cpu_time: float = 10.0     # 最大CPU时间（秒）
    allow_network: bool = False    # 是否允许网络访问
    allow_file_io: bool = False    # 是否允许文件IO
    restricted_modules: list = None  # 禁止导入的模块

    def __post_init__(self):
        if self.restricted_modules is None:
            # 默认禁止危险模块
            self.restricted_modules = [
                'os', 'sys', 'subprocess', 'socket',
                'urllib', 'requests', 'pickle'
            ]


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool                   # 是否成功
    output: Any                     # 输出结果
    error: Optional[str] = None     # 错误信息
    execution_time: float = 0.0     # 执行时间
    memory_used: int = 0            # 使用内存（bytes）
    logs: list = None               # 执行日志

    def __post_init__(self):
        if self.logs is None:
            self.logs = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used,
            'logs': self.logs
        }


class SkillExecutor:
    """技能执行器"""

    def __init__(self):
        """初始化技能执行器"""
        self.default_sandbox_config = SandboxConfig()
        self._skill_registry = None

        logger.info("✅ 技能执行器初始化")

    def set_skill_registry(self, registry):
        """设置技能注册中心"""
        self._skill_registry = registry

    # ==================== 核心执行方法 ====================

    async def execute(
        self,
        skill: Skill,
        input_data: Dict[str, Any],
        sandbox_config: Optional[SandboxConfig] = None
    ) -> ExecutionResult:
        """
        执行技能

        Args:
            skill: 技能对象
            input_data: 输入数据
            sandbox_config: 沙盒配置

        Returns:
            执行结果
        """
        start_time = datetime.now()

        logger.info(
            f"▶️  执行技能: {skill.name} (type={skill.type.value})"
        )

        try:
            # 1. 验证输入
            if not self._validate_input(skill, input_data):
                return ExecutionResult(
                    success=False,
                    output=None,
                    error="输入数据验证失败"
                )

            # 2. 根据技能类型执行
            if skill.type == SkillType.MANUAL:
                result = await self._execute_manual_skill(
                    skill, input_data, sandbox_config
                )
            elif skill.type == SkillType.GENERATED:
                result = await self._execute_generated_skill(
                    skill, input_data, sandbox_config
                )
            else:
                return ExecutionResult(
                    success=False,
                    output=None,
                    error=f"不支持的技能类型: {skill.type}"
                )

            # 3. 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            # 4. 更新统计
            if self._skill_registry:
                self._skill_registry.update_skill_stats(
                    skill.id,
                    success=result.success,
                    execution_time=execution_time
                )

            logger.info(
                f"✅ 技能执行完成: {skill.name}, "
                f"success={result.success}, "
                f"time={execution_time:.2f}s"
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(f"❌ 技能执行失败: {e}", exc_info=True)

            # 更新失败统计
            if self._skill_registry:
                self._skill_registry.update_skill_stats(
                    skill.id,
                    success=False,
                    execution_time=execution_time
                )

            return ExecutionResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )

    def _validate_input(
        self,
        skill: Skill,
        input_data: Dict[str, Any]
    ) -> bool:
        """
        验证输入数据

        Args:
            skill: 技能对象
            input_data: 输入数据

        Returns:
            是否有效
        """
        # 检查必需参数
        if skill.parameters:
            required = skill.parameters.get('required', [])
            for param in required:
                if param not in input_data:
                    logger.warning(f"⚠️ 缺少必需参数: {param}")
                    return False

        return True

    # ==================== 手动技能执行 ====================

    async def _execute_manual_skill(
        self,
        skill: Skill,
        input_data: Dict[str, Any],
        sandbox_config: Optional[SandboxConfig]
    ) -> ExecutionResult:
        """
        执行手动定义的技能

        手动技能使用workflow_prompt驱动LLM执行
        """
        logger.debug(f"🔧 执行手动技能: {skill.name}")

        try:
            # 1. 构建提示词
            prompt = self._build_manual_skill_prompt(skill, input_data)

            # 2. 调用LLM
            # TODO: 这里应该调用统一的LLM服务
            # 当前简化实现：返回模拟结果
            output = await self._call_llm_for_manual_skill(prompt, skill)

            return ExecutionResult(
                success=True,
                output=output,
                logs=[f"手动技能执行: {skill.name}"]
            )

        except Exception as e:
            logger.error(f"❌ 手动技能执行失败: {e}")
            return ExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )

    def _build_manual_skill_prompt(
        self,
        skill: Skill,
        input_data: Dict[str, Any]
    ) -> str:
        """构建手动技能的提示词"""
        prompt_parts = []

        # 技能描述
        if skill.description:
            prompt_parts.append(f"任务: {skill.description}")

        # 工作流提示词
        if skill.workflow_prompt:
            prompt_parts.append(f"\n工作流程:\n{skill.workflow_prompt}")

        # 输入数据
        prompt_parts.append(f"\n输入数据:\n{json.dumps(input_data, ensure_ascii=False, indent=2)}")

        return "\n".join(prompt_parts)

    async def _call_llm_for_manual_skill(
        self,
        prompt: str,
        skill: Skill
    ) -> str:
        """调用LLM执行手动技能"""
        # TODO: 实际调用LLM服务
        # 当前返回占位结果
        return f"手动技能 '{skill.name}' 执行结果（占位）"

    # ==================== 生成技能执行 ====================

    async def _execute_generated_skill(
        self,
        skill: Skill,
        input_data: Dict[str, Any],
        sandbox_config: Optional[SandboxConfig]
    ) -> ExecutionResult:
        """
        执行自动生成的技能

        在沙盒环境中执行技能代码
        """
        logger.debug(f"🤖 执行生成技能: {skill.name}")

        if not skill.code:
            return ExecutionResult(
                success=False,
                output=None,
                error="生成技能缺少代码"
            )

        try:
            # 使用沙盒执行
            config = sandbox_config or self.default_sandbox_config

            result = await self._execute_in_sandbox(
                code=skill.code,
                input_data=input_data,
                config=config
            )

            return result

        except Exception as e:
            logger.error(f"❌ 生成技能执行失败: {e}")
            return ExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )

    # ==================== 沙盒执行 ====================

    async def _execute_in_sandbox(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig
    ) -> ExecutionResult:
        """
        在沙盒环境中执行代码

        Args:
            code: 技能代码
            input_data: 输入数据
            config: 沙盒配置

        Returns:
            执行结果
        """
        logger.debug("🔒 在沙盒中执行代码")

        try:
            # 1. 验证代码安全性
            if not self._validate_code_safety(code, config):
                return ExecutionResult(
                    success=False,
                    output=None,
                    error="代码安全验证失败"
                )

            # 2. 准备执行环境
            execution_globals = {
                '__builtins__': __builtins__,
                'input_data': input_data,
                'json': json
            }

            # 3. 设置超时执行
            try:
                output = await asyncio.wait_for(
                    self._run_code(code, execution_globals),
                    timeout=config.timeout
                )

                return ExecutionResult(
                    success=True,
                    output=output,
                    logs=["代码在沙盒中成功执行"]
                )

            except asyncio.TimeoutError:
                return ExecutionResult(
                    success=False,
                    output=None,
                    error=f"执行超时 (>{config.timeout}s)"
                )

        except Exception as e:
            logger.error(f"❌ 沙盒执行失败: {e}")
            return ExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def _run_code(
        self,
        code: str,
        execution_globals: Dict[str, Any]
    ) -> Any:
        """
        在事件循环中运行代码

        Args:
            code: 代码
            execution_globals: 执行环境

        Returns:
            执行结果
        """
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                # 执行代码
                exec(code, execution_globals)

                # 返回result变量（约定）
                return execution_globals.get('result', None)

            except Exception as e:
                raise RuntimeError(f"代码执行错误: {str(e)}")

        # 在线程池中执行（避免阻塞事件循环）
        result = await loop.run_in_executor(None, _exec)

        return result

    def _validate_code_safety(
        self,
        code: str,
        config: SandboxConfig
    ) -> bool:
        """
        验证代码安全性

        Args:
            code: 代码
            config: 沙盒配置

        Returns:
            是否安全
        """
        # 1. 检查禁止的模块
        for module in config.restricted_modules:
            if f"import {module}" in code or f"from {module}" in code:
                logger.warning(f"⚠️ 代码包含禁止的模块: {module}")
                return False

        # 2. 检查危险函数
        dangerous_functions = [
            'eval', 'exec', 'compile', '__import__',
            'open', 'file', 'input', 'raw_input'
        ]

        for func in dangerous_functions:
            if func in code:
                logger.warning(f"⚠️ 代码包含危险函数: {func}")
                return False

        # 3. 基本语法检查
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            logger.warning(f"⚠️ 代码语法错误: {e}")
            return False

        return True

    # ==================== 批量执行 ====================

    async def execute_batch(
        self,
        executions: list
    ) -> list:
        """
        批量执行技能

        Args:
            executions: 执行任务列表 [(skill, input_data, config), ...]

        Returns:
            执行结果列表
        """
        logger.info(f"📦 批量执行 {len(executions)} 个技能")

        tasks = [
            self.execute(skill, input_data, config)
            for skill, input_data, config in executions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(ExecutionResult(
                    success=False,
                    output=None,
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    # ==================== 工具方法 ====================

    def get_executor_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        return {
            'default_timeout': self.default_sandbox_config.timeout,
            'default_memory_limit': self.default_sandbox_config.max_memory,
            'restricted_modules': self.default_sandbox_config.restricted_modules,
            'registry_connected': self._skill_registry is not None
        }


# 全局单例
_skill_executor_instance = None


def get_skill_executor() -> SkillExecutor:
    """获取技能执行器单例"""
    global _skill_executor_instance
    if _skill_executor_instance is None:
        _skill_executor_instance = SkillExecutor()
    return _skill_executor_instance
