"""
KnowledgeAgent - 知识构建专员

⚠️ 已废弃：此Agent将在v2.0中移除，已被 app.agents.v2.knowledge_agent.KnowledgeAgent 替代

职责：
1. 从文本中提取实体（人物、地名、机构、时间、文化概念）
2. 提取实体间关系（亲缘、师徒、行为、空间、时间）
3. 共现分析（句子级窗口）
4. 跨文档实时合并（同名/同义实体）
5. 构建知识图谱
6. 输出多种格式（D3.js、思维导图）

触发：TranscriptAgent 完成后自动触发
"""

import re
import json
import logging
import os
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import jieba
import jieba.posseg as pseg
from dataclasses import dataclass, asdict

# 知识图谱
try:
    import networkx as nx
except ImportError:
    nx = None

# 向量相似度
from sentence_transformers import SentenceTransformer

# LLM 客户端
try:
    import openai
except ImportError:
    openai = None

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask, AgentResult, AgentStatus
from app.services.dynamic_discovery import DynamicDiscoveryEngine
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


@deprecated(
    reason="旧Agent已被6-Agent v2完全替代",
    replacement="app.agents.v2.knowledge_agent.KnowledgeAgent",
    version="2.0"
)
@dataclass
class Entity:
    """实体数据类"""
    实体ID: str
    实体名称: str
    实体类型: str  # 人物/地名-行政/地名-地标/机构/时间/文化概念-传统/文化概念-仪式
    提及次数: int
    出现文档: List[str]
    上下文片段: List[str]
    关联实体: List[str]
    首次出现时间戳: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class Relation:
    """关系数据类"""
    关系ID: str
    主体: str
    关系类型: str  # 亲缘/师徒/行为/空间/时间/从属/参与
    客体: str
    上下文: str
    时间戳: float
    来源文档: str
    置信度: float = 1.0

    def to_dict(self):
        return asdict(self)


@dataclass
class CoOccurrence:
    """共现数据类"""
    共现实体组: List[str]
    共现频次: int
    窗口类型: str  # 句子级
    关联话题: str = ""

    def to_dict(self):
        return asdict(self)


@deprecated(
    reason="旧Agent已被6-Agent v2完全替代",
    replacement="app.agents.v2.knowledge_agent.KnowledgeAgent",
    version="2.0"
)
class KnowledgeAgent(AgentBase):
    """知识构建Agent"""

    @property
    def role(self) -> AgentRole:
        """Agent角色"""
        return AgentRole.ENTITY  # 使用 ENTITY 角色（知识构建）

    @property
    def name(self) -> str:
        """Agent名称"""
        return "知识构建专员"

    @property
    def description(self) -> str:
        """Agent描述"""
        return "从文本中提取实体、关系，构建知识图谱，支持跨文档实时合并"

    @property
    def capabilities(self) -> List[str]:
        """Agent能力列表"""
        return [
            "命名实体识别（人物、地名、机构、时间、文化概念）",
            "关系抽取（亲缘、师徒、行为、空间、时间）",
            "共现分析（句子级窗口）",
            "跨文档实时合并",
            "知识图谱构建",
            "多格式输出（D3.js、思维导图）"
        ]

    def _initialize_tools(self):
        """初始化工具集"""
        self.tools = {
            'discovery_engine': None,  # 延迟初始化
            'embedder': None
        }

    # 细粒度地名词典（固定 + 可扩展）
    LANDMARK_KEYWORDS = [
        "村史馆", "祠堂", "村委会", "古树", "菜地", "水井", "广场",
        "戏台", "庙宇", "牌坊", "石桥", "老屋", "学堂", "市场",
        "档案馆", "博物馆", "纪念馆", "文化馆", "活动中心"
    ]

    # 文化概念词典
    CULTURE_TRADITIONAL = [
        "山歌", "民歌", "戏曲", "舞蹈", "手工艺", "蜡染", "刺绣",
        "织布", "银饰", "剪纸", "木雕", "石雕", "陶艺", "编织"
    ]

    CULTURE_RITUAL = [
        "祭祀", "婚礼", "葬礼", "节日", "祭祖", "庙会", "祈福",
        "成人礼", "满月酒", "丧葬", "祭典", "仪式", "庆典"
    ]

    # 关系类型模板
    RELATION_PATTERNS = {
        "亲缘关系": [
            (r"(\S+)是(\S+)的(父亲|母亲|儿子|女儿|兄弟|姐妹|丈夫|妻子|爷爷|奶奶|孙子|孙女)", "亲缘"),
            (r"(\S+)的(父亲|母亲|儿子|女儿|兄弟|姐妹|丈夫|妻子)是(\S+)", "亲缘"),
        ],
        "师徒关系": [
            (r"(\S+)教(\S+)(学|跳|唱|做|制作)?(\S+)", "教授"),
            (r"(\S+)跟(\S+)学(\S+)", "学习"),
            (r"(\S+)是(\S+)的(老师|师傅|徒弟|学生)", "师徒"),
        ],
        "空间关系": [
            (r"(\S+)在(\S+)(住|生活|工作|居住)", "位于"),
            (r"(\S+)去(了)?(\S+)", "前往"),
            (r"(\S+)从(\S+)来", "来自"),
        ],
        "参与关系": [
            (r"(\S+)参加(了)?(\S+)", "参与"),
            (r"(\S+)参与(了)?(\S+)", "参与"),
        ],
    }

    def __init__(self, agent_id: str = None):
        super().__init__(agent_id)

        # 初始化NER引擎
        self.discovery_engine = None

        # 初始化向量模型（用于实体消歧）
        self.embedder = None

        # 知识图谱存储
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.co_occurrences: List[CoOccurrence] = []

        # 图结构
        self.graph = nx.DiGraph() if nx else None

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务的具体实现（同步版本）

        注意：这是基类要求的同步方法，实际调用 execute 异步方法
        """
        import asyncio
        return asyncio.run(self.execute(task.input_data))

    def _init_models(self):
        """延迟初始化模型"""
        if self.discovery_engine is None:
            logger.info("🚀 初始化 DynamicDiscoveryEngine...")
            self.discovery_engine = DynamicDiscoveryEngine()

        if self.embedder is None:
            logger.info("🚀 初始化向量模型...")
            # 使用已安装的模型（与 DynamicDiscoveryEngine 一致）
            self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识构建任务

        Args:
            task_input: {
                "doc_id": "doc_999",
                "text": "清洗后的文本",
                "segments": [...],  # 时间戳信息
                "existing_entities": [...],  # TranscriptAgent已提取的实体
                "enable_llm": True  # 是否启用LLM辅助
            }

        Returns:
            包含实体、关系、知识图谱的字典
        """
        doc_id = task_input.get('doc_id', 'unknown')
        text = task_input.get('text', '')
        segments = task_input.get('segments', [])
        existing_entities = task_input.get('existing_entities', [])
        enable_llm = task_input.get('enable_llm', True)

        logger.info(f"📚 KnowledgeAgent 开始处理文档: {doc_id}")

        # 初始化模型
        self._init_models()

        # Step 1: 加载已有知识图谱（跨文档合并）
        await self._load_existing_knowledge_graph(doc_id)

        # Step 2: 实体提取（复用 + 补充）
        logger.info("🔍 Step 1/6: 提取实体...")
        entities = self._extract_entities(text, segments, existing_entities, doc_id)

        # Step 2.5: 实体消歧（向量相似度）
        logger.info("🔗 Step 2/6: 实体消歧...")
        entity_map = self._disambiguate_entities(entities, similarity_threshold=0.85)
        if entity_map:
            entities = self._apply_entity_mapping(entities, entity_map)
            logger.info(f"   ✅ 实体消歧完成: 合并 {len(entity_map)} 对同义实体")

        # Step 3: 关系提取
        logger.info("🔗 Step 3/6: 提取关系...")
        relations = self._extract_relations(text, segments, entities, doc_id, enable_llm)

        # Step 4: 共现分析
        logger.info("📊 Step 4/6: 共现分析...")
        co_occurrences = self._analyze_co_occurrence(text, entities)

        # Step 5: 实时合并到知识图谱
        logger.info("🔄 Step 5/6: 合并到知识图谱...")
        self._merge_into_knowledge_graph(entities, relations, co_occurrences, doc_id)

        # Step 6: 构建图结构
        logger.info("🕸️ Step 6/7: 构建知识图谱...")
        graph_data = self._build_graph()

        # Step 7: 持久化到数据库
        logger.info("💾 Step 7/7: 持久化到数据库...")
        db_session = task_input.get('db_session')  # 外部传入的数据库会话
        if db_session:
            await self._persist_to_database(db_session, doc_id)
        else:
            logger.warning("   ⚠️ 未提供数据库会话，跳过持久化")

        # 生成多格式输出
        output = {
            "实体列表": [e.to_dict() for e in self.entities.values()],
            "关系列表": [r.to_dict() for r in self.relations],
            "共现分析": [co.to_dict() for co in self.co_occurrences],
            "知识图谱统计": {
                "节点总数": len(self.entities),
                "边总数": len(self.relations),
                "核心节点": self._get_core_nodes(top_n=10),
                "社区聚类": self._detect_communities() if self.graph else []
            },
            "可视化数据": {
                "d3_graph": graph_data['d3'],
                "mindmap": graph_data['mindmap']
            }
        }

        logger.info(f"✅ KnowledgeAgent 完成: {len(self.entities)}个实体, {len(self.relations)}个关系")

        return output

    async def _load_existing_knowledge_graph(self, current_doc_id: str):
        """加载已有知识图谱（用于跨文档合并）"""
        logger.info("📥 加载已有知识图谱...")

        # 从数据库加载需要在 execute 中通过 db_session 实现
        # 这里暂时保持内存模式，数据库加载在 _load_from_database 中实现
        pass

    async def _load_from_database(self, db_session):
        """从数据库加载已有知识图谱"""
        try:
            from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine

            kg_service = UnifiedKnowledgeGraphEngine(db_session)

            # 加载实体
            db_entities = kg_service.get_all_entities()
            for db_entity in db_entities:
                entity = Entity(
                    实体ID=db_entity.entity_id,
                    实体名称=db_entity.entity_name,
                    实体类型=db_entity.entity_type,
                    提及次数=db_entity.mention_count,
                    出现文档=db_entity.documents or [],
                    上下文片段=db_entity.contexts or [],
                    关联实体=db_entity.related_entities or [],
                    首次出现时间戳=db_entity.first_timestamp
                )
                self.entities[entity.实体名称] = entity

            # 加载关系
            db_relations = kg_service.get_all_relations()
            for db_rel in db_relations:
                relation = Relation(
                    关系ID=db_rel.relation_id,
                    主体=db_rel.subject_entity.entity_name if db_rel.subject_entity else "",
                    关系类型=db_rel.relation_type,
                    客体=db_rel.object_entity.entity_name if db_rel.object_entity else "",
                    上下文=db_rel.context,
                    时间戳=db_rel.timestamp,
                    来源文档=db_rel.source_document,
                    置信度=db_rel.confidence
                )
                self.relations.append(relation)

            # 加载共现
            db_co_occurrences = kg_service.get_all_co_occurrences()
            for db_co in db_co_occurrences:
                co_occurrence = CoOccurrence(
                    共现实体组=db_co.entities,
                    共现频次=db_co.frequency,
                    窗口类型=db_co.window_type
                )
                self.co_occurrences.append(co_occurrence)

            logger.info(f"   ✅ 从数据库加载: {len(self.entities)}个实体, {len(self.relations)}个关系")

        except Exception as e:
            logger.error(f"   ❌ 从数据库加载失败: {e}")

    async def _persist_to_database(self, db_session, doc_id: str):
        """持久化到数据库"""
        try:
            from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine

            kg_service = UnifiedKnowledgeGraphEngine(db_session)

            # 1. 保存实体
            logger.info(f"   💾 保存 {len(self.entities)} 个实体...")
            for entity in self.entities.values():
                entity_data = {
                    "entity_id": entity.实体ID,
                    "entity_name": entity.实体名称,
                    "entity_type": entity.实体类型,
                    "mention_count": entity.提及次数,
                    "documents": entity.出现文档,
                    "contexts": entity.上下文片段,
                    "related_entities": entity.关联实体,
                    "first_timestamp": entity.首次出现时间戳
                }
                kg_service.save_entity(entity_data)

            # 2. 保存关系
            logger.info(f"   💾 保存 {len(self.relations)} 个关系...")
            for relation in self.relations:
                relation_data = {
                    "relation_id": relation.关系ID,
                    "subject": relation.主体,
                    "relation_type": relation.关系类型,
                    "object": relation.客体,
                    "context": relation.上下文,
                    "timestamp": relation.时间戳,
                    "source_document": relation.来源文档,
                    "confidence": relation.置信度
                }
                kg_service.save_relation(relation_data)

            # 3. 保存共现
            logger.info(f"   💾 保存 {len(self.co_occurrences)} 个共现...")
            for co_occurrence in self.co_occurrences:
                co_data = {
                    "entities": co_occurrence.共现实体组,
                    "frequency": co_occurrence.共现频次,
                    "window_type": co_occurrence.窗口类型
                }
                kg_service.save_co_occurrence(co_data)

            # 4. 保存知识图谱元数据
            graph_metadata = {
                "graph_id": "main_graph",
                "name": "田野调研知识图谱",
                "description": f"基于文档 {doc_id} 的知识图谱",
                "entity_count": len(self.entities),
                "relation_count": len(self.relations),
                "document_count": len(set([e.出现文档 for e in self.entities.values() if e.出现文档])),
                "statistics": {
                    "core_nodes": self._get_core_nodes(top_n=10),
                    "communities": len(self._detect_communities() if self.graph else [])
                }
            }
            kg_service.save_knowledge_graph_metadata(graph_metadata)

            # 5. 提交事务
            kg_service.commit()
            logger.info("   ✅ 数据库持久化完成")

        except Exception as e:
            logger.error(f"   ❌ 数据库持久化失败: {e}")
            if db_session:
                db_session.rollback()

    def _extract_timestamps_for_entity(
        self,
        entity_name: str,
        segments: List[Dict]
    ) -> Tuple[float, List[float]]:
        """
        从 segments 中提取实体的精确时间戳

        Args:
            entity_name: 实体名称
            segments: 片段列表，格式 [{"text": "...", "start": 12.5, "end": 15.3}, ...]

        Returns:
            (首次出现时间戳, [所有出现时间戳列表])
        """
        timestamps = []

        for segment in segments:
            segment_text = segment.get('text', '')
            if entity_name in segment_text:
                start_time = segment.get('start', 0.0)
                timestamps.append(start_time)

        if not timestamps:
            return 0.0, []

        first_timestamp = min(timestamps)
        return first_timestamp, timestamps

    def _extract_timestamp_for_relation(
        self,
        relation_context: str,
        segments: List[Dict]
    ) -> float:
        """
        为关系提取时间戳（根据上下文匹配到 segment）

        Args:
            relation_context: 关系的上下文文本
            segments: 片段列表

        Returns:
            时间戳（匹配到的第一个 segment 的 start）
        """
        # 取上下文的前20个字符作为匹配键
        context_key = relation_context[:20]

        for segment in segments:
            segment_text = segment.get('text', '')
            if context_key in segment_text:
                return segment.get('start', 0.0)

        return 0.0

    def _extract_entities(
        self,
        text: str,
        segments: List[Dict],
        existing_entities: List[Dict],
        doc_id: str
    ) -> List[Entity]:
        """
        提取实体

        策略：
        1. 复用 TranscriptAgent 的核心人物
        2. 使用 DynamicDiscoveryEngine 补充通用实体
        3. 规则匹配细粒度地名、文化概念
        """
        entities = []
        entity_id_counter = 0

        # 1. 复用已有人物实体
        for person in existing_entities:
            entity_id_counter += 1
            entity_name = person.get('name', '')

            # 提取时间戳
            first_timestamp, all_timestamps = self._extract_timestamps_for_entity(entity_name, segments)

            entities.append(Entity(
                实体ID=f"entity_{entity_id_counter:04d}",
                实体名称=entity_name,
                实体类型="人物",
                提及次数=person.get('mentions', 0),
                出现文档=[doc_id],
                上下文片段=person.get('contexts', [])[:3],
                关联实体=[],
                首次出现时间戳=first_timestamp
            ))

        logger.info(f"   ✅ 复用已有人物: {len(existing_entities)} 个")

        # 2. 使用 DynamicDiscoveryEngine 补充
        try:
            discovery_result = self.discovery_engine.discover_entities(
                texts=[text],
                enable_ner=False,  # 轻量模式
                enable_topic=False
            )

            discovered = discovery_result.get('entities', [])
            for ent in discovered:
                entity_id_counter += 1
                entity_name = ent['name']
                first_timestamp, _ = self._extract_timestamps_for_entity(entity_name, segments)

                entities.append(Entity(
                    实体ID=f"entity_{entity_id_counter:04d}",
                    实体名称=entity_name,
                    实体类型="通用实体",  # 后续分类
                    提及次数=ent.get('count', 1),
                    出现文档=[doc_id],
                    上下文片段=[ent.get('context', '')],
                    关联实体=[],
                    首次出现时间戳=first_timestamp
                ))

            logger.info(f"   ✅ DynamicDiscovery 补充: {len(discovered)} 个")
        except Exception as e:
            logger.warning(f"   ⚠️ DynamicDiscovery 失败: {e}")

        # 3. 规则匹配：细粒度地名
        for landmark in self.LANDMARK_KEYWORDS:
            if landmark in text:
                count = text.count(landmark)
                entity_id_counter += 1
                first_timestamp, _ = self._extract_timestamps_for_entity(landmark, segments)

                entities.append(Entity(
                    实体ID=f"entity_{entity_id_counter:04d}",
                    实体名称=landmark,
                    实体类型="地名-地标",
                    提及次数=count,
                    出现文档=[doc_id],
                    上下文片段=self._extract_contexts(text, landmark, max_contexts=3),
                    关联实体=[],
                    首次出现时间戳=first_timestamp
                ))

        # 4. 规则匹配：文化概念
        for concept in self.CULTURE_TRADITIONAL:
            if concept in text:
                count = text.count(concept)
                entity_id_counter += 1
                first_timestamp, _ = self._extract_timestamps_for_entity(concept, segments)

                entities.append(Entity(
                    实体ID=f"entity_{entity_id_counter:04d}",
                    实体名称=concept,
                    实体类型="文化概念-传统",
                    提及次数=count,
                    出现文档=[doc_id],
                    上下文片段=self._extract_contexts(text, concept, max_contexts=3),
                    关联实体=[],
                    首次出现时间戳=first_timestamp
                ))

        for concept in self.CULTURE_RITUAL:
            if concept in text:
                count = text.count(concept)
                entity_id_counter += 1
                entities.append(Entity(
                    实体ID=f"entity_{entity_id_counter:04d}",
                    实体名称=concept,
                    实体类型="文化概念-传统",
                    提及次数=count,
                    出现文档=[doc_id],
                    上下文片段=self._extract_contexts(text, concept, max_contexts=3),
                    关联实体=[]
                ))

        for concept in self.CULTURE_RITUAL:
            if concept in text:
                count = text.count(concept)
                entity_id_counter += 1
                first_timestamp, _ = self._extract_timestamps_for_entity(concept, segments)

                entities.append(Entity(
                    实体ID=f"entity_{entity_id_counter:04d}",
                    实体名称=concept,
                    实体类型="文化概念-仪式",
                    提及次数=count,
                    出现文档=[doc_id],
                    上下文片段=self._extract_contexts(text, concept, max_contexts=3),
                    关联实体=[],
                    首次出现时间戳=first_timestamp
                ))

        logger.info(f"   ✅ 规则匹配: 地名+文化概念")

        return entities

    def _extract_contexts(self, text: str, keyword: str, max_contexts: int = 3) -> List[str]:
        """提取关键词的上下文片段"""
        contexts = []
        sentences = re.split(r'[。！？\n]', text)

        for sent in sentences:
            if keyword in sent and sent.strip():
                contexts.append(sent.strip()[:80])
                if len(contexts) >= max_contexts:
                    break

        return contexts

    def _extract_relations(
        self,
        text: str,
        segments: List[Dict],
        entities: List[Entity],
        doc_id: str,
        enable_llm: bool
    ) -> List[Relation]:
        """
        提取关系

        方法：
        1. 基于实体共现的关系推断
        2. 规则模板匹配（优化：只在包含实体的句子中匹配）
        3. LLM 辅助（复杂关系）
        """
        relations = []
        relation_id_counter = 0

        sentences = re.split(r'[。！？\n]', text)
        entity_names = {e.实体名称 for e in entities}

        # 方法1: 基于共现的关系推断（简单版本）
        # 如果两个实体在同一句话中出现，可能存在关系
        for sent in sentences:
            if not sent.strip():
                continue

            # 找出这句话中的实体
            entities_in_sent = [name for name in entity_names if name in sent]

            if len(entities_in_sent) >= 2:
                # 推断可能的关系
                # 简单规则：检查是否有动词连接
                for i, subj in enumerate(entities_in_sent):
                    for obj in entities_in_sent[i+1:]:
                        # 检查中间是否有关系词
                        # 提取主体和客体之间的文本
                        subj_idx = sent.find(subj)
                        obj_idx = sent.find(obj)

                        if subj_idx < obj_idx:
                            between = sent[subj_idx+len(subj):obj_idx]
                        else:
                            between = sent[obj_idx+len(obj):subj_idx]

                        # 检查关系关键词
                        rel_type = None
                        if any(word in between for word in ['教', '培训', '传授', '指导']):
                            rel_type = "教授"
                        elif any(word in between for word in ['参加', '参与']):
                            rel_type = "参与"
                        elif any(word in between for word in ['在', '于', '位于']):
                            rel_type = "位于"
                        elif any(word in between for word in ['和', '与', '跟']):
                            rel_type = "关联"

                        if rel_type:
                            relation_id_counter += 1
                            # 提取时间戳
                            timestamp = self._extract_timestamp_for_relation(sent[:100], segments)

                            # 创建关系对象
                            relation = Relation(
                                关系ID=f"rel_{relation_id_counter:04d}",
                                主体=subj if subj_idx < obj_idx else obj,
                                关系类型=rel_type,
                                客体=obj if subj_idx < obj_idx else subj,
                                上下文=sent[:100],
                                时间戳=timestamp,
                                来源文档=doc_id,
                                置信度=0.8  # 临时值，稍后计算
                            )

                            # 计算智能置信度
                            relation.置信度 = self._calculate_relation_confidence(
                                relation, entities, extraction_method="cooccur"
                            )
                            relations.append(relation)

        logger.info(f"   ✅ 基于共现推断: {len(relations)} 个关系")

        # 方法2: 规则模板匹配（只在包含实体的句子中）
        original_count = len(relations)
        for sent in sentences:
            if not sent.strip():
                continue

            # 只处理包含至少一个实体的句子
            entities_in_sent = [name for name in entity_names if name in sent]
            if not entities_in_sent:
                continue

            for relation_category, patterns in self.RELATION_PATTERNS.items():
                for pattern, rel_type in patterns:
                    matches = re.findall(pattern, sent)
                    if matches:
                        for match in matches:
                            relation_id_counter += 1

                            # 提取主体和客体
                            if len(match) >= 2:
                                subject = match[0]
                                obj = match[-1] if len(match) > 2 else match[1]

                                # 只保留主体或客体至少有一个是已知实体的关系
                                if subject in entity_names or obj in entity_names:
                                    # 提取时间戳
                                    timestamp = self._extract_timestamp_for_relation(sent[:100], segments)

                                    # 创建关系对象
                                    relation = Relation(
                                        关系ID=f"rel_{relation_id_counter:04d}",
                                        主体=subject,
                                        关系类型=rel_type,
                                        客体=obj,
                                        上下文=sent[:100],
                                        时间戳=timestamp,
                                        来源文档=doc_id,
                                        置信度=0.7  # 临时值
                                    )

                                    # 计算智能置信度
                                    relation.置信度 = self._calculate_relation_confidence(
                                        relation, entities, extraction_method="rule"
                                    )
                                    relations.append(relation)

        logger.info(f"   ✅ 规则模板补充: {len(relations) - original_count} 个关系")

        # 过滤：优先保留两端都是实体的关系
        high_quality_relations = [r for r in relations if r.主体 in entity_names and r.客体 in entity_names]
        medium_quality_relations = [r for r in relations if r not in high_quality_relations]

        logger.info(f"   ✅ 高质量关系（两端都是实体）: {len(high_quality_relations)} 个")
        logger.info(f"   ✅ 中质量关系（至少一端是实体）: {len(medium_quality_relations)} 个")

        # 优先返回高质量关系，如果没有则返回中质量关系
        final_relations = high_quality_relations if high_quality_relations else medium_quality_relations[:20]

        # 方法3: LLM 辅助提取（复杂关系）
        if enable_llm:
            llm_relations = self._extract_relations_with_llm(text, entities, doc_id)
            logger.info(f"   ✅ LLM 辅助提取: {len(llm_relations)} 个关系")

            # 合并 LLM 提取的关系
            for llm_rel in llm_relations:
                relation_id_counter += 1
                llm_rel.关系ID = f"rel_{relation_id_counter:04d}"
                final_relations.append(llm_rel)

        return final_relations

    def _extract_relations_with_llm(
        self,
        text: str,
        entities: List[Entity],
        doc_id: str
    ) -> List[Relation]:
        """
        使用 LLM 提取复杂关系

        策略：
        1. 只发送包含多个实体的句子（节省 token）
        2. 提供实体列表和关系类型作为上下文
        3. 要求 LLM 返回结构化 JSON
        """
        if not openai:
            logger.warning("   ⚠️ openai 未安装，跳过 LLM 辅助提取")
            return []

        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("   ⚠️ OPENAI_API_KEY 未设置，跳过 LLM 辅助提取")
            return []

        try:
            # 1. 筛选包含多个实体的句子
            sentences = re.split(r'[。！？\n]', text)
            entity_names = {e.实体名称 for e in entities}

            candidate_sentences = []
            for sent in sentences:
                if not sent.strip():
                    continue
                entities_in_sent = [name for name in entity_names if name in sent]
                if len(entities_in_sent) >= 2:
                    candidate_sentences.append({
                        "text": sent.strip(),
                        "entities": entities_in_sent
                    })

            if not candidate_sentences:
                logger.info("   ⏭️ 没有包含多个实体的句子，跳过 LLM 提取")
                return []

            # 限制句子数量（避免 token 过多）
            candidate_sentences = candidate_sentences[:20]

            # 2. 构建 prompt
            entity_list = "\n".join([f"- {e.实体名称} ({e.实体类型})" for e in entities[:30]])

            sentences_text = "\n".join([
                f"{i+1}. {s['text']} [实体: {', '.join(s['entities'])}]"
                for i, s in enumerate(candidate_sentences)
            ])

            prompt = f"""你是一个田野调研知识图谱构建专家。请从以下句子中提取实体间的关系。

已识别实体：
{entity_list}

待分析句子：
{sentences_text}

关系类型：
- 亲缘（家庭关系：父子、母女、夫妻等）
- 师徒（教学关系：老师教学生、师傅带徒弟）
- 教授（谁教授谁某项技能或知识）
- 参与（谁参与了什么活动或事件）
- 位于（地点关系：某人/事物位于某地）
- 关联（其他关联关系）

要求：
1. 只提取句子中明确表达的关系
2. 主体和客体必须是已识别的实体
3. 返回 JSON 数组格式：
[
  {{
    "主体": "实体名称",
    "关系类型": "关系类型",
    "客体": "实体名称",
    "上下文": "原句",
    "置信度": 0.9
  }}
]

如果没有关系，返回空数组 []。"""

            # 3. 调用 LLM
            openai.api_key = os.getenv("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "你是知识图谱构建助手，专注于从田野调研文本中提取实体关系。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # 4. 解析结果
            result_text = response.choices[0].message.content.strip()

            # 尝试提取 JSON（可能包含在 markdown 代码块中）
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            relations_data = json.loads(result_text)

            # 5. 转换为 Relation 对象
            llm_relations = []
            for rel_data in relations_data:
                # 验证主体和客体是否在实体列表中
                if rel_data["主体"] not in entity_names or rel_data["客体"] not in entity_names:
                    continue

                # 创建关系对象
                relation = Relation(
                    关系ID="",  # 稍后分配
                    主体=rel_data["主体"],
                    关系类型=rel_data["关系类型"],
                    客体=rel_data["客体"],
                    上下文=rel_data["上下文"][:100],
                    时间戳=0.0,
                    来源文档=doc_id,
                    置信度=rel_data.get("置信度", 0.9)  # 临时值
                )

                # 计算智能置信度（LLM 提取有基础高分）
                relation.置信度 = self._calculate_relation_confidence(
                    relation, entities, extraction_method="llm"
                )

                llm_relations.append(relation)

            return llm_relations

        except Exception as e:
            logger.error(f"   ❌ LLM 辅助提取失败: {e}")
            return []

    def _calculate_relation_confidence(
        self,
        relation: Relation,
        entities: List[Entity],
        extraction_method: str = "rule"
    ) -> float:
        """
        计算关系置信度

        考虑因素：
        1. 上下文质量（长度、完整性、信息密度）
        2. 实体重要性（提及次数、类型）
        3. 关系类型（不同类型可靠性不同）
        4. 提取方式（LLM > 规则）

        分数范围: 0.0 - 1.0
        """
        import math

        confidence = 0.3  # 基础分（降低以留出空间）

        # === 1. 上下文质量评分 (0-0.2) ===
        context = relation.上下文
        context_length = len(context)

        # 长度评分：20-100字为最佳
        if 20 <= context_length <= 100:
            length_score = 0.12
        elif context_length < 20:
            length_score = context_length / 20 * 0.12
        else:
            # 超过100字后逐渐降低
            length_score = 0.12 * (1 - min((context_length - 100) / 200, 0.7))

        # 完整性评分：包含标点、没有截断
        completeness_score = 0.04
        if context.endswith(('...', '…')):
            completeness_score = 0.01
        elif any(context.endswith(p) for p in ['。', '！', '？', '，', '；']):
            completeness_score = 0.04

        # 信息密度：关键词数量
        keywords = ['说', '在', '的', '是', '有', '和', '与', '给', '对', '为']
        keyword_count = sum(1 for kw in keywords if kw in context)
        density_score = min(keyword_count * 0.008, 0.04)

        context_quality = length_score + completeness_score + density_score

        # === 2. 实体重要性评分 (0-0.2) ===
        entity_map = {e.实体名称: e for e in entities}
        subject_entity = entity_map.get(relation.主体)
        object_entity = entity_map.get(relation.客体)

        importance_score = 0.0

        if subject_entity:
            # 提及次数越多越重要（对数缩放）
            subject_importance = min(math.log(subject_entity.提及次数 + 1) / 5, 0.08)
            # 人物实体更重要
            if subject_entity.实体类型 == "人物":
                subject_importance += 0.02
            importance_score += subject_importance

        if object_entity:
            object_importance = min(math.log(object_entity.提及次数 + 1) / 5, 0.08)
            if object_entity.实体类型 == "人物":
                object_importance += 0.02
            importance_score += object_importance

        # === 3. 关系类型可靠性 (0-0.15) ===
        relation_type_scores = {
            "亲缘": 0.15,      # 最可靠
            "师徒": 0.13,
            "教授": 0.12,
            "参与": 0.10,
            "位于": 0.11,
            "从属": 0.10,
            "行为": 0.08,
            "关联": 0.06      # 最模糊
        }
        type_score = relation_type_scores.get(relation.关系类型, 0.06)

        # === 4. 提取方式评分 (0-0.2) ===
        method_scores = {
            "llm": 0.20,      # LLM 提取最可靠
            "rule": 0.12,     # 规则模板次之
            "cooccur": 0.08   # 共现推断最弱
        }
        method_score = method_scores.get(extraction_method, 0.08)

        # === 5. 两端都是已知实体加分 (0-0.15) ===
        both_known_score = 0.15 if (subject_entity and object_entity) else 0.0

        # 总分
        final_confidence = (
            confidence +
            context_quality +
            importance_score +
            type_score +
            method_score +
            both_known_score
        )

        # 归一化到 [0, 1]
        return min(max(final_confidence, 0.0), 1.0)

    def _analyze_co_occurrence(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[CoOccurrence]:
        """
        共现分析（句子级窗口）
        """
        co_occurrences = []
        sentences = re.split(r'[。！？\n]', text)

        # 构建实体名称集合
        entity_names = {e.实体名称 for e in entities}

        # 统计共现
        co_occur_counter = Counter()

        for sent in sentences:
            if not sent.strip():
                continue

            # 找出这句话中出现的实体
            entities_in_sent = [name for name in entity_names if name in sent]

            if len(entities_in_sent) >= 2:
                # 排序后生成元组（避免重复）
                entities_tuple = tuple(sorted(entities_in_sent))
                co_occur_counter[entities_tuple] += 1

        # 转换为 CoOccurrence 对象
        for entities_tuple, freq in co_occur_counter.most_common(50):
            co_occurrences.append(CoOccurrence(
                共现实体组=list(entities_tuple),
                共现频次=freq,
                窗口类型="句子级"
            ))

        logger.info(f"   ✅ 共现分析完成: {len(co_occurrences)} 组")

        return co_occurrences

    def _disambiguate_entities(
        self,
        entities: List[Entity],
        similarity_threshold: float = 0.85
    ) -> Dict[str, str]:
        """
        实体消歧：使用向量相似度识别同义实体

        Args:
            entities: 实体列表
            similarity_threshold: 相似度阈值（0-1）

        Returns:
            映射字典 {原实体名: 标准实体名}

        示例：
            {"鐘老师": "鐘百拜", "钟老师": "鐘百拜"}
        """
        if not self.embedder:
            logger.warning("   ⚠️ 向量模型未初始化，跳过实体消歧")
            return {}

        entity_map = {}
        entity_names = [e.实体名称 for e in entities]

        try:
            # 生成向量
            embeddings = self.embedder.encode(entity_names)

            # 计算相似度矩阵
            from sklearn.metrics.pairwise import cosine_similarity
            similarity_matrix = cosine_similarity(embeddings)

            # 找出相似实体对
            for i in range(len(entity_names)):
                for j in range(i + 1, len(entity_names)):
                    similarity = similarity_matrix[i][j]

                    if similarity >= similarity_threshold:
                        name_i = entity_names[i]
                        name_j = entity_names[j]

                        # 选择提及次数多的作为标准名
                        entity_i = entities[i]
                        entity_j = entities[j]

                        if entity_i.提及次数 >= entity_j.提及次数:
                            standard_name = name_i
                            alias_name = name_j
                        else:
                            standard_name = name_j
                            alias_name = name_i

                        entity_map[alias_name] = standard_name
                        logger.info(f"   🔗 发现同义实体: {alias_name} -> {standard_name} (相似度: {similarity:.2f})")

            return entity_map

        except Exception as e:
            logger.error(f"   ❌ 实体消歧失败: {e}")
            return {}

    def _apply_entity_mapping(
        self,
        entities: List[Entity],
        entity_map: Dict[str, str]
    ) -> List[Entity]:
        """
        应用实体映射（合并同义实体）

        Args:
            entities: 原实体列表
            entity_map: 映射字典 {别名: 标准名}

        Returns:
            合并后的实体列表
        """
        merged_entities = {}

        for entity in entities:
            # 获取标准名称
            standard_name = entity_map.get(entity.实体名称, entity.实体名称)

            if standard_name in merged_entities:
                # 已存在，合并
                existing = merged_entities[standard_name]
                existing.提及次数 += entity.提及次数
                existing.出现文档 = list(set(existing.出现文档 + entity.出现文档))
                existing.上下文片段 = (existing.上下文片段 + entity.上下文片段)[:10]
                existing.关联实体 = list(set(existing.关联实体 + entity.关联实体))
            else:
                # 新实体，使用标准名
                entity.实体名称 = standard_name
                merged_entities[standard_name] = entity

        return list(merged_entities.values())

    def _merge_into_knowledge_graph(
        self,
        new_entities: List[Entity],
        new_relations: List[Relation],
        new_co_occurrences: List[CoOccurrence],
        doc_id: str
    ):
        """
        实时合并到知识图谱

        策略：
        - 实体：同名合并，累加提及次数
        - 关系：去重后添加
        - 共现：累加频次
        """
        # 合并实体
        for entity in new_entities:
            name = entity.实体名称

            if name in self.entities:
                # 已存在，更新
                existing = self.entities[name]
                existing.提及次数 += entity.提及次数
                existing.出现文档.append(doc_id)
                existing.出现文档 = list(set(existing.出现文档))  # 去重
                existing.上下文片段.extend(entity.上下文片段)
                existing.上下文片段 = existing.上下文片段[:10]  # 保留前10个
            else:
                # 新实体
                self.entities[name] = entity

        # 合并关系
        self.relations.extend(new_relations)

        # 合并共现
        self.co_occurrences.extend(new_co_occurrences)

        logger.info(f"   ✅ 合并完成: 当前知识图谱有 {len(self.entities)} 个实体")

    def _build_graph(self) -> Dict[str, Any]:
        """
        构建知识图谱并生成多格式输出
        """
        if self.graph is None:
            logger.warning("   ⚠️ NetworkX 未安装，跳过图构建")
            return {"d3": {}, "mindmap": {}}

        # 清空图
        self.graph.clear()

        # 添加节点
        for name, entity in self.entities.items():
            self.graph.add_node(
                name,
                type=entity.实体类型,
                mentions=entity.提及次数,
                docs=entity.出现文档
            )

        # 添加边
        for rel in self.relations:
            if rel.主体 in self.graph and rel.客体 in self.graph:
                self.graph.add_edge(
                    rel.主体,
                    rel.客体,
                    relation=rel.关系类型,
                    context=rel.上下文,
                    confidence=rel.置信度
                )

        # 生成 D3.js 格式
        d3_data = self._to_d3_format()

        # 生成思维导图格式
        mindmap_data = self._to_mindmap_format()

        return {
            "d3": d3_data,
            "mindmap": mindmap_data
        }

    def _to_d3_format(self) -> Dict[str, Any]:
        """转换为 D3.js 力导向图格式"""
        nodes = []
        links = []

        # 类型到组的映射
        type_to_group = {
            "人物": 1,
            "地名-行政": 2,
            "地名-地标": 3,
            "文化概念-传统": 4,
            "文化概念-仪式": 5,
            "机构": 6,
            "通用实体": 7
        }

        # 构建节点
        for name, entity in self.entities.items():
            nodes.append({
                "id": name,
                "type": entity.实体类型,
                "mentions": entity.提及次数,
                "group": type_to_group.get(entity.实体类型, 7)
            })

        # 构建边
        for rel in self.relations:
            links.append({
                "source": rel.主体,
                "target": rel.客体,
                "type": rel.关系类型,
                "weight": rel.置信度
            })

        return {"nodes": nodes, "links": links}

    def _to_mindmap_format(self) -> Dict[str, Any]:
        """
        转换为思维导图格式

        策略：选择提及次数最多的实体作为根节点
        """
        if not self.entities:
            return {}

        # 找到核心节点（提及次数最多）
        core_entity = max(self.entities.values(), key=lambda e: e.提及次数)

        # 构建子节点
        children = []

        # 按关系类型分组
        relation_groups = defaultdict(list)
        for rel in self.relations:
            if rel.主体 == core_entity.实体名称:
                relation_groups[rel.关系类型].append(rel.客体)
            elif rel.客体 == core_entity.实体名称:
                relation_groups[rel.关系类型].append(rel.主体)

        # 构建分支
        for rel_type, entities in relation_groups.items():
            branch_children = [{"data": {"text": e}} for e in entities[:5]]
            children.append({
                "data": {"text": rel_type},
                "children": branch_children
            })

        return {
            "root": {
                "data": {
                    "text": core_entity.实体名称,
                    "type": core_entity.实体类型
                },
                "children": children
            }
        }

    def _get_core_nodes(self, top_n: int = 10) -> List[str]:
        """获取核心节点（按提及次数排序）"""
        sorted_entities = sorted(
            self.entities.values(),
            key=lambda e: e.提及次数,
            reverse=True
        )
        return [e.实体名称 for e in sorted_entities[:top_n]]

    def _detect_communities(self) -> List[Dict[str, Any]]:
        """社区检测（主题聚类）"""
        if not self.graph or len(self.graph.nodes()) < 3:
            return []

        try:
            # 使用 Louvain 算法
            from networkx.algorithms import community
            communities = community.greedy_modularity_communities(self.graph.to_undirected())

            result = []
            for i, comm in enumerate(communities):
                community_members = list(comm)[:10]

                # 用 LLM 生成主题名称
                topic_name = self._generate_community_topic(community_members, i+1)

                result.append({
                    "社区ID": f"community_{i+1}",
                    "主题": topic_name,
                    "成员实体": community_members
                })

            return result
        except Exception as e:
            logger.warning(f"   ⚠️ 社区检测失败: {e}")
            return []

    def _generate_community_topic(self, community_members: List[str], community_id: int) -> str:
        """
        用 LLM 为社区生成主题名称

        策略：
        1. 收集社区成员的实体信息（类型、上下文）
        2. 收集社区内的关系信息
        3. 请求 LLM 生成简洁的主题名（3-8字）
        """
        if not openai or not os.getenv("OPENAI_API_KEY"):
            return f"社区{community_id}"

        try:
            # 1. 收集社区成员信息
            member_info = []
            for member_name in community_members[:8]:  # 最多8个成员
                entity = self.entities.get(member_name)
                if entity:
                    # 取前2个上下文片段
                    contexts = entity.上下文片段[:2] if entity.上下文片段 else []
                    member_info.append({
                        "名称": entity.实体名称,
                        "类型": entity.实体类型,
                        "提及次数": entity.提及次数,
                        "上下文": contexts
                    })

            if not member_info:
                return f"社区{community_id}"

            # 2. 收集社区内的关系
            community_relations = []
            member_set = set(community_members)
            for relation in self.relations:
                if relation.主体 in member_set and relation.客体 in member_set:
                    community_relations.append({
                        "主体": relation.主体,
                        "关系": relation.关系类型,
                        "客体": relation.客体
                    })

            # 限制关系数量
            community_relations = community_relations[:10]

            # 3. 构建 prompt
            members_text = "\n".join([
                f"- {m['名称']} ({m['类型']}, 提及{m['提及次数']}次)"
                for m in member_info
            ])

            relations_text = "\n".join([
                f"- {r['主体']} {r['关系']} {r['客体']}"
                for r in community_relations[:5]
            ]) if community_relations else "（无明确关系）"

            prompt = f"""这是一个田野调研知识图谱中的社区（聚类），包含以下成员和关系：

成员实体：
{members_text}

关系：
{relations_text}

请为这个社区生成一个简洁的主题名称（3-8个汉字），反映社区的核心内容或主题。

要求：
1. 只返回主题名称，不要其他说明
2. 优先使用实体类型和关系类型概括
3. 示例：「鐘家族谱」「手工艺传承」「地方机构」「田野访谈」

主题名称："""

            # 4. 调用 LLM
            openai.api_key = os.getenv("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "你是知识图谱分析助手，擅长为实体社区生成简洁的主题名称。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )

            # 5. 解析结果
            topic_name = response.choices[0].message.content.strip()

            # 清理格式（去除引号、冒号等）
            topic_name = topic_name.replace('"', '').replace("'", '').replace('「', '').replace('」', '')
            topic_name = topic_name.replace('：', '').replace(':', '')
            topic_name = topic_name.strip()

            # 长度限制
            if len(topic_name) > 12:
                topic_name = topic_name[:12]

            # 验证是否为空或无效
            if not topic_name or len(topic_name) < 2:
                topic_name = f"社区{community_id}"

            logger.info(f"   🏷️ 社区{community_id}主题: {topic_name}")
            return topic_name

        except Exception as e:
            logger.warning(f"   ⚠️ 为社区{community_id}生成主题失败: {e}")
            return f"社区{community_id}"
