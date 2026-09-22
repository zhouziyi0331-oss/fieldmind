"""
数据驱动报告构建器 - 核心引擎

职责：
1. 从已处理数据中提取报告素材
2. 动态生成报告大纲
3. 协调各层报告生成
4. 确保所有内容可追溯到原文（反幻觉）
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text

logger = logging.getLogger(__name__)


class ReportMaterial:
    """报告素材数据类"""
    def __init__(self, use_workflow_engine: bool = True):

        # 基础统计
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.project_id: int = 0
        self.total_documents: int = 0
        self.total_chunks: int = 0
        self.total_words: int = 0

        # 关键词网络数据
        self.main_keywords: List[Dict] = []  # PageRank识别的主关键词
        self.keyword_communities: List[Dict] = []  # Louvain社区检测结果
        self.keyword_relations: List[Dict] = []  # 关键词共现关系

        # 实体网络数据
        self.core_entities: Dict[str, List[Dict]] = {
            'PERSON': [],
            'LOCATION': [],
            'EVENT': [],
            'ORGANIZATION': [],
            'THEME': []
        }
        self.entity_relations: List[Dict] = []  # 实体关系网络

        # 时间线数据（编年史）
        self.timeline: List[Dict] = []  # 按时间排序的事件
        self.temporal_span: Dict = {}  # 时间跨度统计

        # 报告关系网络
        self.related_reports: List[Dict] = []  # 相关报告

        # 原文引用池（反幻觉关键）
        self.citation_pool: List[Dict] = []  # 所有可引用的原文片段

        # 数据画像
        self.data_profile: Dict = {}  # 动态发现的维度


class DataDrivenReportBuilder:
    """
    数据驱动报告构建器

    核心原则：
    1. 先跑数据，后生成大纲
    2. 每个观点必须有原文引用
    3. 利用已有的网络分析结果
    4. 动态章节，不预设维度
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_report_material(self, project_id: int) -> ReportMaterial:
        """
        提取报告所需的所有素材

        这是报告生成的第一步：收集所有已处理的数据
        """
        logger.info(f"📊 开始提取项目 {project_id} 的报告素材...")

        material = ReportMaterial()
        material.project_id = project_id

        # 1. 基础统计
        material.total_documents = self._count_documents(project_id)
        material.total_chunks = self._count_chunks(project_id)
        material.total_words = self._count_total_words(project_id)

        # 2. 关键词网络数据
        material.main_keywords = self._extract_main_keywords(project_id)
        material.keyword_communities = self._extract_keyword_communities(project_id)
        material.keyword_relations = self._extract_keyword_relations(project_id)

        # 3. 实体网络数据
        material.core_entities = self._extract_core_entities(project_id)
        material.entity_relations = self._extract_entity_relations(project_id)

        # 4. 时间线数据
        material.timeline = self._extract_timeline(project_id)
        material.temporal_span = self._calculate_temporal_span(material.timeline)

        # 5. 相关报告
        material.related_reports = self._extract_related_reports(project_id)

        # 6. 原文引用池（最重要！反幻觉的基础）
        material.citation_pool = self._build_citation_pool(project_id)

        # 7. 数据画像
        material.data_profile = self._extract_data_profile(project_id)

        logger.info(f"✅ 素材提取完成：{material.total_documents}文档, "
                   f"{len(material.main_keywords)}主关键词, "
                   f"{sum(len(v) for v in material.core_entities.values())}实体, "
                   f"{len(material.citation_pool)}引用片段")

        return material

    def _count_documents(self, project_id: int) -> int:
        """统计文档数量"""
        from app.models.document import Document
        return self.db.query(func.count(Document.id))\
            .filter(Document.project_id == project_id)\
            .scalar() or 0

    def _count_chunks(self, project_id: int) -> int:
        """统计chunks数量"""
        # 直接查询document_chunks表，该表有project_id字段
        result = self.db.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE project_id = :pid"),
            {"pid": project_id}
        ).scalar()
        return result or 0

    def _count_total_words(self, project_id: int) -> int:
        """统计总字数"""
        # 使用text字段的长度估算（中文按字符数）
        result = self.db.execute(
            text("SELECT SUM(text_length) FROM document_chunks WHERE project_id = :pid"),
            {"pid": project_id}
        ).scalar()
        return int(result) if result else 0

    def _extract_main_keywords(self, project_id: int) -> List[Dict]:
        """
        提取主关键词（基于importance权重）

        从keywords表中提取importance最高的关键词
        """
        result = self.db.execute(
            text("""
                SELECT id, text, frequency, importance, weight
                FROM keywords
                WHERE project_id = :pid
                ORDER BY importance DESC
                LIMIT 20
            """),
            {"pid": project_id}
        ).fetchall()

        return [
            {
                'keyword_id': row[0],
                'keyword': row[1],
                'pagerank': float(row[3]) if row[3] else 0.0,  # 使用importance作为pagerank
                'degree': float(row[4]) if row[4] else 0.0,  # 使用weight作为degree
                'frequency': row[2] or 0,
                'is_main': True
            }
            for row in result
        ]

    def _extract_keyword_communities(self, project_id: int) -> List[Dict]:
        """
        提取关键词社区（基于category分组）

        由于数据库中没有Louvain社区检测结果，我们使用keywords表的category字段进行分组
        """
        result = self.db.execute(
            text("""
                SELECT category, text, importance
                FROM keywords
                WHERE project_id = :pid AND category IS NOT NULL
                ORDER BY category, importance DESC
            """),
            {"pid": project_id}
        ).fetchall()

        # 按category分组
        communities = {}
        for row in result:
            category = row[0] or "其他"
            if category not in communities:
                communities[category] = []

            communities[category].append({
                'keyword': row[1],
                'pagerank': float(row[2]) if row[2] else 0.0
            })

        # 如果没有category，按importance自动分组
        if not communities:
            all_keywords = self.db.execute(
                text("""
                    SELECT text, importance
                    FROM keywords
                    WHERE project_id = :pid
                    ORDER BY importance DESC
                    LIMIT 50
                """),
                {"pid": project_id}
            ).fetchall()

            # 简单分组：每10个关键词一组
            for i in range(0, len(all_keywords), 10):
                group = all_keywords[i:i+10]
                communities[f"主题{i//10 + 1}"] = [
                    {'keyword': kw[0], 'pagerank': float(kw[1]) if kw[1] else 0.0}
                    for kw in group
                ]

        # 转换为列表格式
        result_list = []
        for comm_id, keywords in communities.items():
            keywords_sorted = sorted(keywords, key=lambda x: x['pagerank'], reverse=True)

            result_list.append({
                'community_id': comm_id,
                'label': keywords_sorted[0]['keyword'] if keywords_sorted else comm_id,
                'keywords': [kw['keyword'] for kw in keywords_sorted[:10]],
                'size': len(keywords)
            })

        return result_list

    def _extract_keyword_relations(self, project_id: int) -> List[Dict]:
        """提取关键词共现关系"""
        result = self.db.execute(
            text("""
                SELECT keyword1_id, keyword2_id,
                       co_occurrence, strength
                FROM keyword_relations
                WHERE project_id = :pid
                ORDER BY co_occurrence DESC
                LIMIT 100
            """),
            {"pid": project_id}
        ).fetchall()

        # 获取关键词文本
        relations = []
        for row in result:
            # 查询keyword1和keyword2的文本
            source_text = self.db.execute(
                text("SELECT text FROM keywords WHERE id = :kid LIMIT 1"),
                {"kid": row[0]}
            ).scalar()

            target_text = self.db.execute(
                text("SELECT text FROM keywords WHERE id = :kid LIMIT 1"),
                {"kid": row[1]}
            ).scalar()

            if source_text and target_text:
                relations.append({
                    'source': source_text,
                    'target': target_text,
                    'strength': float(row[3]) if row[3] else 0.0,
                    'co_occurrence': row[2] or 0
                })

        return relations

    def _extract_core_entities(self, project_id: int) -> Dict[str, List[Dict]]:
        """
        提取核心实体（按类型分组）

        从document_entities表通过project关联提取实体
        """
        result = {
            'PERSON': [],
            'LOCATION': [],
            'EVENT': [],
            'ORGANIZATION': [],
            'THEME': [],
            'DATA_SOURCE': [],
            'FINDING': []
        }

        # 通过document_entities关联获取实体（该表通过document_id与项目关联）
        for entity_type in ['PERSON', 'LOCATION', 'ORGANIZATION', 'EVENT']:
            entities = self.db.execute(
                text("""
                    SELECT e.name, e.entity_type, COUNT(*) as frequency
                    FROM entities e
                    JOIN document_entities de ON e.id = de.entity_id
                    JOIN documents d ON de.document_id = d.id
                    WHERE d.project_id = :pid AND e.entity_type = :etype
                    GROUP BY e.name, e.entity_type
                    ORDER BY frequency DESC
                    LIMIT 20
                """),
                {"pid": project_id, "etype": entity_type}
            ).fetchall()

            result[entity_type] = [
                {
                    'name': e[0],
                    'type': e[1],
                    'frequency': e[2]
                }
                for e in entities
            ]

        return result

    def _extract_entity_relations(self, project_id: int) -> List[Dict]:
        """提取实体关系网络"""
        # entity_relations表没有project_id，需要通过document关联
        result = self.db.execute(
            text("""
                SELECT DISTINCT er.source_entity_id, er.target_entity_id,
                       er.relation_type, er.confidence
                FROM entity_relations er
                JOIN entities e1 ON er.source_entity_id = e1.id
                JOIN document_entities de ON e1.id = de.entity_id
                JOIN documents d ON de.document_id = d.id
                WHERE d.project_id = :pid
                LIMIT 100
            """),
            {"pid": project_id}
        ).fetchall()

        relations = []
        for row in result:
            # 查询实体名称
            source_name = self.db.execute(
                text("SELECT name FROM entities WHERE id = :eid LIMIT 1"),
                {"eid": row[0]}
            ).scalar()

            target_name = self.db.execute(
                text("SELECT name FROM entities WHERE id = :eid LIMIT 1"),
                {"eid": row[1]}
            ).scalar()

            if source_name and target_name:
                relations.append({
                    'source': source_name,
                    'target': target_name,
                    'relation_type': row[2] or 'related_to',
                    'confidence': float(row[3]) if row[3] else 0.0
                })

        return relations

    def _extract_timeline(self, project_id: int) -> List[Dict]:
        """
        提取时间线（编年史）

        优先使用timeline_events表，如果没有则从document_chunks提取
        """
        # 先尝试从timeline_events表获取
        timeline_events = self.db.execute(
            text("""
                SELECT id, date, event_type, description, title
                FROM timeline_events
                WHERE project_id = :pid
                ORDER BY date
                LIMIT 200
            """),
            {"pid": project_id}
        ).fetchall()

        timeline = []
        if timeline_events:
            for event in timeline_events:
                # 处理日期字段（可能是字符串或datetime对象）
                timestamp = None
                if event[1]:
                    if hasattr(event[1], 'isoformat'):
                        timestamp = event[1].isoformat()
                    else:
                        timestamp = str(event[1])

                timeline.append({
                    'event_id': event[0],
                    'content': event[3] or event[4] or '',  # description or title
                    'timestamp': timestamp,
                    'event_type': event[2] or 'general',
                    'index': len(timeline)
                })
        else:
            # 如果没有timeline_events，从document_chunks提取（使用temporal_context）
            chunks = self.db.execute(
                text("""
                    SELECT id, text, temporal_context, created_at
                    FROM document_chunks
                    WHERE project_id = :pid AND temporal_context IS NOT NULL
                    ORDER BY created_at
                    LIMIT 100
                """),
                {"pid": project_id}
            ).fetchall()

            for chunk in chunks:
                timeline.append({
                    'chunk_id': chunk[0],
                    'content': chunk[1][:500] if chunk[1] else '',
                    'temporal_context': chunk[2],
                    'timestamp': chunk[3].isoformat() if chunk[3] else None,
                    'index': len(timeline)
                })

        return timeline

    def _calculate_temporal_span(self, timeline: List[Dict]) -> Dict:
        """计算时间跨度"""
        if not timeline:
            return {'has_temporal': False}

        timestamps = [t['timestamp'] for t in timeline if t['timestamp']]

        if not timestamps:
            return {'has_temporal': False}

        return {
            'has_temporal': True,
            'earliest': min(timestamps),
            'latest': max(timestamps),
            'event_count': len(timeline)
        }

    def _extract_related_reports(self, project_id: int) -> List[Dict]:
        """提取相关报告"""
        # 从report_network_nodes表获取
        result = self.db.execute(
            text("""
                SELECT node_id, label, centrality_degree
                FROM report_network_nodes
                WHERE project_id = :pid AND node_type = 'report'
                ORDER BY centrality_degree DESC
                LIMIT 10
            """),
            {"pid": project_id}
        ).fetchall()

        return [
            {
                'report_id': row[0],
                'pagerank': float(row[2]) if row[2] else 0.0,
                'citation_count': 0  # 暂时没有引用计数
            }
            for row in result
        ]

    def _build_citation_pool(self, project_id: int) -> List[Dict]:
        """
        构建原文引用池

        这是反幻觉的核心：所有可引用的原文片段
        每个片段都带有完整的出处信息
        """
        # 从document_chunks获取所有文本块
        chunks = self.db.execute(
            text("""
                SELECT dc.id, dc.text, dc.chunk_index,
                       d.name, d.id as document_id
                FROM document_chunks dc
                LEFT JOIN documents d ON dc.document_id = d.id
                WHERE dc.project_id = :pid
                ORDER BY dc.id
                LIMIT 2000
            """),
            {"pid": project_id}
        ).fetchall()

        citation_pool = []
        for chunk in chunks:
            citation_pool.append({
                'citation_id': f"chunk_{chunk[0]}",
                'content': chunk[1] or '',
                'source_document': chunk[3] or '未知文档',
                'document_id': chunk[4],
                'chunk_index': chunk[2] or 0,
                'citation_format': f"（来源：{chunk[3] or '未知文档'}, 第{(chunk[2] or 0)+1}段）"
            })

        logger.info(f"📚 构建引用池：{len(citation_pool)}个可引用片段")
        return citation_pool

    def _extract_data_profile(self, project_id: int) -> Dict:
        """
        提取数据画像

        从documents表的data_profile字段中提取动态发现的维度
        """
        from app.models.document import Document

        docs = self.db.query(Document)\
            .filter(Document.project_id == project_id)\
            .all()

        # 聚合所有文档的数据画像
        all_dimensions = []
        for doc in docs:
            if hasattr(doc, 'extra_data') and doc.extra_data:
                profile = doc.extra_data.get('dynamic_discovery', {}).get('profile', {})
                dimensions = profile.get('discovered_dimensions', [])
                all_dimensions.extend(dimensions)

        # 如果没有数据画像，返回空
        if not all_dimensions:
            return {'discovered_dimensions': []}

        # 简单聚合（去重并计数）
        from collections import Counter
        dim_counter = Counter(dim['dimension_name'] for dim in all_dimensions)

        aggregated = [
            {
                'dimension_name': name,
                'frequency': count
            }
            for name, count in dim_counter.most_common(10)
        ]

        return {'discovered_dimensions': aggregated}

    def generate_dynamic_outline(
        self,
        material: ReportMaterial,
        report_level: int = 1
    ) -> List[Dict]:
        """
        动态生成报告大纲

        Args:
            material: 报告素材
            report_level: 报告层级（1=田野调查, 2=学术分析, 3=商业分析）

        Returns:
            章节列表，每个章节包含：
            - chapter: 章节标题
            - reason: 为什么要这个章节（数据驱动的理由）
            - content_sources: 内容来源（关键词/实体/时间线）
            - min_words: 最少字数
        """
        logger.info(f"📝 生成Level {report_level}报告大纲...")

        if report_level == 1:
            return self._generate_level1_outline(material)
        elif report_level == 2:
            return self._generate_level2_outline(material)
        elif report_level == 3:
            return self._generate_level3_outline(material)
        else:
            raise ValueError(f"不支持的报告层级: {report_level}")

    def _generate_level1_outline(self, material: ReportMaterial) -> List[Dict]:
        """
        生成田野调查报告大纲（Level 1）

        数据驱动原则：
        1. 编年史时间线优先
        2. 关键词社区形成章节
        3. 核心实体深度展开
        """
        outline = []

        # 第1章：概述（固定）
        outline.append({
            'chapter': '第一章 调查概述',
            'reason': '总体介绍项目背景和数据来源',
            'content_sources': {
                'type': 'overview',
                'data': {
                    'total_documents': material.total_documents,
                    'total_words': material.total_words,
                    'temporal_span': material.temporal_span
                }
            },
            'min_words': 1000
        })

        # 第2章：编年史时间线（如果有时间跨度）
        if material.temporal_span.get('has_temporal'):
            outline.append({
                'chapter': '第二章 田野调查编年史',
                'reason': f"按时间顺序记录{material.temporal_span['event_count']}个调查事件",
                'content_sources': {
                    'type': 'timeline',
                    'data': material.timeline
                },
                'min_words': 2000
            })

        # 第3-N章：基于关键词社区的主题章节
        for idx, community in enumerate(material.keyword_communities[:5], start=len(outline)+1):
            outline.append({
                'chapter': f"第{self._num_to_chinese(idx)}章 {community['label']}",
                'reason': f"关键词社区分析：包含{community['size']}个相关概念",
                'content_sources': {
                    'type': 'keyword_community',
                    'data': community
                },
                'min_words': 1500
            })

        # 倒数第2章：核心人物与关键地点
        if material.core_entities['PERSON'] or material.core_entities['LOCATION']:
            outline.append({
                'chapter': f"第{self._num_to_chinese(len(outline)+1)}章 核心主体分析",
                'reason': f"核心人物{len(material.core_entities['PERSON'])}位, "
                         f"关键地点{len(material.core_entities['LOCATION'])}处",
                'content_sources': {
                    'type': 'entities',
                    'data': {
                        'persons': material.core_entities['PERSON'][:10],
                        'locations': material.core_entities['LOCATION'][:10]
                    }
                },
                'min_words': 2000
            })

        # 最后一章：总结与发现
        outline.append({
            'chapter': f"第{self._num_to_chinese(len(outline)+1)}章 调查发现总结",
            'reason': '归纳核心发现和研究价值',
            'content_sources': {
                'type': 'conclusion',
                'data': {
                    'main_keywords': material.main_keywords[:10],
                    'communities': material.keyword_communities
                }
            },
            'min_words': 1000
        })

        logger.info(f"✅ Level 1大纲生成完成：{len(outline)}个章节")
        return outline

    def _generate_level2_outline(self, material: ReportMaterial) -> List[Dict]:
        """生成学术分析报告大纲（Level 2）- 费孝通视角"""
        outline = [
            {
                'chapter': '第一章 理论框架：费孝通《乡土中国》',
                'reason': '介绍理论工具和分析视角',
                'content_sources': {'type': 'theory_intro'},
                'min_words': 1000
            },
            {
                'chapter': '第二章 差序格局的当代呈现',
                'reason': '分析材料中的关系网络和社会结构',
                'content_sources': {
                    'type': 'feixiaotong_dimension',
                    'dimension': 'differential_mode',
                    'data': material.entity_relations
                },
                'min_words': 2500
            },
            {
                'chapter': '第三章 礼治秩序的延续与变迁',
                'reason': '探讨传统规范在现代社会中的表现',
                'content_sources': {
                    'type': 'feixiaotong_dimension',
                    'dimension': 'ritual_order'
                },
                'min_words': 2500
            },
            {
                'chapter': '第四章 熟人社会的信任机制',
                'reason': '分析社会关系和信任网络',
                'content_sources': {
                    'type': 'feixiaotong_dimension',
                    'dimension': 'acquaintance_society'
                },
                'min_words': 2500
            },
            {
                'chapter': '第五章 现代化进程的冲击与适应',
                'reason': '探讨传统社会的转型路径',
                'content_sources': {
                    'type': 'feixiaotong_dimension',
                    'dimension': 'modernization'
                },
                'min_words': 2000
            },
            {
                'chapter': '第六章 理论对话与学术启示',
                'reason': '材料与理论的深度对话',
                'content_sources': {'type': 'theory_conclusion'},
                'min_words': 1500
            }
        ]

        logger.info(f"✅ Level 2大纲生成完成：{len(outline)}个章节")
        return outline

    def _generate_level3_outline(self, material: ReportMaterial) -> List[Dict]:
        """生成商业分析报告大纲（Level 3）- 商业视角"""
        outline = [
            {
                'chapter': '执行摘要',
                'reason': '为决策者提供核心要点',
                'content_sources': {'type': 'executive_summary'},
                'min_words': 800
            },
            {
                'chapter': '第一章 乡村运营SOP六维度评估',
                'reason': '系统评估社区运营的六个关键维度',
                'content_sources': {
                    'type': 'business_sop',
                    'dimensions': [
                        '社区基础调研', '文化资产评估', '利益相关方分析',
                        '业态可行性', '风险评估', '行动路径规划'
                    ]
                },
                'min_words': 2500
            },
            {
                'chapter': '第二章 社会结构与文化资本分析',
                'reason': '结合费孝通理论分析社会基础',
                'content_sources': {'type': 'social_capital'},
                'min_words': 2000
            },
            {
                'chapter': '第三章 核心议题识别与趋势分析',
                'reason': '基于关键词网络识别关键议题',
                'content_sources': {
                    'type': 'trend_analysis',
                    'data': material.main_keywords
                },
                'min_words': 2000
            },
            {
                'chapter': '第四章 SWOT综合分析',
                'reason': '系统评估优势、劣势、机会、威胁',
                'content_sources': {'type': 'swot'},
                'min_words': 1500
            },
            {
                'chapter': '第五章 战略建议与行动计划',
                'reason': '提供可落地的战略建议',
                'content_sources': {'type': 'action_plan'},
                'min_words': 2000
            },
            {
                'chapter': '第六章 风险预警与应对策略',
                'reason': '识别关键风险并提供应对方案',
                'content_sources': {'type': 'risk_management'},
                'min_words': 1000
            }
        ]

        logger.info(f"✅ Level 3大纲生成完成：{len(outline)}个章节")
        return outline

    @staticmethod
    def _num_to_chinese(num: int) -> str:
        """数字转中文"""
        chinese_nums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        if num <= 10:
            return chinese_nums[num]
        else:
            return str(num)
