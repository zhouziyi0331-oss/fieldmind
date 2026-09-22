"""
实体分类服务 - 链路16：衣食住行分类

将提取的实体分类到田野调查的核心维度：
- 衣（clothing）：服饰、穿着、纺织
- 食（food）：饮食、烹饪、食材
- 住（housing）：建筑、居住、村落
- 行（transportation）：交通、迁徙、道路
- 民歌（folk_song）：歌谣、音乐、传统艺术
- 其他（other）
"""
from typing import Dict, List, Optional
import re


class EntityCategorizer:
    """实体分类器"""
    def __init__(self, use_workflow_engine: bool = True):

        # 分类关键词字典
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.category_keywords = {
            "food": [
                # 食材
                "猪肉", "牛肉", "羊肉", "鸡", "鸭", "鱼", "虾", "豆腐", "米", "面", "菜",
                "杀猪菜", "腊肉", "香肠", "豆瓣酱", "泡菜", "酸菜", "糯米", "玉米", "红薯",
                # 烹饪
                "做菜", "烹饪", "炒", "煮", "蒸", "炖", "腌", "晒", "熏", "烤",
                # 饮食习惯
                "吃饭", "早餐", "午饭", "晚饭", "宴席", "酒席", "喝酒", "茶",
                # 器具
                "锅", "碗", "筷子", "勺子", "菜刀", "砧板", "灶台"
            ],
            "clothing": [
                # 服饰
                "衣服", "裤子", "裙子", "鞋", "帽子", "围巾", "腰带", "头巾", "绣花",
                "苗服", "侗服", "民族服装", "传统服饰", "蜡染", "银饰", "花边",
                # 制作
                "纺织", "织布", "刺绣", "染色", "缝纫", "做衣服",
                # 材料
                "布料", "丝绸", "棉花", "麻", "毛线"
            ],
            "housing": [
                # 建筑
                "房子", "屋", "吊脚楼", "木楼", "瓦房", "茅草房", "祠堂", "庙", "寨门",
                "村", "村寨", "寨子", "院子", "堂屋", "厨房", "卧室", "阁楼",
                # 建设
                "盖房", "修房", "建房", "砌墙", "铺地", "装修", "维修",
                # 材料
                "木头", "竹子", "石头", "瓦", "砖", "泥土",
                # 风水
                "风水", "朝向", "选址"
            ],
            "transportation": [
                # 交通工具
                "路", "桥", "车", "船", "马", "牛车", "轿子", "步行",
                # 迁徙
                "搬家", "迁移", "移民", "外出", "回家", "进城", "下乡",
                # 地理
                "山路", "石板路", "小路", "大路", "公路", "铁路", "河"
            ],
            "folk_song": [
                # 民歌
                "歌", "唱歌", "山歌", "情歌", "酒歌", "劳动号子", "哭嫁歌", "丧歌",
                "苗歌", "侗歌", "飞歌", "游方歌",
                # 音乐
                "芦笙", "唢呐", "鼓", "锣", "二胡", "琵琶", "笛子",
                # 舞蹈
                "跳舞", "芦笙舞", "摆手舞", "踩歌堂",
                # 传统艺术
                "戏曲", "说书", "讲古", "唱词"
            ],
            "ritual": [
                # 仪式
                "婚礼", "葬礼", "祭祀", "拜年", "过节", "春节", "清明", "端午", "中秋",
                "祭祖", "敬神", "还愿", "祈福", "驱邪",
                # 人生仪礼
                "满月", "周岁", "成人礼", "订婚", "出嫁", "办丧事"
            ],
            "kinship": [
                # 家庭关系
                "父亲", "母亲", "儿子", "女儿", "哥哥", "姐姐", "弟弟", "妹妹",
                "爷爷", "奶奶", "外公", "外婆", "叔叔", "伯伯", "姑姑", "舅舅", "姨妈",
                "老公", "老婆", "丈夫", "妻子", "孙子", "孙女",
                # 宗族
                "家族", "宗族", "房族", "同姓", "堂兄弟", "表兄弟", "族长", "长辈"
            ]
        }

    def categorize(self, entity_name: str, entity_type: str, context: str = "") -> Optional[str]:
        """
        对实体进行分类

        Args:
            entity_name: 实体名称
            entity_type: 实体类型（person/location/concept等）
            context: 上下文文本（用于更准确的分类）

        Returns:
            分类标签 | None
        """
        text = f"{entity_name} {context}"

        # 统计每个分类的匹配分数
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # 在实体名称中出现权重更高
                    if keyword in entity_name:
                        score += 3
                    else:
                        score += 1
            scores[category] = score

        # 返回得分最高的分类（必须>0）
        if scores:
            max_category = max(scores, key=scores.get)
            if scores[max_category] > 0:
                return max_category

        return None

    def categorize_batch(
        self,
        entities: List[Dict],
        context_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        批量分类

        Args:
            entities: 实体列表 [{"name": "杀猪菜", "type": "concept"}]
            context_map: 实体名称 -> 上下文文本

        Returns:
            实体名称 -> 分类标签
        """
        context_map = context_map or {}
        result = {}

        for entity in entities:
            name = entity.get("name", "")
            entity_type = entity.get("type", "")
            context = context_map.get(name, "")

            category = self.categorize(name, entity_type, context)
            if category:
                result[name] = category

        return result

    def get_category_display_name(self, category: str) -> str:
        """获取分类的中文显示名称"""
        display_names = {
            "food": "食",
            "clothing": "衣",
            "housing": "住",
            "transportation": "行",
            "folk_song": "民歌",
            "ritual": "仪式",
            "kinship": "亲属"
        }
        return display_names.get(category, "其他")


# 全局单例
_entity_categorizer = None

def get_entity_categorizer() -> EntityCategorizer:
    """获取实体分类器单例"""
    global _entity_categorizer
    if _entity_categorizer is None:
        _entity_categorizer = EntityCategorizer()
    return _entity_categorizer
