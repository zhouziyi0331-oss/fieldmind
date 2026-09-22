"""
社区治理Skill - 分析村庄治理结构、权力关系与决策机制
"""
import logging

logger = logging.getLogger(__name__)

SKILL_DEFINITION = {
    "id": "community_governance",
    "name": "社区治理分析",
    "description": "村庄治理结构、权力关系与决策机制分析",
    "dimensions": {
        "power_structure": {
            "name": "权力结构",
            "keywords": ["村委会", "村支书", "村长", "党支部", "村民代表", "理事会", "族长", "宗族", "长辈"]
        },
        "decision_making": {
            "name": "决策机制",
            "keywords": ["村民大会", "投票", "商议", "协商", "民主", "表决", "意见", "讨论"]
        },
        "conflict_resolution": {
            "name": "矛盾调解",
            "keywords": ["纠纷", "调解", "矛盾", "冲突", "争议", "仲裁", "协调", "化解"]
        },
        "resource_allocation": {
            "name": "资源分配",
            "keywords": ["土地", "分配", "承包", "补贴", "项目", "资金", "公共", "集体"]
        }
    }
}

def analyze(content: str, metadata: dict = None) -> dict:
    """执行社区治理分析"""
    try:
        result = {"skill_name": SKILL_DEFINITION["name"], "dimensions": {}}
        
        for dim_id, dim_info in SKILL_DEFINITION["dimensions"].items():
            matched_count = 0
            contexts = []
            
            for keyword in dim_info["keywords"]:
                if keyword in content:
                    matched_count += 1
                    sentences = content.split('。')
                    for sent in sentences:
                        if keyword in sent and len(sent) > 5:
                            contexts.append(sent.strip() + '。')
                            if len(contexts) >= 3:
                                break
                    if len(contexts) >= 3:
                        break
            
            result["dimensions"][dim_id] = {
                "name": dim_info["name"],
                "matched_count": matched_count,
                "contexts": contexts[:3]
            }
        
        return result
    except Exception as e:
        logger.error(f"社区治理分析失败: {e}")
        return None



# ==================== WorkflowEngine 包装类 ====================

class CommunityGovernanceWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_analyze(self, content: str, _context: dict) -> dict:
        """任务: 执行社区治理分析"""
        metadata = _context.get('metadata')
        result = analyze(content, metadata)
        return {"analysis_result": result}

    def _task_batch_analyze(self, contents: list, _context: dict) -> dict:
        """任务: 批量社区治理分析"""
        metadata = _context.get('metadata')
        results = [analyze(content, metadata) for content in contents]
        return {"results": results, "count": len(results)}

    def analyze_workflow(self, content: str, metadata: dict = None) -> dict:
        """工作流: 使用 WorkflowEngine 执行社区治理分析"""
        if not self.use_workflow_engine:
            return analyze(content, metadata)

        tasks = {
            "analyze": {
                "function": self._task_analyze,
                "args": {"content": content},
                "context": {"metadata": metadata}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["analyze"]["analysis_result"]

    def batch_analyze_workflow(self, contents: list, metadata: dict = None) -> list:
        """工作流: 使用 WorkflowEngine 批量执行社区治理分析"""
        if not self.use_workflow_engine:
            return [analyze(content, metadata) for content in contents]

        tasks = {
            "batch_analyze": {
                "function": self._task_batch_analyze,
                "args": {"contents": contents},
                "context": {"metadata": metadata}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_analyze"]["results"]
