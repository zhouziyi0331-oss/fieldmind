"""
田野维度分类 Agent
分析材料的田野调查维度
"""
from typing import Dict, List, Any, Optional
import logging
from app.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("field_dimension")
class FieldDimensionAgent:
    """
    田野维度分类 Agent

    功能：
    - 识别材料的田野调查类型
    - 提取田野工作特征
    - 分类田野数据维度
    """

    def __init__(self):
        self.name = "field_dimension"
        self.description = "田野维度分类和特征提取"

        # 田野维度定义
        self.dimensions = {
            "participant_observation": {
                "name": "参与式观察",
                "keywords": ["观察", "参与", "体验", "现场", "互动", "活动"],
                "features": ["时间", "地点", "人物", "行为", "互动方式"]
            },
            "interview": {
                "name": "访谈调查",
                "keywords": ["访谈", "采访", "对话", "口述", "讲述", "回忆"],
                "features": ["受访者", "问题", "回答", "态度", "情感"]
            },
            "survey": {
                "name": "问卷调查",
                "keywords": ["问卷", "调查", "统计", "样本", "数据", "比例"],
                "features": ["样本量", "问题设计", "数据分布", "统计结果"]
            },
            "field_notes": {
                "name": "田野笔记",
                "keywords": ["笔记", "记录", "日志", "手记", "备忘", "随记"],
                "features": ["日期", "地点", "事件", "感想", "发现"]
            },
            "photography": {
                "name": "影像记录",
                "keywords": ["照片", "图片", "影像", "视频", "记录", "拍摄"],
                "features": ["拍摄对象", "时间地点", "场景描述"]
            },
            "artifact_collection": {
                "name": "实物采集",
                "keywords": ["实物", "样本", "收集", "采集", "标本", "物品"],
                "features": ["物品类型", "来源", "特征", "用途", "保存状态"]
            },
            "mapping": {
                "name": "地图绘制",
                "keywords": ["地图", "示意图", "空间", "布局", "路线", "位置"],
                "features": ["空间范围", "标注要素", "比例尺", "方向"]
            },
            "historical_document": {
                "name": "历史文献",
                "keywords": ["文献", "档案", "史料", "记载", "资料", "文书"],
                "features": ["时代", "作者", "内容", "真实性", "价值"]
            }
        }

    async def execute(
        self,
        content: str,
        threshold: float = 0.3,
        return_features: bool = True
    ) -> Dict[str, Any]:
        """
        执行田野维度分类

        Args:
            content: 文本内容
            threshold: 分类阈值
            return_features: 是否返回特征提取结果

        Returns:
            {
                "dimensions": [{"name": str, "score": float, "keywords_found": list}],
                "primary_dimension": str,
                "features": dict (可选)
            }
        """
        logger.info(f"开始田野维度分类 (content_length={len(content)})")

        # 分类所有维度
        dimension_scores = []
        for dim_id, dim_info in self.dimensions.items():
            score = self._calculate_dimension_score(content, dim_info)
            if score >= threshold:
                dimension_scores.append({
                    "id": dim_id,
                    "name": dim_info["name"],
                    "score": score,
                    "keywords_found": self._find_keywords(content, dim_info["keywords"])
                })

        # 按分数排序
        dimension_scores.sort(key=lambda x: x["score"], reverse=True)

        # 确定主要维度
        primary_dimension = dimension_scores[0]["name"] if dimension_scores else "未分类"

        result = {
            "dimensions": dimension_scores,
            "primary_dimension": primary_dimension
        }

        # 提取特征
        if return_features and dimension_scores:
            primary_dim_id = dimension_scores[0]["id"]
            features = self._extract_features(content, self.dimensions[primary_dim_id])
            result["features"] = features

        logger.info(f"田野维度分类完成: primary={primary_dimension}, count={len(dimension_scores)}")
        return result

    def _calculate_dimension_score(self, content: str, dimension: Dict) -> float:
        """计算维度匹配分数"""
        keywords = dimension["keywords"]
        matched = 0

        for keyword in keywords:
            if keyword in content:
                matched += 1

        # 基础分数：匹配关键词占比
        if not keywords:
            return 0.0

        score = matched / len(keywords)

        # 加权：关键词出现频率
        for keyword in keywords:
            count = content.count(keyword)
            if count > 0:
                score += min(count * 0.05, 0.3)  # 最多加 0.3

        return min(score, 1.0)

    def _find_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """查找内容中出现的关键词"""
        found = []
        for keyword in keywords:
            if keyword in content:
                found.append(keyword)
        return found

    def _extract_features(self, content: str, dimension: Dict) -> Dict[str, Any]:
        """提取田野特征"""
        features = {}
        feature_types = dimension.get("features", [])

        for feature_type in feature_types:
            # 根据特征类型提取信息
            if feature_type == "时间":
                features["time"] = self._extract_time(content)
            elif feature_type == "地点":
                features["location"] = self._extract_location(content)
            elif feature_type == "人物":
                features["people"] = self._extract_people(content)
            elif feature_type == "事件":
                features["event"] = self._extract_event(content)
            elif feature_type == "样本量":
                features["sample_size"] = self._extract_numbers(content)
            elif feature_type == "物品类型":
                features["item_type"] = self._extract_items(content)

        return features

    def _extract_time(self, content: str) -> List[str]:
        """提取时间信息（简单规则）"""
        import re
        # 匹配常见时间格式
        patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}年\d{1,2}月',
            r'\d{4}年',
            r'\d{1,2}月\d{1,2}日'
        ]
        times = []
        for pattern in patterns:
            times.extend(re.findall(pattern, content))
        return list(set(times))[:5]  # 最多返回 5 个

    def _extract_location(self, content: str) -> List[str]:
        """提取地点信息（简单规则）"""
        # 简单关键词匹配
        location_indicators = ["村", "镇", "县", "市", "省", "区", "路", "街", "号"]
        locations = []

        sentences = content.split("。")
        for sentence in sentences:
            for indicator in location_indicators:
                if indicator in sentence:
                    # 提取包含地点指示词的短语
                    words = sentence.split()
                    for word in words:
                        if indicator in word:
                            locations.append(word)

        return list(set(locations))[:5]

    def _extract_people(self, content: str) -> List[str]:
        """提取人物信息（简单规则）"""
        # 简单规则：查找称谓
        people_indicators = ["先生", "女士", "老师", "师傅", "阿姨", "大爷", "村民", "居民"]
        people = []

        for indicator in people_indicators:
            if indicator in content:
                people.append(indicator)

        return list(set(people))[:5]

    def _extract_event(self, content: str) -> List[str]:
        """提取事件信息"""
        # 简单规则：提取包含动词的句子片段
        event_verbs = ["举办", "进行", "开展", "组织", "参加", "发生", "发现"]
        events = []

        sentences = content.split("。")
        for sentence in sentences[:3]:  # 只取前 3 句
            for verb in event_verbs:
                if verb in sentence:
                    events.append(sentence.strip())
                    break

        return events

    def _extract_numbers(self, content: str) -> List[str]:
        """提取数字信息"""
        import re
        numbers = re.findall(r'\d+', content)
        return numbers[:5]

    def _extract_items(self, content: str) -> List[str]:
        """提取物品类型"""
        item_keywords = ["工具", "器具", "物品", "用品", "设备", "材料", "产品"]
        items = []

        for keyword in item_keywords:
            if keyword in content:
                items.append(keyword)

        return list(set(items))[:5]

    def get_dimension_info(self, dimension_id: str) -> Optional[Dict[str, Any]]:
        """获取维度信息"""
        return self.dimensions.get(dimension_id)

    def list_dimensions(self) -> List[Dict[str, str]]:
        """列出所有维度"""
        return [
            {"id": dim_id, "name": dim_info["name"]}
            for dim_id, dim_info in self.dimensions.items()
        ]
