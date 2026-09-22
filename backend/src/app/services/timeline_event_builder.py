"""
时间线事件构建器 - 从文档内容构建TimelineEvent记录
整合 temporal_extractor + chronicle_service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.timeline import TimelineEvent
from app.services.temporal_extractor import get_temporal_extractor

logger = logging.getLogger(__name__)


class TimelineEventBuilder:
    """从文档内容构建时间线事件"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.temporal_extractor = get_temporal_extractor()

    def build_events_from_document(
        self,
        document_id: int,
        project_id: int,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TimelineEvent]:
        """
        从文档中构建时间线事件

        Args:
            document_id: 文档ID
            project_id: 项目ID
            text_content: 文档文本内容
            metadata: 文档元数据

        Returns:
            创建的 TimelineEvent 列表
        """
        if not text_content or len(text_content.strip()) < 50:
            logger.info(f"文档内容过短，跳过时间线事件提取")
            return []

        # 1. 提取文档日期（作为参考日期）
        document_date = self._extract_document_date(text_content, metadata)

        # 2. 提取时间表达式
        time_expressions = self.temporal_extractor.extract_dates(
            text=text_content,
            document_date=document_date
        )

        if not time_expressions:
            logger.info(f"未从文档中提取到时间表达式")
            return []

        # 3. 为每个时间表达式构建事件
        events = []
        for time_expr in time_expressions:
            event = self._build_event_from_time_expression(
                document_id=document_id,
                project_id=project_id,
                time_expr=time_expr,
                text_content=text_content,
                metadata=metadata
            )
            if event:
                events.append(event)

        # 4. 批量保存到数据库
        if events:
            try:
                self.db.bulk_save_objects(events)
                self.db.commit()
                logger.info(f"✅ 为文档 {document_id} 创建了 {len(events)} 个时间线事件")
            except Exception as e:
                logger.error(f"❌ 保存时间线事件失败: {e}", exc_info=True)
                self.db.rollback()
                events = []

        return events

    def _extract_document_date(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Optional[datetime]:
        """提取文档日期"""
        filename = metadata.get('filename', '') if metadata else ''
        upload_time = metadata.get('created_at') if metadata else None

        return self.temporal_extractor.extract_document_date(
            text=text,
            filename=filename,
            upload_time=upload_time
        )

    def _build_event_from_time_expression(
        self,
        document_id: int,
        project_id: int,
        time_expr: Dict[str, Any],
        text_content: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Optional[TimelineEvent]:
        """
        从单个时间表达式构建事件

        策略：
        1. 提取时间表达式所在句子作为描述
        2. 从描述中提取事件标题（主语+谓语+宾语）
        3. 尝试分类事件类型
        """
        # 提取上下文句子
        position = time_expr['position']
        context = self._extract_context_sentence(text_content, position)

        if not context or len(context.strip()) < 10:
            return None

        # 提取事件标题（简化版：取句子前50字符）
        title = self._extract_event_title(context)

        # 分类事件类型
        event_type = self._classify_event_type(context)

        # 创建 TimelineEvent 对象
        event = TimelineEvent(
            project_id=project_id,
            document_id=document_id,
            title=title,
            description=context,
            narrative=context,  # 初始叙事就是原文
            date=time_expr['date'],
            event_type=event_type,
            confidence_score=int(time_expr['confidence'] * 100),
            source_type='document',
            extra_metadata={
                'time_expression': time_expr['text'],
                'time_type': time_expr['type'],
                'filename': metadata.get('filename') if metadata else None
            }
        )

        return event

    def _extract_context_sentence(
        self,
        text: str,
        position: tuple
    ) -> str:
        """提取时间表达式所在的句子"""
        start, end = position

        # 向前找句子开始（句号、问号、感叹号、换行）
        sentence_start = start
        for i in range(start - 1, max(0, start - 200), -1):
            if text[i] in '。！？\n':
                sentence_start = i + 1
                break

        # 向后找句子结束
        sentence_end = end
        for i in range(end, min(len(text), end + 200)):
            if text[i] in '。！？\n':
                sentence_end = i
                break

        sentence = text[sentence_start:sentence_end].strip()
        return sentence

    def _extract_event_title(self, sentence: str) -> str:
        """提取事件标题"""
        # 简单策略：
        # 1. 去掉时间表达式
        # 2. 取前50个字符
        # 3. 去掉标点符号

        import re

        # 去掉时间表达式
        title = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日', '', sentence)
        title = re.sub(r'\d{4}年\d{1,2}月', '', title)
        title = re.sub(r'\d{4}年', '', title)

        # 去掉开头的标点
        title = re.sub(r'^[，,、；。！？\s]+', '', title)

        # 截取前50字符
        if len(title) > 50:
            title = title[:50] + '...'

        return title.strip() or '未命名事件'

    def _classify_event_type(self, sentence: str) -> str:
        """
        简单分类事件类型

        基于关键词匹配
        """
        type_keywords = {
            '政治': ['选举', '换届', '任命', '会议', '决议', '村委会', '党支部'],
            '经济': ['企业', '合作社', '项目', '投资', '分红', '收入', '支出'],
            '土地': ['土地', '确权', '登记', '承包', '流转', '征用'],
            '基础设施': ['道路', '硬化', '工程', '修建', '竣工', '桥梁', '水利'],
            '民俗': ['祭祀', '庙会', '节日', '仪式', '传统', '习俗'],
            '教育': ['学校', '培训', '教育', '学习', '课程'],
            '医疗': ['医院', '诊所', '卫生', '健康', '治疗'],
            '环境': ['环境', '污染', '绿化', '生态', '保护'],
            '社会': ['矛盾', '纠纷', '调解', '治安', '案件'],
        }

        for event_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in sentence:
                    return event_type

        return '其他'


def get_timeline_event_builder(db: Session) -> TimelineEventBuilder:
    """获取时间线事件构建器实例"""
    return TimelineEventBuilder(db)
