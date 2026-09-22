"""
HanLP 中文 NLP 测试脚本

测试 HanLP 服务的所有功能
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')


def test_hanlp_service():
    """测试 HanLP 服务"""

    print("=" * 60)
    print("🧪 HanLP 中文 NLP 服务测试")
    print("=" * 60)

    from app.services.nlp.hanlp_service import get_hanlp_service

    # 获取服务
    hanlp = get_hanlp_service()

    # 检查可用性
    print("\n1️⃣ 检查服务可用性...")
    if hanlp.is_available():
        print("   ✅ HanLP 服务可用")
    else:
        print("   ⚠️  HanLP 服务不可用（使用降级功能）")
        print("   💡 提示：运行 pip install hanlp 安装 HanLP")

    # 测试文本
    test_text = "北京大学位于北京市海淀区，是中国最著名的大学之一。"
    print(f"\n测试文本: {test_text}")

    # 1. 测试分词
    print("\n2️⃣ 测试中文分词...")
    tokens = hanlp.segment(test_text)
    print(f"   分词结果: {' / '.join(tokens)}")

    # 2. 测试词性标注
    print("\n3️⃣ 测试词性标注...")
    pos_tags = hanlp.pos_tag(test_text)
    if pos_tags:
        print("   词性标注:")
        for item in pos_tags[:5]:
            print(f"      {item['word']}/{item['pos']}")
        if len(pos_tags) > 5:
            print(f"      ... (共 {len(pos_tags)} 个词)")
    else:
        print("   ⚠️  词性标注功能不可用")

    # 3. 测试命名实体识别
    print("\n4️⃣ 测试命名实体识别...")
    entities = hanlp.recognize_entities(test_text)
    if entities:
        print("   识别到的实体:")
        for entity in entities:
            print(f"      {entity['text']} ({entity['type']})")
    else:
        print("   ⚠️  未识别到实体或功能不可用")

    # 4. 测试关键词提取
    print("\n5️⃣ 测试关键词提取...")
    keywords = hanlp.extract_keywords(test_text, top_k=5)
    if keywords:
        print("   关键词:")
        for kw in keywords:
            print(f"      {kw['word']}: {kw['score']:.3f}")
    else:
        print("   ⚠️  关键词提取功能不可用")

    # 5. 测试文本摘要
    print("\n6️⃣ 测试文本摘要...")
    long_text = """
    人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
    它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
    人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，
    可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
    """
    summary = hanlp.summarize(long_text.strip(), max_length=100)
    print(f"   摘要: {summary}")

    # 6. 测试情感分析
    print("\n7️⃣ 测试情感分析...")
    positive_text = "这个产品非常好用，我很喜欢！"
    negative_text = "这个产品太差了，非常失望。"

    sentiment1 = hanlp.sentiment_analysis(positive_text)
    print(f"   正面文本: {positive_text}")
    print(f"   情感: {sentiment1['sentiment']}, 分数: {sentiment1['score']:.2f}")

    sentiment2 = hanlp.sentiment_analysis(negative_text)
    print(f"   负面文本: {negative_text}")
    print(f"   情感: {sentiment2['sentiment']}, 分数: {sentiment2['score']:.2f}")

    # 7. 测试文本相似度
    print("\n8️⃣ 测试文本相似度...")
    text1 = "北京是中国的首都"
    text2 = "中国的首都是北京"
    text3 = "上海是中国的经济中心"

    sim1 = hanlp.text_similarity(text1, text2)
    sim2 = hanlp.text_similarity(text1, text3)

    print(f"   文本1: {text1}")
    print(f"   文本2: {text2}")
    print(f"   相似度: {sim1:.3f}")
    print(f"   文本3: {text3}")
    print(f"   相似度: {sim2:.3f}")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)

    # 总结
    print("\n📊 功能状态:")
    print(f"   {'✅' if hanlp.is_available() else '❌'} 服务可用性")
    print(f"   {'✅' if tokens else '❌'} 中文分词")
    print(f"   {'✅' if pos_tags else '⚠️ '} 词性标注")
    print(f"   {'✅' if entities else '⚠️ '} 命名实体识别")
    print(f"   {'✅' if keywords else '⚠️ '} 关键词提取")
    print(f"   {'✅' if summary else '❌'} 文本摘要")
    print(f"   ✅ 情感分析")
    print(f"   ✅ 文本相似度")


def test_unified_nlp_service():
    """测试统一 NLP 服务集成"""

    print("\n" + "=" * 60)
    print("🧪 测试统一 NLP 服务集成")
    print("=" * 60)

    from app.database import get_db
    from app.core.workbench_services import get_workbench_services

    db = next(get_db())

    try:
        services = get_workbench_services(db)

        print("\n1️⃣ 检查 NLP 服务状态...")
        info = services.nlp.get_info()
        print(f"   服务名称: {info.name}")
        print(f"   服务状态: {info.status.value}")
        print(f"   服务版本: {info.version}")

        test_text = "自然语言处理是人工智能的重要分支。"

        print(f"\n2️⃣ 测试分词...")
        tokens = services.nlp.tokenize(test_text)
        print(f"   结果: {' / '.join(tokens)}")

        print(f"\n3️⃣ 测试关键词提取...")
        keywords = services.nlp.extract_keywords(test_text, top_k=3)
        print(f"   结果: {keywords}")

        print(f"\n4️⃣ 测试实体识别...")
        entities = services.nlp.extract_entities(test_text)
        print(f"   结果: {entities}")

        print(f"\n5️⃣ 测试摘要...")
        summary = services.nlp.summarize(test_text)
        print(f"   结果: {summary}")

        print(f"\n6️⃣ 测试情感分析...")
        sentiment = services.nlp.sentiment_analysis(test_text)
        print(f"   结果: {sentiment}")

        print("\n✅ 统一 NLP 服务集成测试完成!")

    finally:
        db.close()


if __name__ == "__main__":
    # 测试 HanLP 服务
    test_hanlp_service()

    # 测试统一服务集成
    print("\n")
    test_unified_nlp_service()

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
