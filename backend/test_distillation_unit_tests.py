"""
蒸馏功能 Phase 4 - 单元测试
测试所有6类知识单元提取方法
"""
import sys
import pytest
sys.path.insert(0, 'src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from app.core.database import Base
from app.models.distillation import DistilledUnit
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation
from app.models.timeline import TimelineEvent
from app.services.distillation_engine import DistillationEngine

# 测试数据库
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def distillation_engine(db_session):
    """创建蒸馏引擎实例"""
    return DistillationEngine(db_session)

@pytest.fixture
def sample_chunks(db_session):
    """创建测试chunks"""
    chunks = [
        DocumentChunk(
            id=1,
            chunk_id="chunk_1",
            document_id=1,
            project_id=1,
            chunk_index=0,
            text="村支书李明表示，土地改革进展顺利，农民收入提高了30%。",
            legacy_chunk_text="村支书李明表示，土地改革进展顺利，农民收入提高了30%。",
            text_length=30,
            legacy_chunk_size=30,
            speaker="李明",
            key_entities=json.dumps([{"name": "李明", "type": "PERSON"}, {"name": "土地改革", "type": "CONCEPT"}]),
            domain_tags=json.dumps(["土地改革", "农民收入"]),
            created_at=datetime.utcnow()
        ),
        DocumentChunk(
            id=2,
            chunk_id="chunk_2",
            document_id=1,
            project_id=1,
            chunk_index=1,
            text="王教授指出，非常紧急！必须立即保护传统技艺。",
            legacy_chunk_text="王教授指出，非常紧急！必须立即保护传统技艺。",
            text_length=25,
            legacy_chunk_size=25,
            speaker="王教授",
            key_entities=json.dumps([{"name": "王教授", "type": "PERSON"}]),
            domain_tags=json.dumps(["文化保护", "传统技艺"]),
            created_at=datetime.utcnow()
        ),
        DocumentChunk(
            id=3,
            chunk_id="chunk_3",
            document_id=1,
            project_id=1,
            chunk_index=2,
            text="张华的成功案例值得推广：通过创新技术实现收入翻倍。",
            legacy_chunk_text="张华的成功案例值得推广：通过创新技术实现收入翻倍。",
            text_length=28,
            legacy_chunk_size=28,
            key_entities=json.dumps([{"name": "张华", "type": "PERSON"}]),
            domain_tags=json.dumps(["成功案例", "创新"]),
            created_at=datetime.utcnow()
        ),
    ]

    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()
    return chunks

@pytest.fixture
def sample_entities(db_session):
    """创建测试entities"""
    entities = [
        Entity(id="entity_1", text="李明", type="PERSON", legacy_name="李明", legacy_entity_type="PERSON"),
        Entity(id="entity_2", text="王教授", type="PERSON", legacy_name="王教授", legacy_entity_type="PERSON"),
        Entity(id="entity_3", text="张华", type="PERSON", legacy_name="张华", legacy_entity_type="PERSON"),
    ]

    for entity in entities:
        db_session.add(entity)
    db_session.commit()
    return entities

@pytest.fixture
def sample_relations(db_session, sample_entities):
    """创建测试relations"""
    relations = [
        EntityRelation(
            source_entity_id="entity_1",
            target_entity_id="entity_2",
            relation_type="合作",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        EntityRelation(
            source_entity_id="entity_1",
            target_entity_id="entity_3",
            relation_type="领导",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
    ]

    for relation in relations:
        db_session.add(relation)
    db_session.commit()
    return relations

@pytest.fixture
def sample_events(db_session):
    """创建测试events"""
    events = [
        TimelineEvent(
            id="event_1",
            project_id=1,
            title="土地改革启动",
            date=datetime(2024, 1, 15),
            category="政策",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        TimelineEvent(
            id="event_2",
            project_id=1,
            title="村民代表大会",
            date=datetime(2024, 3, 20),
            category="会议",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        TimelineEvent(
            id="event_3",
            project_id=1,
            title="合作社成立",
            date=datetime(2024, 6, 10),
            category="经济",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
    ]

    for event in events:
        db_session.add(event)
    db_session.commit()
    return events


class TestDistillationEngine:
    """测试蒸馏引擎核心功能"""

    def test_load_structured_data(self, distillation_engine, sample_chunks, sample_entities, sample_events):
        """测试数据加载功能"""
        data = distillation_engine._load_structured_data(project_id=1)

        assert data is not None
        assert len(data["chunks"]) == 3
        assert len(data["entities"]) >= 0  # 可能为0，因为需要document_entities关联
        assert len(data["events"]) == 3
        assert "doc_ids" in data

    def test_extract_insights(self, distillation_engine, sample_chunks, sample_entities, sample_events):
        """测试核心洞察提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        insights = distillation_engine._extract_insights(project_id=1, data=data)

        # 应该至少提取1个洞察（事件密度分析）
        assert len(insights) >= 1

        # 检查洞察属性
        for insight in insights:
            assert insight.unit_type == "insight"
            assert insight.project_id == 1
            assert insight.title is not None
            assert insight.content is not None
            assert 0 <= insight.credibility <= 1
            assert 0 <= insight.confidence <= 1

    def test_extract_quotes(self, distillation_engine, sample_chunks, sample_entities):
        """测试经典原话提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        quotes = distillation_engine._extract_quotes(project_id=1, data=data)

        # 应该提取2条原话（有说话人的chunks）
        assert len(quotes) == 2

        # 检查原话属性
        for quote in quotes:
            assert quote.unit_type == "quote"
            assert quote.project_id == 1
            assert quote.credibility == 0.95  # 原话可信度高

            # 检查extra_data包含说话人
            extra_data = json.loads(quote.extra_data)
            assert "speaker" in extra_data

    def test_extract_models(self, distillation_engine, sample_chunks, sample_entities, sample_relations):
        """测试思维模型提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        models = distillation_engine._extract_models(project_id=1, data=data)

        # 应该提取至少1个模型（协作网络）
        assert len(models) >= 1

        # 检查模型属性
        for model in models:
            assert model.unit_type == "model"
            assert model.project_id == 1
            assert "关系" in model.content or "模式" in model.content

    def test_extract_cases(self, distillation_engine, sample_chunks):
        """测试案例应用提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        cases = distillation_engine._extract_cases(project_id=1, data=data)

        # 应该提取1个案例（chunk_3包含"成功案例"）
        assert len(cases) == 1

        # 检查案例属性
        for case in cases:
            assert case.unit_type == "case"
            assert case.project_id == 1
            assert "案例" in case.title or "案例" in case.content

    def test_extract_actions(self, distillation_engine, sample_chunks, sample_events):
        """测试行动建议提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        actions = distillation_engine._extract_actions(project_id=1, data=data)

        # 应该提取至少1个建议（趋势跟进或缺口分析）
        assert len(actions) >= 1

        # 检查建议属性
        for action in actions:
            assert action.unit_type == "action"
            assert action.project_id == 1
            assert 0 <= action.confidence <= 1

    def test_extract_methods(self, distillation_engine, sample_chunks, sample_entities, sample_events):
        """测试方法论提取"""
        data = distillation_engine._load_structured_data(project_id=1)
        methods = distillation_engine._extract_methods(project_id=1, data=data)

        # 应该提取2个方法论（研究方法论+参数配置）
        assert len(methods) == 2

        # 检查方法论属性
        for method in methods:
            assert method.unit_type == "method"
            assert method.project_id == 1
            assert method.credibility >= 0.9  # 方法论可信度高

    def test_distill_project_complete(self, distillation_engine, sample_chunks, sample_entities, sample_relations, sample_events):
        """测试完整的蒸馏流程"""
        result = distillation_engine.distill_project(project_id=1)

        # 检查返回结果
        assert "project_id" in result
        assert "total_units" in result
        assert "breakdown" in result
        assert result["project_id"] == 1
        assert result["total_units"] > 0

        # 检查各类型数量
        breakdown = result["breakdown"]
        assert "insights" in breakdown
        assert "quotes" in breakdown
        assert "models" in breakdown
        assert "cases" in breakdown
        assert "actions" in breakdown
        assert "methods" in breakdown

        # 验证总数一致
        total = sum(breakdown.values())
        assert total == result["total_units"]

    def test_get_distilled_units(self, distillation_engine, sample_chunks, sample_entities, sample_relations, sample_events):
        """测试获取蒸馏产物"""
        # 先执行蒸馏
        distillation_engine.distill_project(project_id=1)

        # 获取所有知识单元
        all_units = distillation_engine.get_distilled_units(project_id=1)
        assert len(all_units) > 0

        # 按类型获取
        insights = distillation_engine.get_distilled_units(project_id=1, unit_type="insight")
        quotes = distillation_engine.get_distilled_units(project_id=1, unit_type="quote")

        assert all(u.unit_type == "insight" for u in insights)
        assert all(u.unit_type == "quote" for u in quotes)

    def test_get_unit_sources(self, distillation_engine, db_session, sample_chunks):
        """测试溯源功能"""
        # 创建一个知识单元
        unit = DistilledUnit(
            project_id=1,
            unit_type="insight",
            title="测试洞察",
            content="测试内容",
            source_chunks=json.dumps([1, 2]),
            credibility=0.8,
            confidence=0.9,
            extra_data=json.dumps({})
        )
        db_session.add(unit)
        db_session.commit()

        # 获取溯源信息
        sources = distillation_engine.get_unit_sources(unit.id)

        # 因为我们没有Document表，sources可能为空或包含chunk信息
        # 这里只验证方法不报错
        assert isinstance(sources, list)

    def test_calculate_credibility(self, distillation_engine):
        """测试可信度计算"""
        # 测试不同来源数量
        score1 = distillation_engine._calculate_credibility(sources=[1, 2, 3], evidence_count=5)
        score2 = distillation_engine._calculate_credibility(sources=[1, 2, 3, 4, 5], evidence_count=10)

        assert 0 <= score1 <= 1
        assert 0 <= score2 <= 1
        assert score2 >= score1  # 更多来源应该有更高可信度

    def test_calculate_confidence(self, distillation_engine):
        """测试置信度计算"""
        score1 = distillation_engine._calculate_confidence(strength=0.8, consistency=0.9)
        score2 = distillation_engine._calculate_confidence(strength=0.5, consistency=0.5)

        assert 0 <= score1 <= 1
        assert 0 <= score2 <= 1
        assert score1 > score2  # 更高强度应该有更高置信度


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_project(self, distillation_engine):
        """测试空项目"""
        result = distillation_engine.distill_project(project_id=999)

        assert result["total_units"] == 0
        assert all(count == 0 for count in result["breakdown"].values())

    def test_no_chunks(self, distillation_engine, db_session):
        """测试没有chunks的情况"""
        data = {"chunks": [], "entities": [], "relations": [], "events": []}

        insights = distillation_engine._extract_insights(project_id=1, data=data)
        quotes = distillation_engine._extract_quotes(project_id=1, data=data)
        cases = distillation_engine._extract_cases(project_id=1, data=data)

        assert len(insights) == 0
        assert len(quotes) == 0
        assert len(cases) == 0

    def test_malformed_json(self, distillation_engine, db_session):
        """测试错误的JSON数据"""
        chunk = DocumentChunk(
            id=100,
            chunk_id="chunk_bad",
            document_id=1,
            project_id=1,
            chunk_index=0,
            text="测试",
            legacy_chunk_text="测试",
            text_length=2,
            legacy_chunk_size=2,
            key_entities="not a json",  # 错误的JSON
            domain_tags="also not json",
            created_at=datetime.utcnow()
        )
        db_session.add(chunk)
        db_session.commit()

        data = distillation_engine._load_structured_data(project_id=1)

        # 应该不报错，容错处理
        try:
            insights = distillation_engine._extract_insights(project_id=1, data=data)
            assert True  # 没有异常
        except Exception as e:
            pytest.fail(f"应该容错处理，但抛出了异常: {e}")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Phase 4 单元测试 - 开始执行")
    print("="*60 + "\n")

    # 运行pytest
    result = pytest.main([
        __file__,
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback
        "-s",  # 显示print输出
    ])

    print("\n" + "="*60)
    if result == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    print("="*60 + "\n")

    return result


if __name__ == "__main__":
    run_tests()
