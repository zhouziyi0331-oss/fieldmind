"""
技能对话适配器 (Skill Chat Adapter)

连接对话系统和技能系统，提供：
1. 技能模型驱动的对话
2. 动态工作流提示词注入
3. 技能参数绑定
4. 技能执行追踪
5. 技能推荐和自动选择

支持手动技能和自动生成技能
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SkillChatAdapter:
    """技能对话适配器"""

    def __init__(self, db: Session):
        """
        初始化适配器

        Args:
            db: 数据库会话
        """
        self.db = db
        self._skills_service = None
        self._execution_tracker = None

        logger.info("✅ 技能对话适配器初始化")

    # ==================== 延迟加载服务 ====================

    @property
    def skills_service(self):
        """统一技能服务（延迟加载）"""
        if self._skills_service is None:
            try:
                from app.services.unified_skills_service import UnifiedSkillsService
                self._skills_service = UnifiedSkillsService(self.db)
                logger.debug("✅ 统一技能服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ 统一技能服务加载失败: {e}")
        return self._skills_service

    @property
    def execution_tracker(self):
        """执行追踪器（延迟加载）"""
        if self._execution_tracker is None:
            try:
                from app.services.execution_tracker import ExecutionTracker
                self._execution_tracker = ExecutionTracker(self.db)
                logger.debug("✅ 执行追踪器已加载")
            except Exception as e:
                logger.warning(f"⚠️ 执行追踪器加载失败: {e}")
        return self._execution_tracker

    # ==================== 核心适配方法 ====================

    def prepare_skill_context(
        self,
        skill_config: Dict[str, Any],
        user_query: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        准备技能上下文

        Args:
            skill_config: 技能配置 {skill_id, skill_name, workflow_prompt, parameters}
            user_query: 用户查询
            project_id: 项目ID

        Returns:
            包含系统提示词、参数绑定等的完整上下文
        """
        try:
            skill_id = skill_config.get('skill_id')
            skill_name = skill_config.get('skill_name')

            logger.info(f"📋 准备技能上下文: skill={skill_name or skill_id}")

            # 获取技能详情
            skill = None
            if skill_id:
                skill = self._get_skill_by_id(skill_id)
            elif skill_name:
                skill = self._get_skill_by_name(skill_name, project_id)

            if not skill:
                logger.warning(f"⚠️ 技能未找到: {skill_name or skill_id}")
                return self._fallback_context(skill_config)

            # 构建系统提示词
            system_prompt = self._build_skill_system_prompt(
                skill=skill,
                custom_workflow=skill_config.get('workflow_prompt')
            )

            # 绑定参数
            parameters = self._bind_parameters(
                skill=skill,
                user_query=user_query,
                custom_params=skill_config.get('parameters')
            )

            # 提取技能元数据
            metadata = {
                'skill_id': skill.get('id'),
                'skill_name': skill.get('name'),
                'skill_type': skill.get('type'),
                'category': skill.get('category'),
                'source': skill.get('source'),  # 'manual' or 'generated'
                'version': skill.get('version'),
                'tags': skill.get('tags', [])
            }

            context = {
                'system_prompt': system_prompt,
                'parameters': parameters,
                'metadata': metadata,
                'skill': skill,
                'prepared_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ 技能上下文准备完成: {skill.get('name')}")

            return context

        except Exception as e:
            logger.error(f"❌ 准备技能上下文失败: {e}")
            return self._fallback_context(skill_config)

    def apply_skill_to_response(
        self,
        response: str,
        skill_context: Dict[str, Any],
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        将技能应用到响应

        处理：
        - 响应后处理
        - 格式转换
        - 结果验证
        - 执行记录

        Args:
            response: AI生成的原始响应
            skill_context: 技能上下文
            execution_metadata: 执行元数据

        Returns:
            处理后的完整结果
        """
        try:
            skill = skill_context.get('skill')
            skill_name = skill.get('name') if skill else '未知技能'

            logger.info(f"🎯 应用技能到响应: {skill_name}")

            # 后处理响应
            processed_response = self._post_process_response(
                response=response,
                skill=skill,
                parameters=skill_context.get('parameters', {})
            )

            # 验证结果
            validation = self._validate_skill_output(
                response=processed_response,
                skill=skill
            )

            # 记录执行
            execution_record = self._record_skill_execution(
                skill=skill,
                input_query=execution_metadata.get('query') if execution_metadata else None,
                output_response=processed_response,
                metadata=execution_metadata
            )

            result = {
                'response': processed_response,
                'validation': validation,
                'execution_record': execution_record,
                'skill_metadata': skill_context.get('metadata'),
                'applied_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ 技能应用完成: valid={validation.get('valid')}")

            return result

        except Exception as e:
            logger.error(f"❌ 应用技能失败: {e}")
            return {
                'response': response,
                'error': str(e),
                'validation': {'valid': False, 'error': str(e)}
            }

    # ==================== 技能推荐 ====================

    def recommend_skill(
        self,
        user_query: str,
        project_id: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        推荐合适的技能

        基于：
        - 查询内容分析
        - 对话历史
        - 项目上下文
        - 技能使用统计

        Args:
            user_query: 用户查询
            project_id: 项目ID
            conversation_history: 对话历史
            top_k: 返回前K个推荐

        Returns:
            推荐的技能列表
        """
        try:
            logger.info(f"🔍 推荐技能: query='{user_query[:50]}...'")

            if not self.skills_service:
                return []

            # 获取所有可用技能
            available_skills = self.skills_service.list_all(
                include_generated=True
            )

            if not available_skills:
                return []

            # 计算每个技能的相关度得分
            skill_scores = []

            for skill in available_skills:
                score = self._calculate_skill_relevance(
                    skill=skill,
                    query=user_query,
                    project_id=project_id,
                    history=conversation_history
                )

                skill_scores.append({
                    'skill': skill,
                    'score': score,
                    'reason': self._generate_recommendation_reason(skill, score)
                })

            # 按得分排序
            skill_scores.sort(key=lambda x: x['score'], reverse=True)

            # 返回top K
            recommendations = skill_scores[:top_k]

            logger.info(
                f"✅ 推荐完成: {len(recommendations)} 个技能, "
                f"top={recommendations[0]['skill']['name'] if recommendations else 'None'}"
            )

            return recommendations

        except Exception as e:
            logger.error(f"❌ 技能推荐失败: {e}")
            return []

    def auto_select_skill(
        self,
        user_query: str,
        project_id: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        confidence_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        自动选择最合适的技能

        Args:
            user_query: 用户查询
            project_id: 项目ID
            conversation_history: 对话历史
            confidence_threshold: 置信度阈值

        Returns:
            选中的技能，如果置信度不够则返回None
        """
        try:
            recommendations = self.recommend_skill(
                user_query=user_query,
                project_id=project_id,
                conversation_history=conversation_history,
                top_k=1
            )

            if not recommendations:
                return None

            top_recommendation = recommendations[0]

            # 检查置信度
            if top_recommendation['score'] >= confidence_threshold:
                logger.info(
                    f"🎯 自动选择技能: {top_recommendation['skill']['name']} "
                    f"(confidence={top_recommendation['score']:.2f})"
                )
                return top_recommendation
            else:
                logger.info(
                    f"⚠️ 置信度不足: {top_recommendation['score']:.2f} < {confidence_threshold}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ 自动选择技能失败: {e}")
            return None

    # ==================== 私有辅助方法 ====================

    def _get_skill_by_id(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """通过ID获取技能"""
        try:
            if not self.skills_service:
                return None
            return self.skills_service.get(skill_id)
        except Exception as e:
            logger.warning(f"⚠️ 获取技能失败 (id={skill_id}): {e}")
            return None

    def _get_skill_by_name(
        self,
        skill_name: str,
        project_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """通过名称获取技能"""
        try:
            if not self.skills_service:
                return None

            # 搜索技能
            skills = self.skills_service.search(
                query=skill_name,
                exact_match=True
            )

            if skills:
                return skills[0]

            return None

        except Exception as e:
            logger.warning(f"⚠️ 获取技能失败 (name={skill_name}): {e}")
            return None

    def _build_skill_system_prompt(
        self,
        skill: Dict[str, Any],
        custom_workflow: Optional[str] = None
    ) -> str:
        """构建技能的系统提示词"""
        base_prompt = f"""你正在使用技能: {skill.get('name')}

技能描述: {skill.get('description', '无描述')}

技能类型: {skill.get('type', '通用')}
"""

        # 添加工作流提示词
        if custom_workflow:
            workflow_section = f"""
## 工作流程

{custom_workflow}
"""
            base_prompt += workflow_section
        elif skill.get('workflow_prompt'):
            workflow_section = f"""
## 工作流程

{skill.get('workflow_prompt')}
"""
            base_prompt += workflow_section

        # 添加示例（如果有）
        if skill.get('examples'):
            examples_section = "\n## 示例\n\n"
            for idx, example in enumerate(skill['examples'][:3], 1):
                examples_section += f"### 示例 {idx}\n"
                examples_section += f"输入: {example.get('input', '')}\n"
                examples_section += f"输出: {example.get('output', '')}\n\n"
            base_prompt += examples_section

        # 添加约束（如果有）
        if skill.get('constraints'):
            constraints_section = "\n## 约束条件\n\n"
            for constraint in skill['constraints']:
                constraints_section += f"- {constraint}\n"
            base_prompt += constraints_section

        return base_prompt

    def _bind_parameters(
        self,
        skill: Dict[str, Any],
        user_query: str,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """绑定技能参数"""
        parameters = {}

        # 技能定义的参数
        skill_params = skill.get('parameters', {})

        # 绑定自定义参数
        if custom_params:
            parameters.update(custom_params)

        # 自动提取参数（从查询中）
        # TODO: 实现更智能的参数提取
        parameters['query'] = user_query
        parameters['query_length'] = len(user_query)

        # 填充默认值
        for param_name, param_config in skill_params.items():
            if param_name not in parameters:
                if 'default' in param_config:
                    parameters[param_name] = param_config['default']

        return parameters

    def _post_process_response(
        self,
        response: str,
        skill: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> str:
        """后处理响应"""
        # 获取技能的后处理配置
        post_processing = skill.get('post_processing', {})

        processed = response

        # 格式转换
        if post_processing.get('format') == 'json':
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', processed, re.DOTALL)
            if json_match:
                processed = json_match.group()

        # 截断
        if 'max_length' in post_processing:
            max_length = post_processing['max_length']
            if len(processed) > max_length:
                processed = processed[:max_length] + '...'

        # 添加前缀/后缀
        if 'prefix' in post_processing:
            processed = post_processing['prefix'] + processed

        if 'suffix' in post_processing:
            processed = processed + post_processing['suffix']

        return processed

    def _validate_skill_output(
        self,
        response: str,
        skill: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证技能输出"""
        validation = {
            'valid': True,
            'checks': [],
            'warnings': []
        }

        # 获取验证规则
        validation_rules = skill.get('validation', {})

        # 长度检查
        if 'min_length' in validation_rules:
            if len(response) < validation_rules['min_length']:
                validation['valid'] = False
                validation['checks'].append({
                    'rule': 'min_length',
                    'passed': False,
                    'message': f"响应长度不足 ({len(response)} < {validation_rules['min_length']})"
                })

        if 'max_length' in validation_rules:
            if len(response) > validation_rules['max_length']:
                validation['warnings'].append({
                    'rule': 'max_length',
                    'message': f"响应过长 ({len(response)} > {validation_rules['max_length']})"
                })

        # 必需关键词检查
        if 'required_keywords' in validation_rules:
            for keyword in validation_rules['required_keywords']:
                if keyword not in response:
                    validation['valid'] = False
                    validation['checks'].append({
                        'rule': 'required_keyword',
                        'passed': False,
                        'message': f"缺少必需关键词: {keyword}"
                    })

        # 格式检查
        if validation_rules.get('format') == 'json':
            try:
                import json
                json.loads(response)
                validation['checks'].append({
                    'rule': 'json_format',
                    'passed': True,
                    'message': 'JSON格式有效'
                })
            except:
                validation['valid'] = False
                validation['checks'].append({
                    'rule': 'json_format',
                    'passed': False,
                    'message': 'JSON格式无效'
                })

        return validation

    def _record_skill_execution(
        self,
        skill: Dict[str, Any],
        input_query: Optional[str],
        output_response: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """记录技能执行"""
        try:
            if not self.execution_tracker:
                return None

            record = self.execution_tracker.record_execution(
                execution_type="skill",
                skill_id=skill.get('id'),
                skill_name=skill.get('name'),
                input_data={'query': input_query},
                output_data={'response': output_response},
                metadata=metadata or {},
                user_id=metadata.get('user_id') if metadata else None
            )

            logger.debug(f"📝 技能执行已记录: {skill.get('name')}")

            return record

        except Exception as e:
            logger.warning(f"⚠️ 记录技能执行失败: {e}")
            return None

    def _calculate_skill_relevance(
        self,
        skill: Dict[str, Any],
        query: str,
        project_id: Optional[int],
        history: Optional[List[Dict]]
    ) -> float:
        """
        计算技能相关度得分

        综合考虑：
        - 关键词匹配
        - 技能类型
        - 历史使用频率
        - 项目偏好
        """
        score = 0.0

        query_lower = query.lower()

        # 1. 名称匹配 (权重: 0.3)
        skill_name = skill.get('name', '').lower()
        if skill_name in query_lower:
            score += 0.3
        elif any(word in query_lower for word in skill_name.split()):
            score += 0.15

        # 2. 描述匹配 (权重: 0.2)
        skill_desc = skill.get('description', '').lower()
        common_words = set(query_lower.split()) & set(skill_desc.split())
        if len(common_words) >= 3:
            score += 0.2
        elif len(common_words) >= 1:
            score += 0.1

        # 3. 标签匹配 (权重: 0.2)
        skill_tags = skill.get('tags', [])
        for tag in skill_tags:
            if tag.lower() in query_lower:
                score += 0.1

        # 4. 类型匹配 (权重: 0.15)
        # 根据查询模式判断类型
        skill_type = skill.get('type', '')
        if '分析' in query_lower and skill_type == 'analysis':
            score += 0.15
        elif '总结' in query_lower and skill_type == 'summary':
            score += 0.15
        elif '翻译' in query_lower and skill_type == 'translation':
            score += 0.15

        # 5. 使用频率 (权重: 0.15)
        # TODO: 从执行追踪获取使用统计
        usage_count = skill.get('usage_count', 0)
        if usage_count > 10:
            score += 0.15
        elif usage_count > 5:
            score += 0.1
        elif usage_count > 0:
            score += 0.05

        # 归一化到 [0, 1]
        return min(score, 1.0)

    def _generate_recommendation_reason(
        self,
        skill: Dict[str, Any],
        score: float
    ) -> str:
        """生成推荐理由"""
        if score >= 0.8:
            return f"高度匹配: {skill.get('name')} - {skill.get('description', '')[:50]}"
        elif score >= 0.6:
            return f"较为匹配: {skill.get('name')} - 可能适用于此场景"
        elif score >= 0.4:
            return f"部分匹配: {skill.get('name')} - 可作为备选"
        else:
            return f"低相关度: {skill.get('name')}"

    def _fallback_context(self, skill_config: Dict[str, Any]) -> Dict[str, Any]:
        """降级上下文"""
        return {
            'system_prompt': f"你正在使用技能: {skill_config.get('skill_name', '通用技能')}",
            'parameters': skill_config.get('parameters', {}),
            'metadata': {
                'skill_name': skill_config.get('skill_name'),
                'fallback': True
            },
            'skill': None,
            'prepared_at': datetime.utcnow().isoformat()
        }

    # ==================== 统计和管理 ====================

    def get_skill_usage_statistics(
        self,
        skill_id: Optional[int] = None,
        project_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取技能使用统计"""
        try:
            if not self.execution_tracker:
                return {'error': 'Execution tracker not available'}

            stats = self.execution_tracker.get_skill_statistics(
                skill_id=skill_id,
                project_id=project_id,
                days=days
            )

            return stats

        except Exception as e:
            logger.error(f"❌ 获取技能统计失败: {e}")
            return {'error': str(e)}

    def get_adapter_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            'skills_service_loaded': self._skills_service is not None,
            'execution_tracker_loaded': self._execution_tracker is not None,
            'timestamp': datetime.utcnow().isoformat()
        }


# 工厂函数
def create_skill_chat_adapter(db: Session) -> SkillChatAdapter:
    """创建技能对话适配器实例"""
    return SkillChatAdapter(db)
