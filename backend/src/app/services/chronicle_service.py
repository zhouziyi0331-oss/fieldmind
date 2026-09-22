"""编年史服务 - 时间线智能关联和叙事生成"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
import json

from app.models.timeline import TimelineEvent
from app.services.multi_provider_llm_manager import MultiProviderLLMManager


class ChronicleService:
    """编年史服务：处理时间线事件的智能关联和叙事生成"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.llm_manager = MultiProviderLLMManager()

    async def analyze_event_relations(
        self,
        event_id: str,
        context_window_days: int = 90
    ) -> Dict[str, Any]:
        """
        分析单个事件的关联关系

        Args:
            event_id: 事件ID
            context_window_days: 上下文窗口（前后多少天的事件作为上下文）

        Returns:
            {
                "causes": ["event_id1"],  # 可能的因
                "effects": ["event_id2"],  # 可能的果
                "related": ["event_id3"],  # 相关事件
                "theme_tags": ["土地改革"],  # 主题标签
                "key_persons": ["李明"],  # 关键人物
                "key_locations": ["XX村"]  # 关键地点
            }
        """
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # 获取上下文窗口内的事件
        from datetime import timedelta
        start_date = event.date - timedelta(days=context_window_days)
        end_date = event.date + timedelta(days=context_window_days)

        context_events = self.db.query(TimelineEvent).filter(
            and_(
                TimelineEvent.date >= start_date,
                TimelineEvent.date <= end_date,
                TimelineEvent.id != event_id
            )
        ).order_by(TimelineEvent.date).all()

        # 构建 LLM prompt
        prompt = self._build_relation_analysis_prompt(event, context_events)

        # 调用 LLM 分析
        try:
            # 获取可用的 provider
            providers = list(self.llm_manager.providers.values())
            if not providers:
                raise Exception("没有可用的 LLM 提供商")

            # 使用第一个可用的 provider
            provider = providers[0]

            from app.services.llm.base import LLMMessage, MessageRole, LLMConfig

            # 构建消息
            messages = [
                LLMMessage(role=MessageRole.USER, content=prompt)
            ]

            # 调用 LLM
            response = await provider.chat(
                messages=messages,
                config=LLMConfig(
                    model=provider.default_model,
                    temperature=0.3,
                    max_tokens=1000
                )
            )

            # 解析 JSON 响应
            result = json.loads(response.content)

            return {
                "causes": result.get("causes", []),
                "effects": result.get("effects", []),
                "related": result.get("related", []),
                "theme_tags": result.get("theme_tags", []),
                "key_persons": result.get("key_persons", []),
                "key_locations": result.get("key_locations", [])
            }

        except Exception as e:
            print(f"LLM关联分析失败: {str(e)}")
            # 返回空结果
            return {
                "causes": [],
                "effects": [],
                "related": [],
                "theme_tags": [],
                "key_persons": [],
                "key_locations": []
            }

    def _build_relation_analysis_prompt(
        self,
        event: TimelineEvent,
        context_events: List[TimelineEvent]
    ) -> str:
        """构建关联分析的 LLM prompt"""

        context_text = "\n".join([
            f"[{e.id}] {e.date.strftime('%Y年%m月%d日')} - {e.title}\n描述：{e.description or '无'}"
            for e in context_events
        ])

        prompt = f"""你是一位人类学家，正在分析田野调查中的事件关联。

【当前事件】
ID: {event.id}
时间: {event.date.strftime('%Y年%m月%d日')}
标题: {event.title}
描述: {event.description or '无'}

【上下文事件（前后90天）】
{context_text}

【任务】
分析当前事件与上下文事件的关联关系，识别：
1. **因果关系**：哪些事件可能是当前事件的"因"（导致当前事件发生）？哪些是"果"（由当前事件导致）？
2. **主题线索**：当前事件属于什么主题？（如：土地改革、村委会选举、经济发展、基础设施建设等）
3. **关键要素**：事件中涉及的关键人物和地点

【输出要求】
- causes: 返回导致当前事件的前置事件ID（从上下文事件中选择，可为空）
- effects: 返回当前事件导致的后续事件ID（从上下文事件中选择，可为空）
- related: 返回相关但无明确因果的事件ID（从上下文事件中选择，可为空）
- theme_tags: 提取主题标签，使用中文短语（如：土地改革、村委会选举）
- key_persons: 提取关键人物姓名
- key_locations: 提取关键地点名称

返回JSON格式。如果某项为空，返回空数组[]。
"""
        return prompt

    async def generate_narrative_summary(
        self,
        event_id: str
    ) -> str:
        """
        为单个事件生成简短的叙事描述（用于编年史页面展示）

        Args:
            event_id: 事件ID

        Returns:
            叙事描述文本（1-2句话）
        """
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        prompt = f"""将以下事件转化为简短的叙事描述（1-2句话，适合时间轴展示）：

时间: {event.date.strftime('%Y年%m月%d日')}
标题: {event.title}
描述: {event.description or '无'}

要求：
- 简洁明了，突出关键信息
- 使用客观的叙事语气
- 1-2句话即可

示例：
"村委会完成换届选举，李明当选新一届村长，承诺将推动土地流转改革。"
"启动农村道路硬化工程，计划在年内完成主干道建设，改善村民出行条件。"

请直接返回叙事文本，不要额外说明。
"""

        try:
            # 获取可用的 provider
            providers = list(self.llm_manager.providers.values())
            if not providers:
                raise Exception("没有可用的 LLM 提供商")

            provider = providers[0]

            from app.services.llm.base import LLMMessage, MessageRole, LLMConfig

            messages = [
                LLMMessage(role=MessageRole.USER, content=prompt)
            ]

            response = await provider.chat(
                messages=messages,
                config=LLMConfig(
                    model=provider.default_model,
                    temperature=0.5,
                    max_tokens=200
                )
            )

            return response.content.strip()
        except Exception as e:
            print(f"叙事生成失败: {str(e)}")
            # 降级：直接返回标题+描述
            return f"{event.title}。{event.description or ''}"

    async def update_event_intelligence(
        self,
        event_id: str,
        context_window_days: int = 90
    ) -> TimelineEvent:
        """
        更新单个事件的智能分析字段

        Args:
            event_id: 事件ID
            context_window_days: 分析上下文窗口

        Returns:
            更新后的 TimelineEvent
        """
        # 1. 关联分析
        relations_data = await self.analyze_event_relations(event_id, context_window_days)

        # 2. 生成叙事
        narrative = await self.generate_narrative_summary(event_id)

        # 3. 更新数据库
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        event.relations = {
            "causes": relations_data.get("causes", []),
            "effects": relations_data.get("effects", []),
            "related": relations_data.get("related", [])
        }
        event.theme_tags = relations_data.get("theme_tags", [])
        event.key_persons = relations_data.get("key_persons", [])
        event.key_locations = relations_data.get("key_locations", [])
        event.narrative_summary = narrative
        event.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(event)

        return event

    async def batch_update_intelligence(
        self,
        project_id: int,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量更新某个项目（或某年）的所有事件智能分析

        Args:
            project_id: 项目ID（通过 document_ids 关联）
            year: 可选，只更新某一年的事件

        Returns:
            {"updated_count": 10, "failed_count": 2}
        """
        # TODO: 需要在 TimelineEvent 中添加 project_id 字段
        # 暂时通过 document_ids 关联项目（假设已有项目关联逻辑）

        query = self.db.query(TimelineEvent)
        if year:
            query = query.filter(extract('year', TimelineEvent.date) == year)

        events = query.order_by(TimelineEvent.date).all()

        updated_count = 0
        failed_count = 0

        for event in events:
            try:
                await self.update_event_intelligence(event.id)
                updated_count += 1
            except Exception as e:
                print(f"更新事件 {event.id} 失败: {str(e)}")
                failed_count += 1

        return {
            "updated_count": updated_count,
            "failed_count": failed_count
        }

    def get_chronicle_by_year(
        self,
        project_id: int,
        year: int
    ) -> Dict[str, Any]:
        """
        获取某一年的编年史数据（用于前端展示）

        Args:
            project_id: 项目ID
            year: 年份

        Returns:
            {
                "year": 2020,
                "events": [
                    {
                        "id": "...",
                        "date": "2020-03-15",
                        "title": "...",
                        "narrative": "...",
                        "theme_tags": ["土地改革"],
                        "key_persons": ["李明"],
                        "relations": {...}
                    }
                ],
                "theme_summary": {
                    "土地改革": 3,
                    "村委会选举": 2
                }
            }
        """
        # TODO: 添加 project_id 过滤
        events = self.db.query(TimelineEvent).filter(
            extract('year', TimelineEvent.date) == year
        ).order_by(TimelineEvent.date).all()

        # 统计主题
        theme_summary = {}
        events_data = []

        for event in events:
            events_data.append({
                "id": event.id,
                "date": event.date.strftime('%Y-%m-%d'),
                "title": event.title,
                "narrative": event.narrative_summary or event.description,
                "theme_tags": event.theme_tags or [],
                "key_persons": event.key_persons or [],
                "key_locations": event.key_locations or [],
                "relations": event.relations or {}
            })

            # 统计主题
            for theme in (event.theme_tags or []):
                theme_summary[theme] = theme_summary.get(theme, 0) + 1

        return {
            "year": year,
            "events": events_data,
            "theme_summary": theme_summary
        }

    def get_chronicle_years(self, project_id: int) -> List[int]:
        """
        获取某个项目所有有事件的年份列表

        Args:
            project_id: 项目ID

        Returns:
            [2020, 2021, 2022, 2023]
        """
        # TODO: 添加 project_id 过滤
        from sqlalchemy import func
        years = self.db.query(
            func.distinct(extract('year', TimelineEvent.date)).label('year')
        ).order_by('year').all()

        return [int(y.year) for y in years if y.year]
