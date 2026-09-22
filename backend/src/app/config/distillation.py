"""
蒸馏系统配置

添加到 FieldMind 配置系统中
"""

# 蒸馏系统配置
DISTILLATION_OUTPUT_DIR = "/var/fieldmind/distillation/output"
DISTILLATION_TEMP_DIR = "/var/fieldmind/distillation/temp"
DISTILLATION_MAX_FILE_SIZE = "500MB"

# Whisper 配置（音频转写）
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"  # 或 "cpu"
WHISPER_COMPUTE_TYPE = "float16"

# 蒸馏模型配置
DISTILLATION_MODEL = "claude-opus-5"
DISTILLATION_MAX_TOKENS = 200000

# Jina Reader API（网页提取）
JINA_READER_API_KEY = "your-api-key"

# 蒸馏任务配置
DISTILLATION_AUTO_START = True  # 创建任务后自动启动
DISTILLATION_USER_CONFIRMATION_REQUIRED = False  # 是否需要用户确认各阶段

# 质量门配置
DISTILLATION_MIN_PASS_RATE = 0.8  # 压力测试最低通过率
DISTILLATION_MIN_EVIDENCE_ANCHORS = 1  # 知识单元最少证据锚点数
DISTILLATION_MIN_TEST_CASES = 5  # 方法单元最少测试用例数
