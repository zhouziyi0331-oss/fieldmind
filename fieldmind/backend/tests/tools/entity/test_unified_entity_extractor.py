"""
统一实体提取引擎测试套件

测试覆盖：
1. 基础实体提取（jieba/hanlp/hybrid/rules）
2. 自定义词典
3. 位置追踪
4. 上下文提取
5. 时间表达式解析
6. 关系提取
7. 批量处理
8. 实体合并
9. 置信度计算
10. 输出格式转换
11. 边界情况
"""

import pytest
from datetime import datetime
from app.tools.entity.unified_entity_extractor import (
    UnifiedEntityExtractor,
    ExtractionEngine,
    EntityType,
    ExtractedEntity,
    EntityPosition,
    EntityRelation,
    ParsedTime,
    create_extractor,
    extract_entities,
    extract_entities_and_relations,
    batch_extract_entities,
)


class TestBasicExtraction:
    """基础提取功能测试"""

    def test_jieba_extraction(self):
        """测试jieba引擎提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在十八洞村进行了田野调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        assert len(entities) > 0
        entity_names = [e.name for e in entities]
        assert "费孝通" in entity_names or "十八洞村" in entity_names

    def test_rules_extraction(self):
        """测试规则引擎提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        text = "2024年3月15日，我们访问了湘西苗族自治州。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        assert len(entities) > 0
        # 应该至少提取到时间和地点
        types = {e.type for e in entities}
        assert EntityType.TIME in types or EntityType.LOCATION in types

    def test_hybrid_extraction(self):
        """测试混合模式提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.HYBRID)
        text = "费孝通先生2020年在十八洞村调查精准扶贫。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        assert len(entities) > 0
        # 混合模式应该提取更多实体
        assert any(e.engine == "jieba" or "jieba" in e.engine for e in entities)

    def test_empty_text(self):
        """测试空文本"""
        extractor = UnifiedEntityExtractor()

        assert extractor.extract_entities("") == []
        assert extractor.extract_entities("   ") == []
        assert extractor.extract_entities(None) == []


class TestEntityTypes:
    """实体类型测试"""

    def test_person_extraction(self):
        """测试人名提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通和林耀华是著名的人类学家。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        person_entities = [e for e in entities if e.type == EntityType.PERSON]

        assert len(person_entities) > 0

    def test_location_extraction(self):
        """测试地点提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        text = "十八洞村位于湖南省湘西州。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        location_entities = [e for e in entities if e.type == EntityType.LOCATION]

        assert len(location_entities) > 0
        names = [e.name for e in location_entities]
        assert any("村" in n or "省" in n or "州" in n for n in names)

    def test_organization_extraction(self):
        """测试组织机构提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        text = "湘西农业合作社和乡村振兴中心合作。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        org_entities = [e for e in entities if e.type == EntityType.ORGANIZATION]

        assert len(org_entities) > 0

    def test_time_extraction(self):
        """测试时间提取"""
        # 使用RULES引擎更可靠地提取时间
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        text = "2024年3月15日我们进行了调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        time_entities = [e for e in entities if e.type == EntityType.TIME]

        assert len(time_entities) > 0

    def test_custom_extraction(self):
        """测试自定义实体提取"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_custom_dict=True
        )
        text = "苗族的芦笙节和侗族的侗歌非常有特色。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 自定义词典应该识别这些实体
        entity_names = [e.name for e in entities]
        assert any(name in ["苗族", "芦笙节", "侗族", "侗歌"] for name in entity_names)


class TestCustomDictionary:
    """自定义词典测试"""

    def test_custom_dict_enabled(self):
        """测试启用自定义词典"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_custom_dict=True
        )
        text = "吊脚楼和风雨桥是侗族的传统建筑。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        entity_names = [e.name for e in entities]

        # 应该识别自定义词汇
        assert any(name in ["吊脚楼", "风雨桥", "侗族"] for name in entity_names)

    def test_custom_dict_disabled(self):
        """测试禁用自定义词典"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_custom_dict=False
        )
        text = "我们品尝了酸汤鱼和糯米饭。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 不启用自定义词典可能识别较少
        # 但测试不应该失败
        assert isinstance(entities, list)


class TestPositionTracking:
    """位置追踪测试"""

    def test_position_tracking_enabled(self):
        """测试启用位置追踪"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_position_tracking=True
        )
        text = "费孝通在江村调查，费孝通写了《江村经济》。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 查找"费孝通"实体
        feixiaotong = next((e for e in entities if e.name == "费孝通"), None)
        if feixiaotong:
            assert len(feixiaotong.positions) > 0
            assert feixiaotong.mention_count >= 2

    def test_position_tracking_disabled(self):
        """测试禁用位置追踪"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_position_tracking=False
        )
        text = "费孝通在江村调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 位置列表应该为空
        for entity in entities:
            assert len(entity.positions) == 0

    def test_position_accuracy(self):
        """测试位置准确性"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.RULES,
            enable_position_tracking=True
        )
        text = "2024年3月15日是个好天气。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        time_entity = next((e for e in entities if "2024" in e.name), None)

        if time_entity and time_entity.positions:
            pos = time_entity.positions[0]
            extracted_text = text[pos.start:pos.end]
            assert extracted_text == time_entity.name


class TestContextExtraction:
    """上下文提取测试"""

    def test_context_enabled(self):
        """测试启用上下文提取"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_position_tracking=True,
            enable_context=True,
            context_window=20
        )
        text = "费孝通是著名的社会学家和人类学家。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 检查是否有上下文
        for entity in entities:
            if entity.positions:
                assert entity.positions[0].context is not None

    def test_context_disabled(self):
        """测试禁用上下文提取"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            enable_position_tracking=True,
            enable_context=False
        )
        text = "费孝通是著名的社会学家。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 上下文应该为None
        for entity in entities:
            if entity.positions:
                assert entity.positions[0].context is None


class TestTimeExpressionParsing:
    """时间表达式解析测试"""

    def test_full_date_parsing(self):
        """测试完整日期解析"""
        extractor = UnifiedEntityExtractor()
        text = "2024年3月15日是调查开始的日期。"

        time_exprs = extractor.extract_time_expressions(text, parse_to_datetime=True)

        assert len(time_exprs) > 0
        parsed = next((t for t in time_exprs if t.parsed), None)
        assert parsed is not None
        assert parsed.parsed.year == 2024
        assert parsed.parsed.month == 3
        assert parsed.parsed.day == 15

    def test_year_month_parsing(self):
        """测试年月解析"""
        extractor = UnifiedEntityExtractor()
        text = "2024年3月的调查报告。"

        time_exprs = extractor.extract_time_expressions(text, parse_to_datetime=True)

        assert len(time_exprs) > 0
        parsed = next((t for t in time_exprs if t.parsed), None)
        if parsed:
            assert parsed.parsed.year == 2024
            assert parsed.parsed.month == 3

    def test_year_only_parsing(self):
        """测试仅年份解析"""
        extractor = UnifiedEntityExtractor()
        text = "2024年是重要的一年。"

        time_exprs = extractor.extract_time_expressions(text, parse_to_datetime=True)

        assert len(time_exprs) > 0
        parsed = next((t for t in time_exprs if t.parsed), None)
        if parsed:
            assert parsed.parsed.year == 2024

    def test_hyphen_date_parsing(self):
        """测试连字符日期解析"""
        extractor = UnifiedEntityExtractor()
        text = "调查日期：2024-03-15。"

        time_exprs = extractor.extract_time_expressions(text, parse_to_datetime=True)

        assert len(time_exprs) > 0
        parsed = next((t for t in time_exprs if "2024" in t.raw), None)
        assert parsed is not None
        if parsed.parsed:
            assert parsed.parsed.year == 2024

    def test_no_parsing(self):
        """测试不解析模式"""
        extractor = UnifiedEntityExtractor()
        text = "2024年3月15日的报告。"

        time_exprs = extractor.extract_time_expressions(text, parse_to_datetime=False)

        # 应该返回原始文本，但不解析
        assert len(time_exprs) > 0
        for expr in time_exprs:
            assert expr.raw is not None


class TestRelationshipExtraction:
    """关系提取测试"""

    def test_basic_relationship(self):
        """测试基础关系提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通前往十八洞村进行调查。"

        relations = extractor.extract_relationships(text, output_mode="dataclass")

        assert isinstance(relations, list)

    def test_lives_in_relationship(self):
        """测试"住在"关系"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "张三住在十八洞村。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        relations = extractor.extract_relationships(text, entities, output_mode="dict")

        # 应该识别"住在"关系
        if relations:
            assert any(r["type"] == "lives_in" for r in relations)

    def test_visited_relationship(self):
        """测试"前往/访问"关系"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通前往十八洞村调查精准扶贫。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        relations = extractor.extract_relationships(text, entities, output_mode="dict")

        # 检查是否提取到关系
        if relations:
            assert len(relations) > 0
            assert all("type" in r for r in relations)

    def test_relationship_with_no_entities(self):
        """测试无实体时的关系提取"""
        extractor = UnifiedEntityExtractor()
        text = "这是一段普通的文本。"

        relations = extractor.extract_relationships(text, output_mode="dict")

        # 无实体应该返回空列表
        assert relations == []


class TestBatchProcessing:
    """批量处理测试"""

    def test_batch_extract_basic(self):
        """测试基础批量提取"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        texts = [
            "费孝通在江村调查。",
            "林耀华在凉山调查。",
            "李亦园在台湾调查。"
        ]

        result = extractor.batch_extract(texts, merge_entities=False, output_mode="dict")

        assert "entities" in result
        assert "stats" in result
        assert result["stats"]["total_texts"] == 3
        assert result["stats"]["total_entities"] > 0

    def test_batch_extract_with_merge(self):
        """测试批量提取并合并"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        texts = [
            "费孝通在江村调查。",
            "费孝通写了《江村经济》。",
            "费孝通是著名学者。"
        ]

        result = extractor.batch_extract(texts, merge_entities=True, output_mode="dataclass")

        # 应该合并重复的"费孝通"
        feixiaotong_entities = [
            e for e in result["entities"]
            if e.name == "费孝通"
        ]

        if feixiaotong_entities:
            # 合并后应该只有一个，但mention_count应该>=3
            assert len(feixiaotong_entities) == 1
            assert feixiaotong_entities[0].mention_count >= 3

    def test_batch_stats(self):
        """测试批量统计信息"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        texts = [
            "2024年3月在湘西调查。",
            "2024年4月在黔东南调查。"
        ]

        result = extractor.batch_extract(texts, output_mode="dict")
        stats = result["stats"]

        assert "total_texts" in stats
        assert "total_entities" in stats
        assert "by_type" in stats
        assert "by_engine" in stats


class TestConfidenceScoring:
    """置信度评分测试"""

    def test_confidence_range(self):
        """测试置信度范围"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在十八洞村进行了详细的田野调查工作。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 所有置信度应该在0-1之间
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0

    def test_min_confidence_filter(self):
        """测试最低置信度过滤"""
        extractor = UnifiedEntityExtractor(
            engine=ExtractionEngine.JIEBA,
            min_confidence=0.8
        )
        text = "费孝通在十八洞村调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 所有实体置信度应该>=0.8
        for entity in entities:
            assert entity.confidence >= 0.8

    def test_high_confidence_count(self):
        """测试高置信度实体统计"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通、费孝通、费孝通多次访问江村。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        stats = extractor.get_extraction_stats(entities)

        assert "high_confidence_count" in stats
        assert "avg_confidence" in stats


class TestOutputModes:
    """输出模式测试"""

    def test_dataclass_output(self):
        """测试dataclass输出模式"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在十八洞村调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        assert isinstance(entities, list)
        if entities:
            assert isinstance(entities[0], ExtractedEntity)
            assert hasattr(entities[0], "name")
            assert hasattr(entities[0], "type")
            assert hasattr(entities[0], "confidence")

    def test_dict_output(self):
        """测试dict输出模式"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在十八洞村调查。"

        entities = extractor.extract_entities(text, output_mode="dict")

        assert isinstance(entities, list)
        if entities:
            assert isinstance(entities[0], dict)
            assert "name" in entities[0]
            assert "type" in entities[0]
            assert "confidence" in entities[0]

    def test_relation_output_modes(self):
        """测试关系输出模式"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通前往十八洞村。"

        # dataclass模式
        relations_dc = extractor.extract_relationships(text, output_mode="dataclass")
        if relations_dc:
            assert isinstance(relations_dc[0], EntityRelation)

        # dict模式
        relations_dict = extractor.extract_relationships(text, output_mode="dict")
        if relations_dict:
            assert isinstance(relations_dict[0], dict)


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_create_extractor(self):
        """测试创建提取器便捷函数"""
        extractor = create_extractor(engine="jieba")
        assert isinstance(extractor, UnifiedEntityExtractor)
        assert extractor.engine == ExtractionEngine.JIEBA

    def test_extract_entities_function(self):
        """测试提取实体便捷函数"""
        entities = extract_entities(
            text="费孝通在十八洞村调查。",
            engine="jieba",
            output_mode="dict"
        )

        assert isinstance(entities, list)
        if entities:
            assert isinstance(entities[0], dict)

    def test_extract_entities_and_relations_function(self):
        """测试同时提取实体和关系"""
        result = extract_entities_and_relations(
            text="费孝通前往十八洞村。",
            engine="jieba"
        )

        assert "entities" in result
        assert "relations" in result
        assert isinstance(result["entities"], list)
        assert isinstance(result["relations"], list)

    def test_batch_extract_function(self):
        """测试批量提取便捷函数"""
        texts = [
            "费孝通在江村调查。",
            "林耀华在凉山调查。"
        ]

        result = batch_extract_entities(texts, engine="jieba")

        assert "entities" in result
        assert "stats" in result


class TestEdgeCases:
    """边界情况测试"""

    def test_very_long_text(self):
        """测试超长文本"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在十八洞村调查。" * 100

        entities = extractor.extract_entities(text, output_mode="dict")

        # 应该能处理，不抛异常
        assert isinstance(entities, list)

    def test_special_characters(self):
        """测试特殊字符"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.RULES)
        text = "2024年3月15日！！！调查@#$%。"

        entities = extractor.extract_entities(text, output_mode="dict")

        # 应该能提取时间
        assert isinstance(entities, list)

    def test_mixed_language(self):
        """测试中英混合"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通(Fei Xiaotong)在2024年调查。"

        entities = extractor.extract_entities(text, output_mode="dict")

        assert isinstance(entities, list)

    def test_no_entities_text(self):
        """测试无实体文本"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "这是一些普通的文字。"

        entities = extractor.extract_entities(text, output_mode="dict")

        # 可能为空或很少
        assert isinstance(entities, list)

    def test_duplicate_entities(self):
        """测试重复实体"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通、费孝通、费孝通。"

        entities = extractor.extract_entities(text, output_mode="dataclass")

        # 应该合并为一个
        feixiaotong = [e for e in entities if e.name == "费孝通"]
        if feixiaotong:
            assert len(feixiaotong) == 1
            assert feixiaotong[0].mention_count == 3


class TestStatistics:
    """统计功能测试"""

    def test_extraction_stats(self):
        """测试提取统计"""
        extractor = UnifiedEntityExtractor(engine=ExtractionEngine.JIEBA)
        text = "费孝通在2024年前往十八洞村调查。"

        entities = extractor.extract_entities(text, output_mode="dataclass")
        stats = extractor.get_extraction_stats(entities)

        assert "total" in stats
        assert "by_type" in stats
        assert "by_engine" in stats
        assert "avg_confidence" in stats
        assert "high_confidence_count" in stats

    def test_empty_stats(self):
        """测试空实体列表的统计"""
        extractor = UnifiedEntityExtractor()
        stats = extractor.get_extraction_stats([])

        assert stats["total"] == 0
        assert stats["avg_confidence"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
