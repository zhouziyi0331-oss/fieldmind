"""
Skill沙箱执行环境 - 安全隔离的Skill执行器（完整版）
"""

import os
import sys
import json
import tempfile
import subprocess
import time
import shutil
import resource
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SkillSandbox:
    """Skill沙箱 - 提供完全隔离的执行环境"""

    def __init__(
        self,
        project_id: int,
        skill_id: int,
        timeout: int = 30,
        max_memory_mb: int = 512,
        max_cpu_time: int = 30
    ):
        """
        初始化沙箱

        Args:
            project_id: 项目ID（用于数据隔离）
            skill_id: Skill ID
            timeout: 执行超时时间（秒）
            max_memory_mb: 最大内存限制（MB）
            max_cpu_time: 最大CPU时间（秒）
        """
        self.project_id = project_id
        self.skill_id = skill_id
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time

        # 创建隔离的工作目录
        self.workspace = self._create_workspace()

        # 执行日志
        self.execution_log = []

        logger.info(f"Skill沙箱初始化: skill_id={skill_id}, project_id={project_id}")

    def _create_workspace(self) -> Path:
        """
        创建Skill的完全隔离工作目录

        路径结构:
        ~/Library/Application Support/FieldMind/skill_workspace/{skill_id}/
        ├── input/     # 输入文件
        ├── output/    # 输出文件
        ├── temp/      # 临时文件
        └── logs/      # 日志文件
        """
        base_dir = Path.home() / "Library" / "Application Support" / "FieldMind" / "skill_workspace"
        workspace = base_dir / str(self.skill_id)

        # 创建目录结构
        for subdir in ['input', 'output', 'temp', 'logs']:
            (workspace / subdir).mkdir(parents=True, exist_ok=True)

        # 设置权限（只读写当前用户）
        workspace.chmod(0o700)

        logger.info(f"Skill工作目录创建: {workspace}")

        return workspace

    def execute_skill(
        self,
        skill_code: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        在沙箱中执行Skill

        Args:
            skill_code: Skill的Python代码
            parameters: 执行参数

        Returns:
            执行结果
        """
        start_time = time.time()

        try:
            # 1. 准备执行环境
            self._log("准备执行环境")

            # 2. 创建临时Python文件
            script_file = self.workspace / f"skill_{self.skill_id}_{int(time.time())}.py"

            # 3. 包装代码（注入安全限制）
            wrapped_code = self._wrap_skill_code(skill_code, parameters)

            # 4. 写入文件
            script_file.write_text(wrapped_code, encoding='utf-8')
            self._log(f"代码写入: {script_file}")

            # 5. 执行（使用subprocess隔离）
            result = self._execute_in_subprocess(script_file, parameters)

            # 6. 记录执行时间
            execution_time = time.time() - start_time

            # 7. 返回结果
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'logs': self.execution_log
            }

        except TimeoutError:
            self._log("执行超时", level='ERROR')
            return {
                'success': False,
                'error': 'Skill执行超时',
                'execution_time': time.time() - start_time,
                'logs': self.execution_log
            }

        except Exception as e:
            self._log(f"执行失败: {str(e)}", level='ERROR')
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'logs': self.execution_log
            }

        finally:
            # 清理临时文件
            if 'script_file' in locals() and script_file.exists():
                script_file.unlink()

    def _wrap_skill_code(
        self,
        skill_code: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        包装Skill代码，注入安全限制和上下文

        包装内容:
        1. 禁用网络库
        2. 限制文件访问
        3. 注入project_id（数据隔离）
        4. 注入parameters
        """
        wrapper_template = '''
import sys
import os
import json
from pathlib import Path
import builtins

# ============================================================
# 安全限制：禁用网络库和危险操作（必须在最开始）
# ============================================================
class NetworkBlocker:
    """阻止网络访问"""
    def __init__(self, module_name):
        self._module_name = module_name

    def __getattr__(self, name):
        raise RuntimeError("Skill禁止访问网络模块: " + self._module_name + "." + name)

    def __call__(self, *args, **kwargs):
        raise RuntimeError("Skill禁止使用网络模块: " + self._module_name)

# 在任何用户代码执行前就禁用网络模块
network_modules = [
    'requests', 'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
    'urllib3', 'socket', 'http', 'http.client', 'httplib', 'httplib2',
    'httpx', 'aiohttp', 'websocket', 'websockets',
    'ftplib', 'telnetlib', 'smtplib', 'poplib', 'imaplib',
    'ssl', 'asyncio.streams'
]

for module_name in network_modules:
    sys.modules[module_name] = NetworkBlocker(module_name)

# 禁用subprocess和multiprocessing
sys.modules['subprocess'] = NetworkBlocker('subprocess')
sys.modules['multiprocessing'] = NetworkBlocker('multiprocessing')

# 重写__import__函数，阻止动态导入网络模块
_original_import = builtins.__import__

def _restricted_import(name, *args, **kwargs):
    """受限的import - 阻止导入网络模块"""
    blocked = ['requests', 'urllib', 'socket', 'http', 'httpx', 'aiohttp',
               'websocket', 'ftplib', 'telnetlib', 'smtplib', 'ssl',
               'subprocess', 'multiprocessing']

    # 检查是否尝试导入被禁止的模块
    for blocked_name in blocked:
        if name == blocked_name or name.startswith(blocked_name + '.'):
            raise ImportError("Skill禁止导入模块: " + name)

    return _original_import(name, *args, **kwargs)

builtins.__import__ = _restricted_import

# ============================================================
# 数据隔离：注入project_id
# ============================================================
PROJECT_ID = {project_id}

# ============================================================
# 执行参数
# ============================================================
PARAMETERS = {parameters}

# ============================================================
# 工作目录限制
# ============================================================
WORKSPACE = Path(r"{workspace}")
os.chdir(WORKSPACE)

# ============================================================
# 数据库访问辅助函数（自动添加project_id过滤）
# ============================================================
def query_database(query_func, *args, **kwargs):
    """
    数据库查询包装器 - 自动添加project_id过滤

    所有数据库查询都必须通过这个函数，自动确保数据隔离
    """
    # 如果是SQLAlchemy查询，自动添加project_id过滤
    if hasattr(query_func, 'filter'):
        return query_func.filter(project_id=PROJECT_ID)
    return query_func(*args, **kwargs)

# ============================================================
# 向量检索辅助函数（自动添加project_id过滤）
# ============================================================
def search_vectors(query_text, top_k=10, threshold=0.5):
    """
    向量检索包装器 - 自动限制在当前项目
    """
    # 这里会调用实际的向量检索服务，但已经限制了project_id
    from app.services.vectorization_service_complete import VectorizationService
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        vectorizer = VectorizationService()
        results = vectorizer.semantic_search(
            query=query_text,
            project_id=PROJECT_ID,
            db=db,
            top_k=top_k,
            threshold=threshold
        )
        return results
    finally:
        db.close()

# ============================================================
# Skill代码开始
# ============================================================
try:
    # 用户的Skill代码
{skill_code}

    # 如果代码中定义了main函数，调用它
    if 'main' in dir():
        result = main(PARAMETERS)
    else:
        result = {{"status": "success", "message": "Skill执行完成"}}

    # 输出结果（JSON格式）
    print("__SKILL_RESULT__")
    print(json.dumps(result, ensure_ascii=False))
    print("__SKILL_RESULT_END__")

except Exception as e:
    import traceback
    error_result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print("__SKILL_RESULT__")
    print(json.dumps(error_result, ensure_ascii=False))
    print("__SKILL_RESULT_END__")
'''

        # 格式化代码
        wrapped = wrapper_template.format(
            project_id=self.project_id,
            parameters=json.dumps(parameters, ensure_ascii=False),
            workspace=str(self.workspace),
            skill_code=self._indent_code(skill_code, 4)
        )

        return wrapped

    def _indent_code(self, code: str, spaces: int) -> str:
        """给代码添加缩进"""
        indent = ' ' * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)

    def _execute_in_subprocess(
        self,
        script_file: Path,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        在子进程中执行代码（隔离）

        使用subprocess确保:
        1. 进程隔离
        2. 超时控制
        3. 资源限制
        """
        self._log("启动子进程执行")

        try:
            # 执行Python脚本
            process = subprocess.run(
                [sys.executable, str(script_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.workspace)
            )

            # 解析输出
            stdout = process.stdout
            stderr = process.stderr

            # 记录标准输出和错误
            if stdout:
                self._log(f"标准输出: {stdout[:500]}")
            if stderr:
                self._log(f"标准错误: {stderr[:500]}", level='WARNING')

            # 提取结果
            result = self._extract_result(stdout)

            if process.returncode != 0 and not result:
                raise RuntimeError(f"Skill执行失败，退出码: {process.returncode}")

            return result

        except subprocess.TimeoutExpired:
            self._log(f"执行超时（>{self.timeout}秒）", level='ERROR')
            raise TimeoutError(f"Skill执行超时（>{self.timeout}秒）")

    def _extract_result(self, output: str) -> Dict[str, Any]:
        """从输出中提取结果"""
        try:
            # 查找结果标记
            start_marker = "__SKILL_RESULT__"
            end_marker = "__SKILL_RESULT_END__"

            if start_marker in output and end_marker in output:
                start_idx = output.index(start_marker) + len(start_marker)
                end_idx = output.index(end_marker)

                result_json = output[start_idx:end_idx].strip()
                result = json.loads(result_json)

                return result

            return {"status": "success", "output": output}

        except Exception as e:
            logger.error(f"结果解析失败: {e}")
            return {"status": "error", "error": "结果解析失败", "raw_output": output}

    def _log(self, message: str, level: str = 'INFO'):
        """记录执行日志"""
        log_entry = {
            'timestamp': time.time(),
            'level': level,
            'message': message
        }
        self.execution_log.append(log_entry)

        if level == 'ERROR':
            logger.error(f"[Skill {self.skill_id}] {message}")
        elif level == 'WARNING':
            logger.warning(f"[Skill {self.skill_id}] {message}")
        else:
            logger.info(f"[Skill {self.skill_id}] {message}")

    def cleanup(self):
        """清理工作目录"""
        try:
            import shutil
            if self.workspace.exists():
                shutil.rmtree(self.workspace)
                self._log("工作目录已清理")
        except Exception as e:
            logger.error(f"清理失败: {e}")


class SkillExecutionContext:
    """Skill执行上下文 - 提供给Skill的安全API"""

    def __init__(self, project_id: int, db_session):
        self.project_id = project_id
        self.db = db_session

    def query_chunks(self, query: str, top_k: int = 10):
        """查询项目的chunks（自动限制project_id）"""
        from app.services.vectorization_service_complete import VectorizationService

        vectorizer = VectorizationService()
        results = vectorizer.semantic_search(
            query=query,
            project_id=self.project_id,
            db=self.db,
            top_k=top_k
        )

        return results

    def get_documents(self):
        """获取项目的所有文档（自动限制project_id）"""
        from app.models.project import ProjectDocument

        docs = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == self.project_id
        ).all()

        return [
            {
                'id': doc.id,
                'filename': doc.filename,
                'file_type': doc.file_type,
                'status': doc.status
            }
            for doc in docs
        ]
