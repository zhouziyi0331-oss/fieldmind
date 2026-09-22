# P1 外部服务集成方案

## 🎯 目标

将现有的外部服务集成到文档规范化规则层，实现真正的音频转写、OCR识别、图像描述功能。

---

## 📊 现有服务情况

### 已存在的服务：

1. ✅ **AudioProcessor** (`audio_processor.py`)
   - 使用 Whisper 进行音频转写
   - 支持长音频切片
   - 已实现

2. ✅ **OCRService** (`ocr_service.py`)
   - 使用 PaddleOCR 进行文字识别
   - 支持中英文
   - 已实现

3. ❓ **视觉模型服务** - 需要创建

---

## 🔧 集成策略

### 方案1：直接集成（推荐）

修改文档规范化规则，直接调用现有服务：

```python
# AudioToTextRule._transcribe_audio() 调用 AudioProcessor
# ImageToTextRule._ocr_recognize() 调用 OCRService
# ImageToTextRule._generate_image_description() 调用 VisionService
```

### 方案2：适配器模式

创建适配器层，统一接口：

```python
class ServiceAdapter:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.ocr_service = OCRService()
        self.vision_service = VisionService()
```

**推荐方案1**，因为更直接、更简单。

---

## 📋 集成任务清单

### 任务1: 集成 AudioProcessor 到 AudioToTextRule ⏳

**文件**: `src/app/services/document_normalization/normalization_rules.py`

**修改位置**: `AudioToTextRule._transcribe_audio()`

**改动**:
```python
# 当前（模拟数据）
def _transcribe_audio(self, file_content: bytes, ...):
    return {"segments": [...模拟数据...]}

# 修改后（调用真实服务）
def _transcribe_audio(self, file_content: bytes, ...):
    from app.services.audio_processor import AudioProcessor
    processor = AudioProcessor()
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(file_content)
        temp_path = f.name
    
    # 调用转写
    result = processor.process_audio(temp_path)
    
    # 清理
    os.unlink(temp_path)
    
    return result
```

---

### 任务2: 集成 OCRService 到 ImageToTextRule ⏳

**文件**: `src/app/services/document_normalization/normalization_rules.py`

**修改位置**: 
- `ImageToTextRule._detect_text_regions()`
- `ImageToTextRule._ocr_recognize()`

**改动**:
```python
# 当前（模拟检测）
def _detect_text_regions(self, image_content: bytes):
    # 简单启发式...
    return []

# 修改后（调用真实OCR）
def _detect_text_regions(self, image_content: bytes):
    from app.services.ocr_service import OCRService
    ocr = OCRService()
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(image_content)
        temp_path = f.name
    
    # OCR识别
    result = ocr.recognize_image(temp_path)
    
    # 清理
    os.unlink(temp_path)
    
    # 提取文字区域
    regions = []
    if result and result.get('boxes'):
        for i, box in enumerate(result['boxes']):
            regions.append({
                'id': i + 1,
                'bbox': box['bbox'],
                'confidence': box.get('confidence', 0.8)
            })
    
    return regions
```

---

### 任务3: 创建 VisionService 用于图像描述 ⏳

**新建文件**: `src/app/services/vision_service.py`

**内容**:
```python
"""
视觉模型服务 - 图像描述生成

支持的模型：
1. BLIP-2 (推荐)
2. CLIP + GPT (备选)
3. GPT-4V API (如有key)
"""

import logging
from typing import Dict, Any
import tempfile
import os

logger = logging.getLogger(__name__)


class VisionService:
    """视觉模型服务"""

    def __init__(self, model_type: str = "blip2"):
        self.model_type = model_type
        self.model = None
        self._init_model()

    def _init_model(self):
        """初始化模型"""
        if self.model_type == "blip2":
            self._init_blip2()
        elif self.model_type == "gpt4v":
            self._init_gpt4v()
        else:
            self._init_fallback()

    def _init_blip2(self):
        """初始化 BLIP-2 模型"""
        try:
            from transformers import Blip2Processor, Blip2ForConditionalGeneration
            import torch

            logger.info("🔧 加载 BLIP-2 模型...")

            self.processor = Blip2Processor.from_pretrained(
                "Salesforce/blip2-opt-2.7b"
            )
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                "Salesforce/blip2-opt-2.7b",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )

            if torch.cuda.is_available():
                self.model = self.model.to("cuda")

            logger.info("✅ BLIP-2 模型加载成功")

        except Exception as e:
            logger.warning(f"⚠️ BLIP-2 加载失败: {e}")
            self._init_fallback()

    def _init_gpt4v(self):
        """初始化 GPT-4V API"""
        # TODO: 实现 GPT-4V 调用
        logger.info("🔧 使用 GPT-4V API")

    def _init_fallback(self):
        """降级方案：返回基础描述"""
        logger.info("⚠️ 使用降级方案：基础图像分析")
        self.model = None

    def describe_image(self, image_path: str, prompt: str = None) -> str:
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
        elif self.model_type == "gpt4v":
            return self._describe_with_gpt4v(image_path, prompt)
        else:
            return self._fallback_description(image_path)

    def _describe_with_blip2(self, image_path: str, prompt: str = None) -> str:
        """使用 BLIP-2 生成描述"""
        try:
            from PIL import Image
            import torch

            image = Image.open(image_path).convert('RGB')

            # 默认提示词
            if prompt is None:
                prompt = "请详细描述这张图片的内容，包括主体、环境、氛围等。"

            inputs = self.processor(image, text=prompt, return_tensors="pt")

            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            generated_ids = self.model.generate(**inputs, max_new_tokens=200)
            description = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0].strip()

            return description

        except Exception as e:
            logger.error(f"BLIP-2 描述生成失败: {e}")
            return self._fallback_description(image_path)

    def _describe_with_gpt4v(self, image_path: str, prompt: str = None) -> str:
        """使用 GPT-4V API 生成描述"""
        # TODO: 实现 GPT-4V API 调用
        return "图像描述（GPT-4V）"

    def _fallback_description(self, image_path: str) -> str:
        """降级方案：基础图像分析"""
        try:
            from PIL import Image

            image = Image.open(image_path)
            width, height = image.size
            mode = image.mode

            # 基础描述
            description = f"这是一张 {width}x{height} 像素的{mode}模式图片。"

            # 简单的颜色分析
            if mode == 'RGB':
                # 缩小图片进行颜色分析
                small = image.resize((100, 100))
                colors = small.getcolors(10000)
                if colors:
                    dominant_color = max(colors, key=lambda x: x[0])
                    description += f"主要色调偏向 RGB{dominant_color[1]}。"

            return description

        except Exception as e:
            logger.error(f"基础图像分析失败: {e}")
            return "无法生成图像描述。"
```

---

### 任务4: 集成 VisionService 到 ImageToTextRule ⏳

**文件**: `src/app/services/document_normalization/normalization_rules.py`

**修改位置**: `ImageToTextRule._generate_image_description()`

**改动**:
```python
# 当前（返回模拟描述）
def _generate_image_description(self, image_content: bytes, has_text: bool):
    return "模拟图像描述..."

# 修改后（调用真实服务）
def _generate_image_description(self, image_content: bytes, has_text: bool):
    from app.services.vision_service import VisionService
    
    vision = VisionService(model_type="blip2")  # 或 "gpt4v"
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(image_content)
        temp_path = f.name
    
    # 生成描述
    prompt = """请详细描述这张图片：
1. 主体内容是什么？
2. 有哪些关键元素？
3. 场景、环境、氛围如何？
4. 如果是自然景观，描述地理特征
5. 如果是人物，描述人物动作、表情
6. 如果是物品，描述物品特征、状态

要求：描述至少50字，具体明确。
"""
    
    description = vision.describe_image(temp_path, prompt)
    
    # 清理
    os.unlink(temp_path)
    
    return description
```

---

### 任务5: 集成 VideoToTextRule 视频处理 ⏳

**文件**: `src/app/services/document_normalization/additional_rules.py`

**修改**:
- `_extract_audio()` 使用 ffmpeg
- `_detect_scenes()` 使用 PySceneDetect
- `_extract_frame()` 使用 opencv
- `_describe_frame()` 调用 VisionService

---

## 📦 依赖包检查和安装

### 当前已安装（需验证）:

```bash
# 检查已安装的包
pip list | grep -E "paddleocr|whisper|torch|transformers|opencv"
```

### 需要的包:

1. **PaddleOCR** (OCR)
   ```bash
   pip install paddleocr paddlepaddle
   ```

2. **Whisper** (音频转写) - 可能已安装
   ```bash
   pip install openai-whisper
   ```

3. **BLIP-2** (图像描述)
   ```bash
   pip install transformers torch pillow
   ```

4. **视频处理**
   ```bash
   pip install opencv-python scenedetect[opencv]
   ```

5. **ffmpeg** (音视频处理) - 系统级
   ```bash
   brew install ffmpeg  # macOS
   ```

---

## 🚀 实施步骤

### 步骤1: 检查依赖 ⏳

```bash
cd /Users/alwan/Downloads/FieldMind/fieldmind/backend

# 检查已安装
pip list | grep -E "paddleocr|whisper|torch|transformers|opencv|scenedetect"

# 检查 ffmpeg
which ffmpeg
```

### 步骤2: 创建 VisionService ⏳

创建新文件 `src/app/services/vision_service.py`

### 步骤3: 修改规范化规则 ⏳

修改以下文件：
- `normalization_rules.py` (AudioToTextRule, ImageToTextRule)
- `additional_rules.py` (VideoToTextRule)

### 步骤4: 测试集成 ⏳

使用真实文件测试：
- 音频文件 → 验证 AudioProcessor 调用
- 图片文件 → 验证 OCRService 和 VisionService 调用
- 视频文件 → 验证完整视频处理流程

---

## ⚠️ 降级策略

如果某些模型无法加载（内存不足、GPU不可用等），使用降级方案：

1. **BLIP-2 失败** → 使用基础图像分析（颜色、尺寸）
2. **Whisper 失败** → 返回错误，要求用户手动上传文本
3. **PaddleOCR 失败** → 返回空文本，标记"需要OCR"

---

## 📊 预期效果

集成完成后：

| 功能 | 集成前 | 集成后 |
|------|--------|--------|
| 音频转写 | 返回模拟数据 | ✅ 真实转写（Whisper） |
| 图片OCR | 简单检测 | ✅ 真实识别（PaddleOCR） |
| 图像描述 | 模拟描述 | ✅ 真实描述（BLIP-2） |
| 视频处理 | 模拟数据 | ✅ 真实处理（ffmpeg+opencv） |

---

## 🎯 成功标准

1. ✅ 上传真实音频 → 得到完整转写文本
2. ✅ 上传真实图片 → 得到OCR文字 + 视觉描述
3. ✅ 上传真实Excel → 得到结构化数据（公式保留）
4. ✅ 上传真实PDF → 得到逐页文本
5. ✅ 所有处理结果写入数据库
6. ✅ 边界验证正常工作

---

需要我开始实施这些集成工作吗？
