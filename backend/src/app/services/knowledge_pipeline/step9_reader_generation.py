"""
Step 9: 阅读器生成服务
Reader Generation Service

功能：
1. 应用阅读器模板
2. 生成实体卡片（人物卡、地点卡）
3. 生成事件时间线
4. 生成关系网络图数据
5. 生成 Wiki 页面（Markdown/HTML）
6. 保存到 wiki_pages 表
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List, Dict, Any
import uuid
import json

from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    KnowledgeUnit, WikiPage, ReaderTemplate
)
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class ReaderGenerationService:
    """阅读器生成服务（Step 9）"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def generate_readers(self, document_id: int) -> Dict[str, Any]:
        """
        生成阅读器

        Args:
            document_id: 文档 ID

        Returns:
            生成结果
        """
        logger.info(f"📖 Step 9: 开始阅读器生成 - 文档 {document_id}")

        try:
            # 获取所有知识组件
            entities = self._get_entities(document_id)
            events = self._get_events(document_id)
            relationships = self._get_relationships(document_id)
            knowledge_units = self._get_knowledge_units(document_id)

            if not any([entities, events, knowledge_units]):
                logger.warning(f"文档 {document_id} 没有知识组件")
                return {'success': False, 'message': '没有知识组件'}

            wiki_pages = []

            # 1. 为每个实体生成卡片页面
            entity_pages = self._generate_entity_cards(entities, relationships, events)
            wiki_pages.extend(entity_pages)

            # 2. 生成事件时间线页面
            timeline_page = self._generate_timeline_page(events, entities)
            if timeline_page:
                wiki_pages.append(timeline_page)

            # 3. 生成关系网络图页面
            network_page = self._generate_network_page(entities, relationships)
            if network_page:
                wiki_pages.append(network_page)

            # 4. 生成知识单元索引页面
            index_page = self._generate_index_page(knowledge_units)
            if index_page:
                wiki_pages.append(index_page)

            # 保存到数据库
            saved_count = self._save_wiki_pages(document_id, wiki_pages)

            result = {
                'success': True,
                'document_id': document_id,
                'pages_created': saved_count,
                'page_types': self._count_by_type(wiki_pages),
                'entity_cards': len([p for p in wiki_pages if p['page_type'] == 'entity']),
                'timeline_pages': len([p for p in wiki_pages if p['page_type'] == 'timeline']),
                'network_pages': len([p for p in wiki_pages if p['page_type'] == 'network']),
                'index_pages': len([p for p in wiki_pages if p['page_type'] == 'index'])
            }

            logger.info(
                f"✅ Step 9 完成: 生成了 {saved_count} 个页面, "
                f"实体卡:{result['entity_cards']}, 时间线:{result['timeline_pages']}, "
                f"网络图:{result['network_pages']}, 索引:{result['index_pages']}"
            )

            # 发布事件
            publish_event(
                event_type='reader.generated',
                payload={
                    'step': 9,
                    'step_name': 'reader_generation',
                    'document_id': document_id,
                    'result': result
                },
                publisher='ReaderGenerationService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 9 失败: {e}", exc_info=True)
            raise

    def _get_entities(self, document_id: int) -> List[Dict]:
        """获取实体"""
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).all()

        return [
            {
                'id': e.entity_id,
                'name': e.entity_name,
                'type': e.entity_type,
                'description': e.description,
                'mention_count': e.mention_count
            }
            for e in entities
        ]

    def _get_events(self, document_id: int) -> List[Dict]:
        """获取事件"""
        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).all()

        return [
            {
                'id': e.event_id,
                'name': e.event_name,
                'type': e.event_type,
                'description': e.description,
                'time': e.normalized_time_start,
                'location': e.normalized_location,
                'participants': json.loads(e.participants) if e.participants else []
            }
            for e in events
        ]

    def _get_relationships(self, document_id: int) -> List[Dict]:
        """获取关系"""
        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).all()

        return [
            {
                'id': r.relationship_id,
                'subject_id': r.subject_id,
                'predicate': r.predicate,
                'object_id': r.object_id
            }
            for r in relationships
        ]

    def _get_knowledge_units(self, document_id: int) -> List[Dict]:
        """获取知识单元"""
        units = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.document_id == document_id
        ).all()

        return [
            {
                'id': u.unit_id,
                'type': u.unit_type,
                'title': u.title,
                'summary': u.summary
            }
            for u in units
        ]

    def _generate_entity_cards(
        self,
        entities: List[Dict],
        relationships: List[Dict],
        events: List[Dict]
    ) -> List[Dict]:
        """
        为每个实体生成卡片页面

        卡片内容：
        - 基本信息
        - 相关关系
        - 参与的事件
        """
        entity_pages = []

        for entity in entities:
            # 查找相关关系
            entity_rels = [r for r in relationships if r['subject_id'] == entity['id'] or r['object_id'] == entity['id']]

            # 查找参与的事件
            entity_events = []
            for event in events:
                for participant in event.get('participants', []):
                    if participant.get('entity_id') == entity['id']:
                        entity_events.append(event)
                        break

            # 生成 Markdown 内容
            markdown = self._generate_entity_card_markdown(entity, entity_rels, entity_events, entities)

            # 生成 HTML 内容
            html = self._markdown_to_html(markdown)

            entity_pages.append({
                'page_type': 'entity',
                'page_title': entity['name'],
                'target_id': entity['id'],
                'content_markdown': markdown,
                'content_html': html,
                'content_json': json.dumps({
                    'entity': entity,
                    'relationships': entity_rels,
                    'events': entity_events
                }),
                'tags': [entity['type']],
                'category': entity['type']
            })

        return entity_pages

    def _generate_entity_card_markdown(
        self,
        entity: Dict,
        relationships: List[Dict],
        events: List[Dict],
        all_entities: List[Dict]
    ) -> str:
        """生成实体卡片的 Markdown 内容"""
        lines = []

        # 标题
        lines.append(f"# {entity['name']}")
        lines.append("")

        # 基本信息
        lines.append("## 基本信息")
        lines.append(f"- **类型**: {entity['type']}")
        lines.append(f"- **提及次数**: {entity['mention_count']}")
        if entity.get('description'):
            lines.append(f"- **描述**: {entity['description']}")
        lines.append("")

        # 相关关系
        if relationships:
            lines.append("## 相关关系")
            for rel in relationships[:10]:  # 最多显示 10 个
                if rel['subject_id'] == entity['id']:
                    # 查找对象名称
                    obj_name = next((e['name'] for e in all_entities if e['id'] == rel['object_id']), rel['object_id'])
                    lines.append(f"- {rel['predicate']} [[{obj_name}]]")
                else:
                    # 查找主体名称
                    subj_name = next((e['name'] for e in all_entities if e['id'] == rel['subject_id']), rel['subject_id'])
                    lines.append(f"- 被 [[{subj_name}]] {rel['predicate']}")
            lines.append("")

        # 参与的事件
        if events:
            lines.append("## 参与的事件")
            for event in events[:10]:  # 最多显示 10 个
                time_str = f"({event['time']})" if event.get('time') else ""
                lines.append(f"- {event['name']} {time_str}")
            lines.append("")

        return "\n".join(lines)

    def _generate_timeline_page(
        self,
        events: List[Dict],
        entities: List[Dict]
    ) -> Dict:
        """
        生成事件时间线页面

        内容：
        - 按时间排序的事件列表
        - 可视化数据（JSON）
        """
        # 过滤有时间的事件
        timed_events = [e for e in events if e.get('time')]
        timed_events.sort(key=lambda e: e['time'])

        if not timed_events:
            return None

        # 生成 Markdown
        lines = []
        lines.append("# 事件时间线")
        lines.append("")

        for event in timed_events:
            lines.append(f"## {event['time']}: {event['name']}")
            if event.get('description'):
                lines.append(f"{event['description']}")
            if event.get('location'):
                lines.append(f"**地点**: {event['location']}")

            # 参与者
            if event.get('participants'):
                participant_names = []
                for p in event['participants']:
                    entity_name = next((e['name'] for e in entities if e['id'] == p['entity_id']), p.get('entity_name', ''))
                    if entity_name:
                        participant_names.append(entity_name)
                if participant_names:
                    lines.append(f"**参与者**: {', '.join(participant_names)}")

            lines.append("")

        markdown = "\n".join(lines)
        html = self._markdown_to_html(markdown)

        return {
            'page_type': 'timeline',
            'page_title': '事件时间线',
            'target_id': None,
            'content_markdown': markdown,
            'content_html': html,
            'content_json': json.dumps({
                'events': timed_events,
                'visualization_type': 'timeline'
            }),
            'tags': ['时间线', '事件'],
            'category': '可视化'
        }

    def _generate_network_page(
        self,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> Dict:
        """
        生成关系网络图页面

        内容：
        - 实体和关系的网络图数据（JSON）
        """
        if not entities or not relationships:
            return None

        # 准备网络图数据
        nodes = [
            {
                'id': e['id'],
                'label': e['name'],
                'type': e['type'],
                'size': e['mention_count']
            }
            for e in entities
        ]

        edges = [
            {
                'source': r['subject_id'],
                'target': r['object_id'],
                'label': r['predicate']
            }
            for r in relationships
        ]

        # 生成 Markdown
        markdown = f"""# 关系网络图

共有 {len(entities)} 个实体，{len(relationships)} 个关系。

（此页面包含可视化数据，请使用前端组件渲染）
"""

        html = self._markdown_to_html(markdown)

        return {
            'page_type': 'network',
            'page_title': '关系网络图',
            'target_id': None,
            'content_markdown': markdown,
            'content_html': html,
            'content_json': json.dumps({
                'nodes': nodes,
                'edges': edges,
                'visualization_type': 'network'
            }),
            'tags': ['网络图', '关系'],
            'category': '可视化'
        }

    def _generate_index_page(self, knowledge_units: List[Dict]) -> Dict:
        """
        生成知识单元索引页面

        内容：
        - 所有知识单元的目录
        """
        if not knowledge_units:
            return None

        # 按类型分组
        units_by_type = {}
        for unit in knowledge_units:
            unit_type = unit['type']
            if unit_type not in units_by_type:
                units_by_type[unit_type] = []
            units_by_type[unit_type].append(unit)

        # 生成 Markdown
        lines = []
        lines.append("# 知识单元索引")
        lines.append("")

        type_names = {
            'fact': '事实',
            'rule': '规则',
            'pattern': '模式',
            'insight': '洞察'
        }

        for unit_type, units in units_by_type.items():
            type_name = type_names.get(unit_type, unit_type)
            lines.append(f"## {type_name}（{len(units)}个）")
            lines.append("")

            for unit in units:
                lines.append(f"- **{unit['title']}**: {unit['summary']}")

            lines.append("")

        markdown = "\n".join(lines)
        html = self._markdown_to_html(markdown)

        return {
            'page_type': 'index',
            'page_title': '知识单元索引',
            'target_id': None,
            'content_markdown': markdown,
            'content_html': html,
            'content_json': json.dumps({
                'knowledge_units': knowledge_units,
                'units_by_type': {k: len(v) for k, v in units_by_type.items()}
            }),
            'tags': ['索引', '知识单元'],
            'category': '导航'
        }

    def _markdown_to_html(self, markdown: str) -> str:
        """
        将 Markdown 转换为 HTML（简化版本）

        可以使用 markdown 库进行转换
        """
        try:
            import markdown
            return markdown.markdown(markdown)
        except ImportError:
            # 如果没有安装 markdown 库，返回基本 HTML
            html = markdown.replace('\n', '<br>\n')
            html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
            html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
            return f"<div>{html}</div>"

    def _save_wiki_pages(self, document_id: int, wiki_pages: List[Dict]) -> int:
        """保存 Wiki 页面到数据库"""
        saved_count = 0

        # 获取项目 ID
        from app.models.project import ProjectDocument
        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            return 0

        for page in wiki_pages:
            page_id = f"wiki_{uuid.uuid4().hex[:16]}"

            db_page = WikiPage(
                page_id=page_id,
                project_id=doc.project_id,
                page_title=page['page_title'],
                page_type=page['page_type'],
                target_id=page.get('target_id'),
                content_markdown=page.get('content_markdown'),
                content_html=page.get('content_html'),
                content_json=page.get('content_json'),
                tags=json.dumps(page.get('tags', [])),
                category=page.get('category'),
                status='published'
            )

            self.db.add(db_page)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _count_by_type(self, wiki_pages: List[Dict]) -> Dict[str, int]:
        """统计各类型页面数量"""
        type_counts = {}
        for page in wiki_pages:
            page_type = page['page_type']
            type_counts[page_type] = type_counts.get(page_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def generate_document_readers(db: Session, document_id: int) -> Dict[str, Any]:
    """
    生成文档阅读器的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        生成结果
    """
    service = ReaderGenerationService(db)
    return service.generate_readers(document_id)
