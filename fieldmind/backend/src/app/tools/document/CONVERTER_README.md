# 统一文档转换器 (Unified Document Converter)

## 概述

整合了2个版本的文档转换器，提供统一、强大、可靠的文档转换服务。

### 整合的版本

1. **DocumentConverter** (87行) - 基于MarkItDown的基础转换器
2. **UnstructuredConverter** (284行) - 基于Unstructured的强大转换器

### 新增功能 ✨

1. **多策略自动降级** - Unstructured → MarkItDown → 纯文本，三层保障
2. **自动格式检测** - 自动识别并选择最佳转换策略
3. **表格提取和保留** - 准确提取文档中的表格数据
4. **结构识别** - 识别标题、段落、列表、表格等文档结构
5. **错误重试机制** - 可配置的重试次数和延迟
6. **批处理支持** - 高效处理多个文档
7. **转换质量评分** - 0-100分质量评分系统
8. **元数据增强** - 提取丰富的文档元数据

---

## 快速开始

### 基础用法

```python
from app.tools.document import UnifiedDocumentConverter

# 创建转换器
converter = UnifiedDocumentConverter()

# 转换文档
result = converter.convert("document.pdf")

print(f"文本: {result.text}")
print(f"策略: {result.strategy_used}")
print(f"质量: {result.quality_score}")
```

### 结构化转换

```python
# 保留文档结构
result = converter.convert("document.pdf", preserve_structure=True)

# 访问结构化元素
for element in result.elements:
    print(f"[{element['type']}] {element['text']}")
```

### 表格提取

```python
# 提取所有表格
tables = converter.extract_tables("document.pdf")

for i, table in enumerate(tables, 1):
    print(f"表格 {i}:\n{table}\n")
```

### 批量转换

```python
# 批量处理多个文档
files = ["doc1.pdf", "doc2.docx", "doc3.txt"]

def progress_callback(current, total, message):
    print(f"[{current}/{total}] {message}")

results = converter.batch_convert(files, progress_callback=progress_callback)

for result in results:
    print(f"{result.metadata['file_name']}: {result.quality_level}")
```

---

## 核心API

### UnifiedDocumentConverter

主要转换器类。

#### 初始化

```python
converter = UnifiedDocumentConverter(
    preferred_strategy=ConversionStrategy.UNSTRUCTURED,  # 首选策略
    max_retries=2,                                       # 最大重试次数
    retry_delay=0.5,                                     # 重试延迟(秒)
    enable_structure_detection=True,                     # 启用结构检测
    enable_table_extraction=True,                        # 启用表格提取
    min_text_length=10                                   # 最小文本长度
)
```

#### 主要方法

##### convert()

转换单个文档。

```python
result = converter.convert(
    file_path="document.pdf",
    preserve_structure=False,      # 是否保留结构
    extract_tables=None,           # 是否提取表格(None=自动)
    strategy=None,                 # 强制使用的策略
    progress_callback=None         # 进度回调
)
```

**返回**: `ConversionResult` 对象

##### batch_convert()

批量转换多个文档。

```python
results = converter.batch_convert(
    file_paths=["doc1.pdf", "doc2.docx"],
    progress_callback=callback
)
```

**返回**: `List[ConversionResult]`

##### extract_tables()

提取文档中的表格。

```python
tables = converter.extract_tables("document.pdf")
```

**返回**: `List[str]` - 表格文本列表

##### get_document_summary()

获取文档摘要信息。

```python
summary = converter.get_document_summary("document.pdf")
```

**返回**: 包含文档统计信息的字典

##### is_supported()

检查文件格式是否支持。

```python
if converter.is_supported("document.pdf"):
    result = converter.convert("document.pdf")
```

---

## 转换策略

### ConversionStrategy 枚举

- **UNSTRUCTURED** - 使用Unstructured库（最强，支持表格、OCR、结构）
- **MARKITDOWN** - 使用MarkItDown库（中等，支持常见格式）
- **PLAINTEXT** - 纯文本读取（兜底，总是可用）

### 自动降级机制

转换器会自动尝试多个策略，直到成功：

```
Unstructured (首选)
    ↓ 失败
MarkItDown (降级)
    ↓ 失败
纯文本读取 (兜底)
```

---

## 返回结果

### ConversionResult

```python
@dataclass
class ConversionResult:
    text: str                           # 提取的文本
    strategy_used: ConversionStrategy   # 使用的策略
    quality_score: float                # 质量分数(0-100)
    quality_level: ConversionQuality    # 质量等级
    elements: List[Dict]                # 结构化元素(可选)
    tables: List[str]                   # 提取的表格(可选)
    metadata: Dict                      # 元数据
    warnings: List[str]                 # 警告信息
    processing_time: float              # 处理时间(秒)
```

### 质量等级

- **EXCELLENT** - 90-100分（完美转换）
- **GOOD** - 70-89分（良好转换）
- **FAIR** - 50-69分（基本可用）
- **POOR** - <50分（质量较差）

### 质量评分因素

1. **文本长度** (30分) - 提取的文本量
2. **结构丰富度** (30分) - 识别的元素类型数量
3. **表格提取** (20分) - 提取的表格数量
4. **策略能力** (20分) - 使用的转换策略能力

---

## 便捷函数

### create_converter()

快速创建转换器实例。

```python
from app.tools.document import create_converter

converter = create_converter(max_retries=5)
```

### convert_document()

单次转换快捷方式。

```python
from app.tools.document import convert_document

result = convert_document("document.pdf")
print(result.text)
```

### batch_convert_documents()

批量转换快捷方式。

```python
from app.tools.document import batch_convert_documents

results = batch_convert_documents(["doc1.pdf", "doc2.docx"])
```

---

## 支持的格式

### Unstructured 支持的格式

- **文档**: PDF, DOCX, DOC, RTF, ODT
- **演示**: PPTX, PPT
- **表格**: XLSX, XLS, CSV
- **网页**: HTML, HTM, XML
- **文本**: TXT, MD, JSON
- **邮件**: MSG, EML
- **电子书**: EPUB

### MarkItDown 支持的格式

- **文档**: PDF, DOCX
- **演示**: PPTX
- **表格**: XLSX, CSV
- **网页**: HTML
- **文本**: TXT, MD, JSON

### 纯文本支持的格式

- **文本**: TXT, MD, CSV, JSON, XML, LOG

---

## 高级用法

### 自定义进度回调

```python
def my_progress_callback(message, progress):
    print(f"{message}: {progress*100:.1f}%")

result = converter.convert(
    "large_document.pdf",
    progress_callback=my_progress_callback
)
```

### 强制使用特定策略

```python
# 强制使用MarkItDown
result = converter.convert(
    "document.pdf",
    strategy=ConversionStrategy.MARKITDOWN
)
```

### 处理结构化元素

```python
result = converter.convert("document.pdf", preserve_structure=True)

for element in result.elements:
    elem_type = element['type']
    elem_text = element['text']
    elem_meta = element.get('metadata', {})
    
    if elem_type == 'Title':
        print(f"# {elem_text}")
    elif elem_type == 'Table':
        print(f"表格: {elem_text[:100]}...")
    else:
        print(elem_text)
```

### 获取详细文档信息

```python
summary = converter.get_document_summary("document.pdf")

print(f"文本长度: {summary['text_length']}")
print(f"词数: {summary['word_count']}")
print(f"质量分数: {summary['quality_score']}")
print(f"元素数量: {summary.get('element_count', 0)}")
print(f"表格数量: {summary.get('table_count', 0)}")

if 'element_types' in summary:
    print("元素类型分布:")
    for elem_type, count in summary['element_types'].items():
        print(f"  {elem_type}: {count}")
```

---

## 错误处理

### ConversionError

所有策略都失败时抛出。

```python
from app.tools.document import ConversionError

try:
    result = converter.convert("corrupt_file.pdf")
except ConversionError as e:
    print(f"转换失败: {e}")
```

### 检查警告

```python
result = converter.convert("document.txt")

if result.warnings:
    print("警告信息:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

### 质量检查

```python
result = converter.convert("document.pdf")

if result.quality_level == ConversionQuality.POOR:
    print("警告: 转换质量较差，可能丢失信息")
    print(f"质量分数: {result.quality_score}")
```

---

## 性能优化

### 批处理

批处理比单独转换效率更高：

```python
# ❌ 不推荐
results = []
for file in files:
    result = converter.convert(file)
    results.append(result)

# ✅ 推荐
results = converter.batch_convert(files)
```

### 策略选择

根据需求选择合适的策略：

```python
# 需要表格和结构 → 使用Unstructured
converter = UnifiedDocumentConverter(
    preferred_strategy=ConversionStrategy.UNSTRUCTURED
)

# 只需要文本 → 使用MarkItDown（更快）
converter = UnifiedDocumentConverter(
    preferred_strategy=ConversionStrategy.MARKITDOWN
)

# 纯文本文件 → 使用PLAINTEXT（最快）
converter = UnifiedDocumentConverter(
    preferred_strategy=ConversionStrategy.PLAINTEXT
)
```

### 禁用不需要的功能

```python
# 不需要结构检测和表格提取
converter = UnifiedDocumentConverter(
    enable_structure_detection=False,
    enable_table_extraction=False
)
```

---

## 迁移指南

### 从 DocumentConverter 迁移

**旧代码:**
```python
from app.services.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert_file("document.pdf")
text = result['text_content']
title = result['title']
```

**新代码:**
```python
from app.tools.document import UnifiedDocumentConverter

converter = UnifiedDocumentConverter()
result = converter.convert("document.pdf")
text = result.text
title = result.metadata.get('title')
```

### 从 UnstructuredConverter 迁移

**旧代码:**
```python
from app.services.document_converter_v2 import UnstructuredConverter

text = UnstructuredConverter.convert_to_text("document.pdf")
structured = UnstructuredConverter.convert_with_structure("document.pdf")
tables = UnstructuredConverter.extract_tables("document.pdf")
```

**新代码:**
```python
from app.tools.document import UnifiedDocumentConverter

converter = UnifiedDocumentConverter()

# 基础转换
result = converter.convert("document.pdf")
text = result.text

# 结构化转换
result = converter.convert("document.pdf", preserve_structure=True)
structured = result.elements

# 表格提取
tables = converter.extract_tables("document.pdf")
```

---

## 测试

运行测试套件：

```bash
cd /Users/alwan/FieldMind/backend
PYTHONPATH=src:$PYTHONPATH python3 -m pytest tests/tools/document/test_unified_document_converter.py -v
```

**测试覆盖**:
- 24个测试用例
- 100% 通过率
- 覆盖所有核心功能

---

## API对比

| 功能 | DocumentConverter | UnstructuredConverter | UnifiedDocumentConverter |
|------|-------------------|----------------------|--------------------------|
| 基础转换 | ✅ | ✅ | ✅ |
| 结构检测 | ❌ | ✅ | ✅ |
| 表格提取 | ❌ | ✅ | ✅ |
| 自动降级 | ❌ | ✅ (部分) | ✅ (完整) |
| 错误重试 | ❌ | ❌ | ✅ |
| 批处理 | ❌ | ❌ | ✅ |
| 质量评分 | ❌ | ❌ | ✅ |
| 进度回调 | ❌ | ❌ | ✅ |
| 多编码支持 | ❌ | ❌ | ✅ |
| 格式检测 | ✅ (部分) | ❌ | ✅ (完整) |

---

## 依赖

### 可选依赖

```bash
# Unstructured (推荐) - 最强大的转换能力
pip install "unstructured[all-docs]"

# MarkItDown - 轻量级转换
pip install markitdown

# 没有安装任何依赖也能工作（自动降级到纯文本）
```

---

## 常见问题

### Q: 为什么转换质量低？

A: 检查以下几点：
1. 是否安装了Unstructured？（最强转换能力）
2. 文档格式是否损坏？
3. 查看`result.warnings`了解具体问题
4. 查看`result.strategy_used`确认使用的策略

### Q: 如何处理大文件？

A: 
```python
# 使用进度回调监控进度
def progress(msg, pct):
    print(f"{msg}: {pct*100:.0f}%")

result = converter.convert("large.pdf", progress_callback=progress)
```

### Q: 转换失败怎么办？

A: 统一转换器有三层保障：
1. Unstructured (最强)
2. MarkItDown (中等)
3. 纯文本读取 (兜底)

如果全部失败，会抛出`ConversionError`并说明原因。

### Q: 表格格式是什么？

A: 表格以文本形式返回，通常是Markdown格式或结构化文本。使用Unstructured策略可以获得最佳表格识别效果。

---

## 更新日志

### v1.0.0 (2026-08-14)

- ✅ 整合DocumentConverter和UnstructuredConverter
- ✅ 实现多策略自动降级
- ✅ 添加质量评分系统
- ✅ 支持批量处理
- ✅ 添加结构检测和表格提取
- ✅ 实现错误重试机制
- ✅ 24个测试用例，100%通过

---

## 贡献者

- 统一转换器由FieldMind团队开发
- 基于DocumentConverter和UnstructuredConverter整合而成

---

## 许可

与FieldMind项目相同的许可协议。
