"""
PaddleOCR使用示例 - 7个实用场景演示
展示OCR服务在实际项目中的应用
"""
import asyncio
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io


# ==================== 辅助函数 ====================

def create_sample_image(text: str, filename: str = "sample.png") -> str:
    """创建示例图像"""
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
    except:
        font = ImageFont.load_default()

    draw.text((50, 150), text, fill='black', font=font)

    temp_path = f"/tmp/{filename}"
    img.save(temp_path)
    print(f"✅ 创建示例图像: {temp_path}")

    return temp_path


# ==================== 示例1: 基础图像OCR ====================

def example_1_basic_ocr():
    """示例1: 基础图像OCR识别"""
    print("\n" + "="*60)
    print("示例1: 基础图像OCR识别")
    print("="*60)

    from app.services.ocr_service import get_ocr_service

    # 创建测试图像
    image_path = create_sample_image(
        "FieldMind 田野调查系统\n文档智能识别测试"
    )

    # 初始化OCR服务
    ocr_service = get_ocr_service(lang="ch")

    # 执行OCR
    print("\n📄 正在识别图像...")
    result = ocr_service.recognize_image(image_path)

    # 输出结果
    print(f"\n✅ OCR识别完成:")
    print(f"  识别文本: {result.text}")
    print(f"  置信度: {result.confidence:.2%}")
    print(f"  文本块数: {result.total_blocks}")
    print(f"  处理时间: {result.processing_time:.2f}秒")
    print(f"  图像尺寸: {result.image_size}")

    # 详细的文本块信息
    print(f"\n📋 文本块详情:")
    for i, block in enumerate(result.text_blocks, 1):
        print(f"  块{i}: {block['text']}")
        print(f"       置信度: {block['confidence']:.2%}")
        print(f"       位置: {block['position']}")


# ==================== 示例2: 英文OCR识别 ====================

def example_2_english_ocr():
    """示例2: 英文OCR识别"""
    print("\n" + "="*60)
    print("示例2: 英文OCR识别")
    print("="*60)

    from app.services.ocr_service import get_ocr_service

    # 创建英文图像
    image_path = create_sample_image(
        "FieldMind Document System\nOCR Recognition Test 2024",
        "english_sample.png"
    )

    # 使用英文OCR引擎
    ocr_service = get_ocr_service(lang="en")

    print("\n📄 正在识别英文图像...")
    result = ocr_service.recognize_image(image_path, language="en")

    print(f"\n✅ 识别结果:")
    print(f"  Text: {result.text}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Blocks: {result.total_blocks}")


# ==================== 示例3: OCR质量检查 ====================

def example_3_quality_check():
    """示例3: OCR质量检查"""
    print("\n" + "="*60)
    print("示例3: OCR质量检查")
    print("="*60)

    from app.services.ocr_service import get_ocr_service
    from app.services.ocr_quality_checker import check_ocr_quality

    # 创建测试图像
    image_path = create_sample_image(
        "质量检查测试\n这是一段清晰的文本\n用于测试OCR质量评估功能"
    )

    # 执行OCR
    ocr_service = get_ocr_service()
    result = ocr_service.recognize_image(image_path)

    # 质量检查
    print("\n🔍 正在执行质量检查...")
    quality_report = check_ocr_quality(result)

    # 输出质量报告
    print(f"\n📊 质量报告:")
    print(f"  总体分数: {quality_report.overall_score:.1f}/100")
    print(f"  质量等级: {quality_report._get_grade()}")
    print(f"  置信度分数: {quality_report.confidence_score:.1f}")
    print(f"  文本质量分数: {quality_report.text_quality_score:.1f}")
    print(f"  布局分数: {quality_report.layout_score:.1f}")

    # 问题列表
    print(f"\n⚠️  发现 {len(quality_report.issues)} 个问题:")
    for issue in quality_report.issues:
        print(f"  [{issue.severity.upper()}] {issue.description}")
        if issue.suggestion:
            print(f"      建议: {issue.suggestion}")

    # 改进建议
    print(f"\n💡 改进建议:")
    for rec in quality_report.recommendations:
        print(f"  • {rec}")

    # 统计信息
    print(f"\n📈 文本统计:")
    stats = quality_report.statistics
    print(f"  总字符数: {stats['total_chars']}")
    print(f"  中文字符: {stats['chinese_char_count']}")
    print(f"  英文字符: {stats['english_char_count']}")
    print(f"  数字: {stats['digit_count']}")


# ==================== 示例4: 批量OCR处理 ====================

def example_4_batch_ocr():
    """示例4: 批量OCR处理"""
    print("\n" + "="*60)
    print("示例4: 批量OCR处理")
    print("="*60)

    from app.services.ocr_service import get_ocr_service

    # 创建多个测试图像
    image_paths = []
    texts = [
        "文档1: 田野调查报告",
        "文档2: 访谈记录",
        "文档3: 数据分析",
        "文档4: 研究总结"
    ]

    print("\n📝 创建测试图像...")
    for i, text in enumerate(texts, 1):
        path = create_sample_image(text, f"batch_{i}.png")
        image_paths.append(path)

    # 批量OCR
    ocr_service = get_ocr_service()

    print(f"\n🔄 批量处理 {len(image_paths)} 个图像（4个工作线程）...")
    results = ocr_service.recognize_batch(image_paths, max_workers=4)

    # 输出结果
    print(f"\n✅ 批量处理完成:")
    for i, result in enumerate(results, 1):
        if "error" not in result.metadata:
            print(f"  图像{i}: {result.text} (置信度: {result.confidence:.2%})")
        else:
            print(f"  图像{i}: 处理失败 - {result.metadata['error']}")

    # 统计信息
    total_time = sum(r.processing_time for r in results)
    avg_confidence = sum(r.confidence for r in results) / len(results)
    print(f"\n📊 批量处理统计:")
    print(f"  总处理时间: {total_time:.2f}秒")
    print(f"  平均置信度: {avg_confidence:.2%}")
    print(f"  平均单图时间: {total_time/len(results):.2f}秒")


# ==================== 示例5: PDF文档OCR ====================

def example_5_pdf_ocr():
    """示例5: PDF文档OCR（需要PyMuPDF）"""
    print("\n" + "="*60)
    print("示例5: PDF文档OCR")
    print("="*60)

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("\n⚠️  跳过此示例: PyMuPDF未安装")
        print("   安装命令: pip install pymupdf")
        return

    from app.services.ocr_service import get_ocr_service

    # 创建一个简单的PDF（实际项目中使用真实PDF）
    print("\n📄 此示例需要真实PDF文件")
    print("   使用方法:")
    print("   ```python")
    print("   ocr_service = get_ocr_service()")
    print("   results = ocr_service.recognize_pdf('document.pdf')")
    print("   ")
    print("   # 处理指定页码范围")
    print("   results = ocr_service.recognize_pdf(")
    print("       'document.pdf',")
    print("       page_range=(1, 5)  # 第1-5页")
    print("   )")
    print("   ")
    print("   # 提取全部文本")
    print("   full_text = '\\n\\n'.join(r.text for r in results)")
    print("   ```")


# ==================== 示例6: 区域文本提取 ====================

def example_6_region_extraction():
    """示例6: 区域文本提取"""
    print("\n" + "="*60)
    print("示例6: 区域文本提取")
    print("="*60)

    from app.services.ocr_service import get_ocr_service

    # 创建测试图像（模拟表单）
    image_path = create_sample_image(
        "姓名: 张三\n年龄: 28岁\n职业: 研究员\n部门: 田野调查组"
    )

    # 执行OCR
    ocr_service = get_ocr_service()
    result = ocr_service.recognize_image(image_path)

    print(f"\n✅ 完整识别文本:")
    print(result.text)

    # 提取特定区域的文本（根据坐标）
    print(f"\n🔍 区域文本提取:")
    print("  提取左上角区域（0-400, 0-200）:")
    region_text = result.get_text_by_region(0, 0, 400, 200)
    print(f"  {region_text}")

    # 获取低置信度文本块
    print(f"\n⚠️  低置信度文本块（<70%）:")
    low_conf_blocks = result.get_low_confidence_blocks(threshold=0.7)
    if low_conf_blocks:
        for block in low_conf_blocks:
            print(f"  {block['text']} (置信度: {block['confidence']:.2%})")
    else:
        print("  无")


# ==================== 示例7: 集成到文档处理流水线 ====================

def example_7_pipeline_integration():
    """示例7: 集成到文档处理流水线"""
    print("\n" + "="*60)
    print("示例7: 集成到文档处理流水线")
    print("="*60)

    from app.services.ocr_service import get_ocr_service
    from app.services.ocr_quality_checker import check_ocr_quality

    print("\n📋 模拟文档处理流程:")

    # 1. 上传文档（模拟）
    print("\n  步骤1: 上传扫描文档")
    image_path = create_sample_image(
        "项目报告\n2024年田野调查数据分析\n\n主要发现：\n1. 数据完整性良好\n2. 样本代表性高\n3. 结论可靠"
    )

    # 2. OCR识别
    print("  步骤2: OCR文本识别")
    ocr_service = get_ocr_service()
    ocr_result = ocr_service.recognize_image(image_path)
    print(f"    ✓ 识别到 {len(ocr_result.text)} 个字符")

    # 3. 质量检查
    print("  步骤3: 质量检查")
    quality_report = check_ocr_quality(ocr_result)
    print(f"    ✓ 质量分数: {quality_report.overall_score:.1f}/100")

    # 4. 根据质量决定是否需要人工审核
    print("  步骤4: 质量判断")
    if quality_report.overall_score >= 80:
        print("    ✓ 质量优良，自动通过")
        needs_review = False
    elif quality_report.overall_score >= 60:
        print("    ⚠️  质量中等，建议人工审核")
        needs_review = True
    else:
        print("    ❌ 质量较差，必须人工审核")
        needs_review = True

    # 5. 文本处理（分块、向量化等）
    print("  步骤5: 后续处理")
    if not needs_review:
        print("    ✓ 进入自动分块流程")
        print("    ✓ 进入向量化流程")
        print("    ✓ 存储到知识库")
    else:
        print("    ⏸  等待人工审核")

    # 6. 输出最终结果
    print(f"\n📊 处理结果:")
    print(f"  文本长度: {len(ocr_result.text)} 字符")
    print(f"  置信度: {ocr_result.confidence:.2%}")
    print(f"  质量等级: {quality_report._get_grade()}")
    print(f"  需要人工审核: {'是' if needs_review else '否'}")

    # 7. 统计信息
    stats = ocr_service.get_statistics()
    print(f"\n📈 OCR服务统计:")
    print(f"  总处理图像: {stats['total_images_processed']}")
    print(f"  总文本块: {stats['total_text_blocks']}")
    print(f"  平均置信度: {stats['average_confidence']:.2%}")
    print(f"  平均处理时间: {stats['average_time_per_image']:.2f}秒")


# ==================== 示例8: HTTP API调用示例 ====================

async def example_8_api_usage():
    """示例8: 通过HTTP API使用OCR"""
    print("\n" + "="*60)
    print("示例8: HTTP API调用示例")
    print("="*60)

    print("\n📡 API端点使用示例:")

    # 1. 单图像识别
    print("\n1️⃣  单图像OCR识别:")
    print("```bash")
    print("curl -X POST 'http://localhost:8000/api/ocr/recognize' \\")
    print("  -F 'file=@document.jpg' \\")
    print("  -F 'language=ch' \\")
    print("  -F 'enable_quality_check=true'")
    print("```")

    # 2. PDF识别
    print("\n2️⃣  PDF文档OCR:")
    print("```bash")
    print("curl -X POST 'http://localhost:8000/api/ocr/recognize-pdf' \\")
    print("  -F 'file=@report.pdf' \\")
    print("  -F 'start_page=1' \\")
    print("  -F 'end_page=10'")
    print("```")

    # 3. 批量识别
    print("\n3️⃣  批量图像OCR:")
    print("```bash")
    print("curl -X POST 'http://localhost:8000/api/ocr/recognize-batch' \\")
    print("  -F 'files=@img1.jpg' \\")
    print("  -F 'files=@img2.jpg' \\")
    print("  -F 'files=@img3.jpg' \\")
    print("  -F 'max_workers=4'")
    print("```")

    # 4. 质量检查
    print("\n4️⃣  OCR质量检查:")
    print("```bash")
    print("curl -X POST 'http://localhost:8000/api/ocr/quality-check' \\")
    print("  -F 'file=@scan.jpg'")
    print("```")

    # 5. 查询支持的语言
    print("\n5️⃣  查询支持的语言:")
    print("```bash")
    print("curl 'http://localhost:8000/api/ocr/supported-languages'")
    print("```")

    # 6. 获取统计信息
    print("\n6️⃣  获取服务统计:")
    print("```bash")
    print("curl 'http://localhost:8000/api/ocr/statistics'")
    print("```")

    # 7. 健康检查
    print("\n7️⃣  健康检查:")
    print("```bash")
    print("curl 'http://localhost:8000/api/ocr/health'")
    print("```")

    # Python客户端示例
    print("\n\n🐍 Python客户端示例:")
    print("```python")
    print("import requests")
    print("")
    print("# 单图像OCR")
    print("with open('document.jpg', 'rb') as f:")
    print("    response = requests.post(")
    print("        'http://localhost:8000/api/ocr/recognize',")
    print("        files={'file': f},")
    print("        params={'language': 'ch', 'enable_quality_check': True}")
    print("    )")
    print("    result = response.json()")
    print("    print(f\"识别文本: {result['text']}\")")
    print("    print(f\"置信度: {result['confidence']:.2%}\")")
    print("```")


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print(" "*15 + "PaddleOCR使用示例集合")
    print("="*70)

    examples = [
        ("基础图像OCR", example_1_basic_ocr),
        ("英文OCR识别", example_2_english_ocr),
        ("OCR质量检查", example_3_quality_check),
        ("批量OCR处理", example_4_batch_ocr),
        ("PDF文档OCR", example_5_pdf_ocr),
        ("区域文本提取", example_6_region_extraction),
        ("集成到处理流水线", example_7_pipeline_integration),
    ]

    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n运行示例...")

    try:
        # 运行前7个示例
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\n❌ 示例失败: {e}")
                import traceback
                traceback.print_exc()

        # 运行API示例（异步）
        asyncio.run(example_8_api_usage())

    except KeyboardInterrupt:
        print("\n\n⏸  示例运行被中断")

    print("\n" + "="*70)
    print("示例运行完成！")
    print("="*70)


if __name__ == "__main__":
    main()
