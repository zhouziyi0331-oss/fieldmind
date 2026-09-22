"""
视觉模型服务 - 图像描述生成

支持的模型：
1. BLIP-2 (推荐，离线可用)
2. 降级方案（基础图像分析）
"""

import logging
from typing import Dict, Any, Optional
import tempfile
import os

logger = logging.getLogger(__name__)


class VisionService:
    """视觉模型服务"""

    def __init__(self, model_type: str = "blip2"):
        self.model_type = model_type
        self.model = None
        self.processor = None
        self._init_model()

    def _init_model(self):
        """初始化模型"""
        if self.model_type == "blip2":
            self._init_blip2()
        else:
            self._init_fallback()

    def _init_blip2(self):
        """初始化 BLIP-2 模型"""
        try:
            from transformers import Blip2Processor, Blip2ForConditionalGeneration
            import torch

            logger.info("🔧 加载 BLIP-2 模型...")

            # 使用较小的模型以节省内存
            model_name = "Salesforce/blip2-opt-2.7b"

            self.processor = Blip2Processor.from_pretrained(model_name)
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

            logger.info("✅ BLIP-2 模型加载成功")

        except Exception as e:
            logger.warning(f"⚠️ BLIP-2 加载失败: {e}")
            logger.info("切换到降级方案")
            self._init_fallback()

    def _init_fallback(self):
        """降级方案：返回基础描述"""
        logger.info("⚠️ 使用降级方案：基础图像分析")
        self.model = None
        self.processor = None

    def describe_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        生成图像描述

        Args:
            image_path: 图片路径
            prompt: 可选的提示词

        Returns:
            图像描述文本
        """
        if self.model is None:
            return self._fallback_description(image_path)

        if self.model_type == "blip2":
            return self._describe_with_blip2(image_path, prompt)
        else:
            return self._fallback_description(image_path)

    def _describe_with_blip2(self, image_path: str, prompt: Optional[str] = None) -> str:
        """使用 BLIP-2 生成描述"""
        try:
            from PIL import Image
            import torch

            image = Image.open(image_path).convert('RGB')

            # 生成描述（不使用额外的 prompt）
            inputs = self.processor(image, return_tensors="pt")

            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # 生成描述
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=100,
                num_beams=5,
                temperature=0.7
            )

            description = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0].strip()

            # 如果描述太短，补充基础信息
            if len(description) < 30:
                basic_info = self._get_basic_info(image_path)
                description = f"{description}。{basic_info}"

            return description

        except Exception as e:
            logger.error(f"BLIP-2 描述生成失败: {e}")
            return self._fallback_description(image_path)

    def _fallback_description(self, image_path: str) -> str:
        """降级方案：基础图像分析"""
        try:
            from PIL import Image
            import numpy as np

            image = Image.open(image_path)
            width, height = image.size
            mode = image.mode

            # 基础描述
            description = f"这是一张 {width}x{height} 像素的图片。"

            # 颜色分析
            if mode in ['RGB', 'RGBA']:
                # 转换为RGB
                rgb_image = image.convert('RGB')
                # 缩小图片进行颜色分析
                small = rgb_image.resize((100, 100))
                pixels = np.array(small)

                # 计算平均颜色
                avg_color = pixels.mean(axis=(0, 1))
                r, g, b = avg_color

                # 判断主色调
                if r > g and r > b:
                    color_desc = "偏红色调"
                elif g > r and g > b:
                    color_desc = "偏绿色调"
                elif b > r and b > g:
                    color_desc = "偏蓝色调"
                elif r + g + b > 600:
                    color_desc = "明亮色调"
                elif r + g + b < 200:
                    color_desc = "深暗色调"
                else:
                    color_desc = "中性色调"

                description += f"图片整体{color_desc}。"

            # 判断方向
            if width > height * 1.5:
                description += "这是一张横向构图的图片。"
            elif height > width * 1.5:
                description += "这是一张纵向构图的图片。"

            return description

        except Exception as e:
            logger.error(f"基础图像分析失败: {e}")
            return "这是一张图片，无法生成详细描述。"

    def _get_basic_info(self, image_path: str) -> str:
        """获取图片基础信息"""
        try:
            from PIL import Image
            image = Image.open(image_path)
            width, height = image.size
            return f"图片尺寸 {width}x{height} 像素"
        except:
            return ""
