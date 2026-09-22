"""
InternVL 多模态理解服务

核心功能：
1. 图片内容理解（描述场景、回答问题）
2. 文档理解（图表、流程图、复杂文档）
3. OCR 增强（理解文字的语义）
4. 多轮对话（针对图片的交互式问答）

技术栈：
- InternVL：开源多模态大模型
- Vision Transformer + LLM
- 支持高分辨率图片（4K）
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import torch

logger = logging.getLogger(__name__)


class InternVLService:
    """InternVL 多模态理解服务"""
    def __init__(self, model_name: str = "OpenGVLab/InternVL2-8B", use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化 InternVL 服务

        Args:
            model_name: 模型名称
                - OpenGVLab/InternVL2-8B (推荐，8B参数，平衡性能)
                - OpenGVLab/InternVL2-26B (26B参数，最强性能)
                - OpenGVLab/InternVL2-4B (4B参数，最快速度)
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = None
        self._check_gpu()

    def _check_gpu(self):
        """检查 GPU 可用性"""
        if torch.cuda.is_available():
            self.device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"✅ GPU 可用: {gpu_name} ({gpu_memory:.1f} GB)")
        else:
            self.device = "cpu"
            logger.warning("⚠️ GPU 不可用，将使用 CPU（速度较慢）")

    def load_model(self):
        """加载 InternVL 模型"""
        if self.model is not None:
            logger.info("模型已加载")
            return

        try:
            logger.info(f"🔧 加载 InternVL 模型: {self.model_name}")
            logger.info(f"   设备: {self.device}")

            from transformers import AutoModel, AutoTokenizer

            # 加载模型和 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            ).eval()

            if self.device == "cuda":
                self.model = self.model.cuda()

            logger.info("✅ InternVL 模型加载成功")

        except ImportError:
            logger.error("❌ transformers 未安装，请运行: pip install transformers")
            self.model = None
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self.model = None

    def understand_image(
        self,
        image_path: str,
        prompt: str = "请详细描述这张图片的内容。",
        max_length: int = 512
    ) -> Dict[str, Any]:
        """
        理解图片内容

        Args:
            image_path: 图片路径
            prompt: 提示词（问题）
            max_length: 最大生成长度

        Returns:
            {
                "description": "图片描述",
                "method": "internvl",
                "model": "InternVL2-8B",
                "confidence": 0.95
            }
        """
        if self.model is None:
            logger.warning("模型未加载")
            return {
                "description": "",
                "method": "internvl",
                "error": "Model not loaded"
            }

        try:
            from PIL import Image

            logger.info(f"🖼️ 理解图片: {Path(image_path).name}")
            logger.info(f"   问题: {prompt}")

            # 加载图片
            image = Image.open(image_path).convert('RGB')

            # 生成描述
            with torch.no_grad():
                response = self.model.chat(
                    self.tokenizer,
                    pixel_values=None,
                    image=image,
                    question=prompt,
                    generation_config={
                        'max_new_tokens': max_length,
                        'do_sample': True,
                        'temperature': 0.7
                    }
                )

            logger.info(f"✅ 生成完成: {len(response)} 字符")

            return {
                "description": response,
                "method": "internvl",
                "model": self.model_name,
                "prompt": prompt,
                "confidence": 0.95
            }

        except Exception as e:
            logger.error(f"❌ 图片理解失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())

            return {
                "description": "",
                "method": "internvl",
                "error": str(e)
            }

    def extract_structured_info(
        self,
        image_path: str,
        info_type: str = "general"
    ) -> Dict[str, Any]:
        """
        提取结构化信息

        Args:
            image_path: 图片路径
            info_type: 信息类型
                - "general": 通用描述
                - "chart": 图表分析
                - "document": 文档理解
                - "scene": 场景描述

        Returns:
            结构化信息
        """
        prompts = {
            "general": "请详细描述这张图片，包括：1. 主要对象 2. 场景 3. 颜色 4. 构图",
            "chart": "这是一张图表。请分析：1. 图表类型 2. 数据趋势 3. 关键发现 4. 结论",
            "document": "这是一份文档。请提取：1. 标题 2. 主要内容 3. 关键信息 4. 结构",
            "scene": "请描述这个场景：1. 地点 2. 时间（如果能判断）3. 人物 4. 活动"
        }

        prompt = prompts.get(info_type, prompts["general"])

        result = self.understand_image(image_path, prompt)

        # 解析结构化信息
        description = result.get("description", "")

        structured = {
            "type": info_type,
            "raw_description": description,
            "method": "internvl"
        }

        # 简单的结构化解析（可以进一步增强）
        if info_type == "chart":
            structured["insights"] = self._extract_chart_insights(description)
        elif info_type == "document":
            structured["document_info"] = self._extract_document_info(description)

        return structured

    def _extract_chart_insights(self, description: str) -> Dict[str, Any]:
        """从描述中提取图表洞察"""
        # 简单实现，可以用更复杂的 NLP 方法
        return {
            "has_trend": any(word in description for word in ["上升", "下降", "增长", "趋势"]),
            "has_comparison": any(word in description for word in ["对比", "比较", "差异"]),
            "description": description
        }

    def _extract_document_info(self, description: str) -> Dict[str, Any]:
        """从描述中提取文档信息"""
        lines = description.split('\n')
        return {
            "line_count": len(lines),
            "first_line": lines[0] if lines else "",
            "description": description
        }

    def batch_understand(
        self,
        image_paths: List[str],
        prompt: str = "请描述这张图片。"
    ) -> List[Dict[str, Any]]:
        """
        批量理解图片

        Args:
            image_paths: 图片路径列表
            prompt: 提示词

        Returns:
            结果列表
        """
        results = []

        for image_path in image_paths:
            result = self.understand_image(image_path, prompt)
            result["image_path"] = image_path
            results.append(result)

        return results


# 全局单例
_internvl_service = None


def get_internvl_service(
    model_name: str = "OpenGVLab/InternVL2-8B",
    auto_load: bool = False
) -> InternVLService:
    """
    获取 InternVL 服务单例

    Args:
        model_name: 模型名称
        auto_load: 是否自动加载模型

    Returns:
        InternVL 服务实例
    """
    global _internvl_service

    if _internvl_service is None:
        _internvl_service = InternVLService(model_name)

        if auto_load:
            _internvl_service.load_model()

    return _internvl_service


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 InternVL 服务测试")
    print("=" * 80)

    service = get_internvl_service()

    print(f"\n模型: {service.model_name}")
    print(f"设备: {service.device}")

    print("\n使用示例:")
    print("""
# 1. 加载模型
service.load_model()

# 2. 理解图片
result = service.understand_image("image.jpg", "这张图片里有什么？")
print(result["description"])

# 3. 分析图表
result = service.extract_structured_info("chart.png", info_type="chart")
print(result["insights"])

# 4. 批量处理
results = service.batch_understand(["img1.jpg", "img2.jpg"])
    """)
