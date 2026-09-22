"""
关键词分类配置
根据田野调查的实际需求定制
"""

from enum import Enum
from typing import Dict, List


class KeywordCategory(str, Enum):
    """关键词分类"""
    # 基础分类
    PERSON = "人物"           # 村民、干部、访谈对象
    LOCATION = "地点"         # 村庄、地标、区域
    EVENT = "事件"           # 会议、活动、重要事件
    ORGANIZATION = "组织"     # 村委会、合作社
    THEME = "主题"           # 土地、选举、经济

    # 生活类
    CLOTHING = "衣"          # 服饰、穿着
    FOOD = "食"             # 饮食、食物
    HOUSING = "住"          # 居住、房屋
    TRANSPORTATION = "行"    # 交通、出行

    # 遗产类
    NATURAL_HERITAGE = "自然遗产"    # 自然景观、生态
    CULTURAL_HERITAGE = "文化遗产"   # 人文遗产
    INTANGIBLE_HERITAGE = "非物质文化遗产"  # 非遗、传统技艺

    # 支持类
    ASSISTANCE = "帮助支持"   # 获得的帮助、资源
    SUPPORTER = "支持人物"    # 提供支持的人物/组织


# 分类描述和关键词示例
CATEGORY_INFO: Dict[str, Dict] = {
    KeywordCategory.PERSON: {
        "description": "村民、干部、访谈对象等人物",
        "examples": ["村长", "书记", "村民", "老人", "年轻人"],
        "extraction_hints": ["职务", "身份", "姓名", "称呼"]
    },
    KeywordCategory.LOCATION: {
        "description": "村庄、地标、区域等地理位置",
        "examples": ["XX村", "村委会", "祠堂", "广场", "田地"],
        "extraction_hints": ["地名", "建筑", "场所"]
    },
    KeywordCategory.EVENT: {
        "description": "会议、活动、重要事件",
        "examples": ["村民大会", "选举", "节日庆典", "纠纷", "改革"],
        "extraction_hints": ["会议", "活动", "仪式", "事件"]
    },
    KeywordCategory.ORGANIZATION: {
        "description": "村委会、合作社等组织机构",
        "examples": ["村委会", "合作社", "互助组", "理事会"],
        "extraction_hints": ["委员会", "社", "会", "组织"]
    },
    KeywordCategory.THEME: {
        "description": "土地、选举、经济等主题",
        "examples": ["土地流转", "选举制度", "集体经济", "乡村振兴"],
        "extraction_hints": ["制度", "政策", "问题", "发展"]
    },
    KeywordCategory.CLOTHING: {
        "description": "服饰、穿着、传统服装",
        "examples": ["传统服饰", "民族服装", "工作服", "节日服装"],
        "extraction_hints": ["衣服", "服饰", "穿着", "打扮"]
    },
    KeywordCategory.FOOD: {
        "description": "饮食、食物、饮食习惯",
        "examples": ["传统美食", "节日食品", "日常饮食", "特色小吃"],
        "extraction_hints": ["食物", "吃", "饮食", "菜肴"]
    },
    KeywordCategory.HOUSING: {
        "description": "居住、房屋、建筑",
        "examples": ["传统民居", "新房", "老房子", "住宅"],
        "extraction_hints": ["房屋", "住", "居住", "建筑"]
    },
    KeywordCategory.TRANSPORTATION: {
        "description": "交通、出行方式",
        "examples": ["道路", "公交", "摩托车", "步行"],
        "extraction_hints": ["交通", "出行", "道路", "车辆"]
    },
    KeywordCategory.NATURAL_HERITAGE: {
        "description": "自然景观、生态环境、自然资源",
        "examples": ["古树", "河流", "山脉", "保护区", "生态"],
        "extraction_hints": ["自然", "景观", "环境", "生态", "资源"]
    },
    KeywordCategory.CULTURAL_HERITAGE: {
        "description": "人文遗产、历史遗迹、文物",
        "examples": ["古建筑", "祠堂", "牌坊", "文物", "历史遗迹"],
        "extraction_hints": ["文化", "历史", "遗产", "古迹", "传统"]
    },
    KeywordCategory.INTANGIBLE_HERITAGE: {
        "description": "非物质文化遗产、传统技艺、民俗",
        "examples": ["传统技艺", "民间艺术", "节日习俗", "口述传统"],
        "extraction_hints": ["非遗", "技艺", "传统", "习俗", "民俗"]
    },
    KeywordCategory.ASSISTANCE: {
        "description": "获得的帮助、支持、资源",
        "examples": ["政府补贴", "项目支持", "资金援助", "技术指导"],
        "extraction_hints": ["帮助", "支持", "援助", "补贴", "项目"]
    },
    KeywordCategory.SUPPORTER: {
        "description": "提供支持的人物或组织",
        "examples": ["扶贫干部", "专家", "志愿者", "上级单位"],
        "extraction_hints": ["提供", "帮助者", "支持者", "援助方"]
    },
}


# 分类权重（用于自动分类）
CATEGORY_WEIGHTS = {
    KeywordCategory.PERSON: 1.2,              # 人物很重要
    KeywordCategory.LOCATION: 1.1,            # 地点重要
    KeywordCategory.EVENT: 1.3,               # 事件最重要
    KeywordCategory.ORGANIZATION: 1.0,
    KeywordCategory.THEME: 1.2,               # 主题重要
    KeywordCategory.CLOTHING: 0.8,
    KeywordCategory.FOOD: 0.8,
    KeywordCategory.HOUSING: 0.8,
    KeywordCategory.TRANSPORTATION: 0.7,
    KeywordCategory.NATURAL_HERITAGE: 1.0,
    KeywordCategory.CULTURAL_HERITAGE: 1.1,   # 遗产重要
    KeywordCategory.INTANGIBLE_HERITAGE: 1.1,
    KeywordCategory.ASSISTANCE: 0.9,
    KeywordCategory.SUPPORTER: 0.9,
}


def get_all_categories() -> List[str]:
    """获取所有分类"""
    return [cat.value for cat in KeywordCategory]


def get_category_description(category: str) -> str:
    """获取分类描述"""
    return CATEGORY_INFO.get(category, {}).get("description", "")


def get_category_examples(category: str) -> List[str]:
    """获取分类示例"""
    return CATEGORY_INFO.get(category, {}).get("examples", [])


def get_extraction_hints(category: str) -> List[str]:
    """获取提取提示词"""
    return CATEGORY_INFO.get(category, {}).get("extraction_hints", [])
