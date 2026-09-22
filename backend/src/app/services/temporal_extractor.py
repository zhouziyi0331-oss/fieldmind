"""
时间抽取器 - 链路十五核心模块
从文本中抽取时间表达，并标准化为ISO格式日期

解决问题：
- "去年发生了什么" → AI能识别时间范围
- "2024年3月的报告" → 可按时间筛选
- "上周五的访谈" → 转换为绝对日期
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dateparser
import logging

logger = logging.getLogger(__name__)


class TemporalExtractor:
    """时间抽取器 - 支持中文和相对时间"""
    def __init__(self, reference_date: Optional[datetime] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        Args:
            reference_date: 参考日期（用于解析相对时间），默认为当前时间
        """
        self.reference_date = reference_date or datetime.now()

        # 中文时间表达的正则模式
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> List[Dict[str, Any]]:
        """构建时间表达的正则模式"""
        return [
            # 1. 完整日期格式
            {
                "name": "full_date",
                "pattern": r'\d{4}年\d{1,2}月\d{1,2}日',
                "example": "2024年3月15日"
            },
            {
                "name": "full_date_hyphen",
                "pattern": r'\d{4}-\d{1,2}-\d{1,2}',
                "example": "2024-03-15"
            },
            {
                "name": "full_date_slash",
                "pattern": r'\d{4}/\d{1,2}/\d{1,2}',
                "example": "2024/03/15"
            },

            # 2. 年月格式
            {
                "name": "year_month",
                "pattern": r'\d{4}年\d{1,2}月',
                "example": "2024年3月"
            },
            {
                "name": "year_month_hyphen",
                "pattern": r'\d{4}-\d{1,2}',
                "example": "2024-03"
            },

            # 3. 纯年份
            {
                "name": "year_only",
                "pattern": r'\d{4}年',
                "example": "2024年"
            },

            # 4. 相对时间（需要上下文）
            {
                "name": "relative_year",
                "pattern": r'(去年|前年|今年|明年|后年)',
                "example": "去年"
            },
            {
                "name": "relative_month",
                "pattern": r'(上个?月|这个?月|下个?月|本月)',
                "example": "上个月"
            },
            {
                "name": "relative_week",
                "pattern": r'(上周|上星期|本周|这周|这星期|下周|下星期)',
                "example": "上周"
            },
            {
                "name": "relative_day",
                "pattern": r'(昨天|前天|今天|明天|后天)',
                "example": "昨天"
            },

            # 5. 模糊时间
            {
                "name": "season",
                "pattern": r'(春季|夏季|秋季|冬季|春天|夏天|秋天|冬天)',
                "example": "春天"
            },
            {
                "name": "quarter",
                "pattern": r'\d{4}年?[第一二三四]季度',
                "example": "2024年第一季度"
            },
        ]

    def extract_dates(
        self,
        text: str,
        document_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        从文本中抽取所有时间表达

        Args:
            text: 待抽取的文本
            document_date: 文档的创建/修改日期（作为相对时间的参考）

        Returns:
            List of dicts with keys: text, date, confidence
        """
        if not text:
            return []

        # 使用文档日期或默认参考日期
        ref_date = document_date or self.reference_date

        extracted = []

        # 遍历所有模式
        for pattern_info in self.patterns:
            pattern = pattern_info["pattern"]
            name = pattern_info["name"]

            matches = re.finditer(pattern, text)

            for match in matches:
                time_expr = match.group(0)
                position = match.span()

                # 解析时间表达
                parsed_result = self._parse_time_expression(
                    time_expr,
                    name,
                    ref_date
                )

                if parsed_result:
                    extracted.append({
                        "text": time_expr,
                        "date": parsed_result["date"],
                        "date_iso": parsed_result["date_iso"],
                        "confidence": parsed_result["confidence"],
                        "type": name,
                        "position": position
                    })

        # 去重（同一时间点可能被多个模式匹配）
        extracted = self._deduplicate_dates(extracted)

        # 按位置排序
        extracted.sort(key=lambda x: x["position"][0])

        logger.info(f"📅 从文本中抽取了 {len(extracted)} 个时间表达")

        return extracted

    def _parse_time_expression(
        self,
        expr: str,
        expr_type: str,
        ref_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        解析单个时间表达

        Returns:
            {
                "date": datetime对象,
                "date_iso": ISO格式字符串,
                "confidence": 置信度 (0.0-1.0)
            }
        """
        try:
            # 优先使用自定义解析（更精确）
            custom_result = self._custom_parse(expr, expr_type, ref_date)
            if custom_result:
                return custom_result

            # 回退到dateparser（处理复杂表达）
            parsed = dateparser.parse(
                expr,
                languages=['zh', 'en'],
                settings={
                    'RELATIVE_BASE': ref_date,
                    'PREFER_DATES_FROM': 'past'
                }
            )

            if parsed:
                return {
                    "date": parsed,
                    "date_iso": parsed.strftime("%Y-%m-%d"),
                    "confidence": 0.7  # dateparser解析的置信度较低
                }

        except Exception as e:
            logger.debug(f"解析时间表达失败: {expr}, error: {e}")

        return None

    def _custom_parse(
        self,
        expr: str,
        expr_type: str,
        ref_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """自定义解析规则（高置信度）"""

        # 1. 完整日期格式
        if expr_type == "full_date":
            # "2024年3月15日"
            match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', expr)
            if match:
                year, month, day = map(int, match.groups())
                dt = datetime(year, month, day)
                return {
                    "date": dt,
                    "date_iso": dt.strftime("%Y-%m-%d"),
                    "confidence": 1.0
                }

        if expr_type in ["full_date_hyphen", "full_date_slash"]:
            # "2024-03-15" or "2024/03/15"
            separator = '-' if '-' in expr else '/'
            parts = expr.split(separator)
            if len(parts) == 3:
                year, month, day = map(int, parts)
                dt = datetime(year, month, day)
                return {
                    "date": dt,
                    "date_iso": dt.strftime("%Y-%m-%d"),
                    "confidence": 1.0
                }

        # 2. 年月格式
        if expr_type == "year_month":
            match = re.match(r'(\d{4})年(\d{1,2})月', expr)
            if match:
                year, month = map(int, match.groups())
                dt = datetime(year, month, 1)
                return {
                    "date": dt,
                    "date_iso": dt.strftime("%Y-%m-%d"),
                    "confidence": 0.95
                }

        if expr_type == "year_month_hyphen":
            parts = expr.split('-')
            if len(parts) == 2:
                year, month = map(int, parts)
                dt = datetime(year, month, 1)
                return {
                    "date": dt,
                    "date_iso": dt.strftime("%Y-%m-%d"),
                    "confidence": 0.95
                }

        # 3. 纯年份
        if expr_type == "year_only":
            year = int(expr.replace('年', ''))
            dt = datetime(year, 1, 1)
            return {
                "date": dt,
                "date_iso": dt.strftime("%Y-%m-%d"),
                "confidence": 0.9
            }

        # 4. 相对年份
        if expr_type == "relative_year":
            delta = {
                "前年": -2,
                "去年": -1,
                "今年": 0,
                "明年": 1,
                "后年": 2
            }.get(expr, 0)

            dt = ref_date + relativedelta(years=delta)
            dt = dt.replace(month=1, day=1)  # 年初
            return {
                "date": dt,
                "date_iso": dt.strftime("%Y-%m-%d"),
                "confidence": 0.85
            }

        # 5. 相对月份
        if expr_type == "relative_month":
            delta = {
                "上个月": -1,
                "上月": -1,
                "这个月": 0,
                "本月": 0,
                "这月": 0,
                "下个月": 1,
                "下月": 1
            }.get(expr, 0)

            dt = ref_date + relativedelta(months=delta)
            dt = dt.replace(day=1)  # 月初
            return {
                "date": dt,
                "date_iso": dt.strftime("%Y-%m-%d"),
                "confidence": 0.85
            }

        # 6. 相对周
        if expr_type == "relative_week":
            delta = {
                "上周": -7,
                "上星期": -7,
                "本周": 0,
                "这周": 0,
                "这星期": 0,
                "下周": 7,
                "下星期": 7
            }.get(expr, 0)

            dt = ref_date + timedelta(days=delta)
            # 调整到周一
            dt = dt - timedelta(days=dt.weekday())
            return {
                "date": dt,
                "date_iso": dt.strftime("%Y-%m-%d"),
                "confidence": 0.8
            }

        # 7. 相对天
        if expr_type == "relative_day":
            delta = {
                "前天": -2,
                "昨天": -1,
                "今天": 0,
                "明天": 1,
                "后天": 2
            }.get(expr, 0)

            dt = ref_date + timedelta(days=delta)
            return {
                "date": dt,
                "date_iso": dt.strftime("%Y-%m-%d"),
                "confidence": 0.9
            }

        # 8. 季节（近似）
        if expr_type == "season":
            season_months = {
                "春季": 3, "春天": 3,
                "夏季": 6, "夏天": 6,
                "秋季": 9, "秋天": 9,
                "冬季": 12, "冬天": 12
            }
            month = season_months.get(expr)
            if month:
                dt = ref_date.replace(month=month, day=1)
                return {
                    "date": dt,
                    "date_iso": dt.strftime("%Y-%m-%d"),
                    "confidence": 0.6  # 季节时间较模糊
                }

        return None

    def _deduplicate_dates(self, dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重复的日期（保留置信度最高的，去除重叠匹配）
        """
        if not dates:
            return []

        # 按位置排序
        dates.sort(key=lambda x: x["position"][0])

        # 去除位置重叠的匹配（保留置信度最高的）
        filtered = []
        for current in dates:
            # 检查是否与已选择的匹配重叠
            overlaps = False
            for selected in filtered:
                # 检查位置是否重叠
                if self._positions_overlap(current["position"], selected["position"]):
                    # 如果当前匹配更好（置信度更高或更精确），替换
                    if current["confidence"] > selected["confidence"]:
                        filtered.remove(selected)
                        filtered.append(current)
                    overlaps = True
                    break

            if not overlaps:
                filtered.append(current)

        # 再按日期去重（不同位置的相同日期保留）
        date_groups = {}
        for item in filtered:
            date_iso = item["date_iso"]
            if date_iso not in date_groups:
                date_groups[date_iso] = []
            date_groups[date_iso].append(item)

        # 每个日期只保留第一次出现
        deduplicated = []
        for date_iso, group in date_groups.items():
            # 保留位置最早的
            first = min(group, key=lambda x: x["position"][0])
            deduplicated.append(first)

        return deduplicated

    def _positions_overlap(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """检查两个位置是否重叠"""
        start1, end1 = pos1
        start2, end2 = pos2

        # 完全包含或部分重叠
        return not (end1 <= start2 or end2 <= start1)

    def extract_document_date(
        self,
        text: str,
        filename: str,
        upload_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        提取文档的整体日期（用于作为参考日期）

        优先级：
        1. 文本中的第一个高置信度日期
        2. 文件名中的日期
        3. 上传时间
        """
        # 1. 从文本中提取
        dates = self.extract_dates(text)
        if dates:
            # 取置信度最高的
            best = max(dates, key=lambda x: x["confidence"])
            if best["confidence"] >= 0.9:
                logger.info(f"📅 从文本中提取文档日期: {best['date_iso']}")
                return best["date"]

        # 2. 从文件名中提取
        filename_date = self._extract_date_from_filename(filename)
        if filename_date:
            logger.info(f"📅 从文件名中提取文档日期: {filename_date.strftime('%Y-%m-%d')}")
            return filename_date

        # 3. 使用上传时间
        if upload_time:
            logger.info(f"📅 使用上传时间作为文档日期: {upload_time.strftime('%Y-%m-%d')}")
            return upload_time

        logger.warning("⚠️ 无法确定文档日期")
        return None

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """从文件名中提取日期"""
        # 常见格式：report_20240315.pdf, 访谈_2024-03-15.mp3
        patterns = [
            r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # 20240315, 2024-03-15
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年3月15日
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = map(int, groups)
                        return datetime(year, month, day)
                except ValueError:
                    continue

        return None


# 全局单例
_temporal_extractor = None

def get_temporal_extractor() -> TemporalExtractor:
    """获取时间抽取器单例"""
    global _temporal_extractor
    if _temporal_extractor is None:
        _temporal_extractor = TemporalExtractor()
    return _temporal_extractor
