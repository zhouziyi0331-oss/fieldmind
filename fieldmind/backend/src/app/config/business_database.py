"""
在地业态数据库配置
包含现有业态和可能业态的完整推演规则
"""

# ==================== 现有业态关键词库（扩展版）====================

EXISTING_BUSINESS_DATABASE = {
    "传统农业": {
        "keywords": ["水稻", "玉米", "种植", "耕地", "农作物", "播种", "收割", "农田", "农业", "庄稼"],
        "description": "以山地种植为主的传统农业生产，主要种植水稻、玉米等粮食作物",
        "sustainability_factors": {
            "positive": ["政府补贴", "合作社", "技术支持", "市场稳定"],
            "negative": ["劳动力老龄化", "收益低", "年轻人外流", "土地碎片化"]
        }
    },
    "蜡染手工艺": {
        "keywords": ["蜡染", "刺绣", "手工艺", "传统工艺", "纹样", "图案", "染料", "蜡画", "织布"],
        "description": "传承的传统手工艺技能，具有民族特色和文化价值",
        "sustainability_factors": {
            "positive": ["非遗保护", "文化价值", "旅游需求", "政府支持"],
            "negative": ["传承人老龄化", "年轻人不愿学", "市场有限", "竞争激烈"]
        }
    },
    "外出务工": {
        "keywords": ["打工", "外出", "务工", "城市", "返乡", "留守", "收入", "出去", "工作"],
        "description": "年轻劳动力外出务工现象，是当前主要收入来源之一",
        "sustainability_factors": {
            "positive": ["收入稳定", "开阔眼界", "积累经验", "汇款回家"],
            "negative": ["留守问题", "村庄空心化", "家庭分离", "文化断层"]
        }
    },
    "民宿旅游": {
        "keywords": ["民宿", "旅游", "游客", "住宿", "接待", "景点", "客栈", "体验"],
        "description": "乡村旅游和民宿经营，依托自然和文化资源",
        "sustainability_factors": {
            "positive": ["旅游热潮", "政策支持", "收入可观", "带动就业"],
            "negative": ["季节性强", "投资成本", "管理要求", "同质化竞争"]
        }
    },
    "传统节庆": {
        "keywords": ["节日", "庆典", "祭祀", "仪式", "传统活动", "民俗", "春节", "六月六"],
        "description": "传统节庆活动的保留与传承，是文化认同的重要载体",
        "sustainability_factors": {
            "positive": ["文化认同", "社区凝聚", "旅游价值", "非遗保护"],
            "negative": ["年轻人参与少", "仪式简化", "商业化倾向", "成本增加"]
        }
    },
    "特色种养": {
        "keywords": ["茶叶", "中药材", "果树", "养殖", "特色", "有机", "绿色"],
        "description": "特色农产品种植和养殖，具有较高经济价值",
        "sustainability_factors": {
            "positive": ["市场需求", "附加值高", "政策扶持", "生态友好"],
            "negative": ["技术要求", "市场波动", "销售渠道", "品牌建设"]
        }
    },
    "农家乐": {
        "keywords": ["农家乐", "餐饮", "饭店", "美食", "特色菜", "体验"],
        "description": "提供餐饮和休闲体验的农家乐经营",
        "sustainability_factors": {
            "positive": ["需求稳定", "门槛较低", "文化体验", "地方特色"],
            "negative": ["卫生要求", "竞争激烈", "淡旺季明显", "食材成本"]
        }
    },
    "电商销售": {
        "keywords": ["电商", "网店", "淘宝", "拼多多", "直播", "销售", "快递"],
        "description": "通过电商平台销售农特产品和手工艺品",
        "sustainability_factors": {
            "positive": ["市场广阔", "直接销售", "利润提高", "品牌建设"],
            "negative": ["运营难度", "物流成本", "竞争激烈", "需要培训"]
        }
    }
}


# ==================== 可能业态推演规则库（扩展版）====================

POTENTIAL_BUSINESS_RULES = {
    "山歌": {
        "trigger_frequency": 5,  # 至少出现5次
        "potential_businesses": [
            {
                "name": "山歌研学营",
                "description": "以布依族山歌为核心的文化研学体验，面向中小学生和文化爱好者",
                "base_score": 82,
                "required_keywords": ["山歌", "传承", "文化"],
                "supporting_factors": ["传承人", "传统", "非遗", "学习", "体验", "教育"],
                "implementation_difficulty": "中等",
                "investment_range": "5-15万元",
                "return_cycle": "1-2年",
                "key_resources": ["传承人", "场地", "课程设计", "安全保障"]
            },
            {
                "name": "山歌×文创产品",
                "description": "将山歌元素融入文创产品设计，包括音乐盒、明信片、服饰等",
                "base_score": 71,
                "required_keywords": ["山歌", "文化", "产品"],
                "supporting_factors": ["手工艺", "设计", "产品", "文创", "旅游"],
                "implementation_difficulty": "较高",
                "investment_range": "10-30万元",
                "return_cycle": "2-3年",
                "key_resources": ["设计师", "生产能力", "销售渠道", "品牌运营"]
            },
            {
                "name": "山歌主题民宿",
                "description": "融入山歌文化的特色民宿，提供沉浸式文化体验",
                "base_score": 68,
                "required_keywords": ["山歌", "民宿", "文化"],
                "supporting_factors": ["旅游", "住宿", "体验", "建筑", "服务"],
                "implementation_difficulty": "较高",
                "investment_range": "20-50万元",
                "return_cycle": "3-5年",
                "key_resources": ["房屋改造", "服务团队", "文化策划", "营销推广"]
            },
            {
                "name": "山歌音乐节",
                "description": "定期举办山歌音乐节，打造地方文化品牌",
                "base_score": 65,
                "required_keywords": ["山歌", "活动", "节日"],
                "supporting_factors": ["表演", "节日", "游客", "宣传", "组织"],
                "implementation_difficulty": "高",
                "investment_range": "30-100万元",
                "return_cycle": "3-5年",
                "key_resources": ["活动策划", "场地设施", "演员团队", "赞助支持"]
            }
        ]
    },
    "蜡染": {
        "trigger_frequency": 5,
        "potential_businesses": [
            {
                "name": "蜡染工坊体验",
                "description": "游客亲手体验蜡染制作过程，带走自己的作品",
                "base_score": 78,
                "required_keywords": ["蜡染", "手工艺", "体验"],
                "supporting_factors": ["传承人", "体验", "旅游", "工坊", "教学"],
                "implementation_difficulty": "中等",
                "investment_range": "3-10万元",
                "return_cycle": "1-2年",
                "key_resources": ["传承人指导", "工坊场地", "材料工具", "安全管理"]
            },
            {
                "name": "蜡染文创产品线",
                "description": "现代设计与传统蜡染结合，开发时尚文创产品",
                "base_score": 75,
                "required_keywords": ["蜡染", "产品", "设计"],
                "supporting_factors": ["设计", "市场", "品牌", "创新", "时尚"],
                "implementation_difficulty": "较高",
                "investment_range": "15-40万元",
                "return_cycle": "2-3年",
                "key_resources": ["设计团队", "生产供应链", "品牌营销", "销售渠道"]
            },
            {
                "name": "蜡染技艺培训班",
                "description": "面向年轻人的蜡染技艺传承培训，提供就业机会",
                "base_score": 70,
                "required_keywords": ["蜡染", "传承", "培训"],
                "supporting_factors": ["年轻人", "教育", "技能", "就业", "收入"],
                "implementation_difficulty": "中等",
                "investment_range": "5-15万元",
                "return_cycle": "2-3年",
                "key_resources": ["培训场地", "传承人师资", "培训教材", "就业对接"]
            },
            {
                "name": "蜡染艺术馆",
                "description": "展示蜡染历史和精品，提供文化教育和旅游服务",
                "base_score": 65,
                "required_keywords": ["蜡染", "展示", "文化"],
                "supporting_factors": ["历史", "艺术", "展览", "旅游", "教育"],
                "implementation_difficulty": "高",
                "investment_range": "50-150万元",
                "return_cycle": "5-10年",
                "key_resources": ["场馆建设", "藏品征集", "策展能力", "运营管理"]
            }
        ]
    },
    "节庆": {
        "trigger_frequency": 5,
        "potential_businesses": [
            {
                "name": "节庆文化旅游",
                "description": "打造特色节庆旅游品牌，吸引游客体验传统文化",
                "base_score": 80,
                "required_keywords": ["节日", "庆典", "旅游"],
                "supporting_factors": ["游客", "活动", "体验", "文化", "宣传"],
                "implementation_difficulty": "中等",
                "investment_range": "20-60万元",
                "return_cycle": "2-3年",
                "key_resources": ["活动策划", "配套设施", "宣传推广", "接待能力"]
            },
            {
                "name": "节庆活动策划服务",
                "description": "专业化的传统节庆活动组织和策划服务",
                "base_score": 68,
                "required_keywords": ["节日", "活动", "策划"],
                "supporting_factors": ["组织", "策划", "运营", "服务", "专业"],
                "implementation_difficulty": "较高",
                "investment_range": "10-30万元",
                "return_cycle": "2-3年",
                "key_resources": ["策划团队", "执行能力", "资源整合", "客户网络"]
            },
            {
                "name": "节庆文化产品",
                "description": "开发节庆相关的文化产品和纪念品",
                "base_score": 63,
                "required_keywords": ["节日", "产品", "文化"],
                "supporting_factors": ["纪念品", "特色", "销售", "设计"],
                "implementation_difficulty": "中等",
                "investment_range": "5-20万元",
                "return_cycle": "1-2年",
                "key_resources": ["产品设计", "生产渠道", "销售网络", "品牌建设"]
            }
        ]
    },
    "传承人": {
        "trigger_frequency": 3,
        "potential_businesses": [
            {
                "name": "非遗传承工作室",
                "description": "建立传承人工作室，提供技艺展示、教学和产品销售",
                "base_score": 76,
                "required_keywords": ["传承人", "非遗", "工作室"],
                "supporting_factors": ["技艺", "教学", "展示", "销售", "文化"],
                "implementation_difficulty": "中等",
                "investment_range": "8-25万元",
                "return_cycle": "2-3年",
                "key_resources": ["传承人", "工作场地", "学员招募", "产品开发"]
            },
            {
                "name": "传承人直播带货",
                "description": "传承人通过直播展示技艺并销售产品",
                "base_score": 72,
                "required_keywords": ["传承人", "销售", "网络"],
                "supporting_factors": ["直播", "电商", "网络", "宣传", "产品"],
                "implementation_difficulty": "中等",
                "investment_range": "2-8万元",
                "return_cycle": "6个月-1年",
                "key_resources": ["直播设备", "运营团队", "产品供应", "流量运营"]
            }
        ]
    },
    "民宿": {
        "trigger_frequency": 3,
        "potential_businesses": [
            {
                "name": "主题民宿集群",
                "description": "打造不同主题的民宿集群，形成规模效应",
                "base_score": 75,
                "required_keywords": ["民宿", "旅游", "住宿"],
                "supporting_factors": ["主题", "集群", "规模", "管理", "服务"],
                "implementation_difficulty": "高",
                "investment_range": "100-300万元",
                "return_cycle": "3-5年",
                "key_resources": ["多处房产", "统一管理", "品牌建设", "营销推广"]
            },
            {
                "name": "民宿+研学基地",
                "description": "民宿与研学教育结合，提供食宿+课程一体化服务",
                "base_score": 73,
                "required_keywords": ["民宿", "研学", "教育"],
                "supporting_factors": ["学生", "课程", "体验", "教学", "安全"],
                "implementation_difficulty": "较高",
                "investment_range": "30-80万元",
                "return_cycle": "2-4年",
                "key_resources": ["住宿设施", "课程开发", "师资团队", "学校对接"]
            }
        ]
    },
    "农产品": {
        "trigger_frequency": 5,
        "potential_businesses": [
            {
                "name": "农产品品牌化运营",
                "description": "打造地方农产品品牌，开拓高端市场",
                "base_score": 77,
                "required_keywords": ["农产品", "销售", "品牌"],
                "supporting_factors": ["特色", "品质", "认证", "渠道", "营销"],
                "implementation_difficulty": "较高",
                "investment_range": "20-60万元",
                "return_cycle": "2-3年",
                "key_resources": ["品牌设计", "质量认证", "营销团队", "销售渠道"]
            },
            {
                "name": "农产品深加工",
                "description": "对农产品进行深加工，提高附加值",
                "base_score": 74,
                "required_keywords": ["农产品", "加工", "产品"],
                "supporting_factors": ["加工", "技术", "设备", "市场", "标准"],
                "implementation_difficulty": "高",
                "investment_range": "50-150万元",
                "return_cycle": "3-5年",
                "key_resources": ["加工设备", "技术团队", "食品认证", "销售网络"]
            },
            {
                "name": "农产品订单农业",
                "description": "与企业或平台合作，发展订单式农业",
                "base_score": 70,
                "required_keywords": ["农产品", "合作", "订单"],
                "supporting_factors": ["合作社", "合同", "稳定", "收入", "技术"],
                "implementation_difficulty": "中等",
                "investment_range": "10-30万元",
                "return_cycle": "1-2年",
                "key_resources": ["合作企业", "种植规模", "质量保障", "物流配送"]
            }
        ]
    },
    "合作社": {
        "trigger_frequency": 3,
        "potential_businesses": [
            {
                "name": "综合型合作社升级",
                "description": "整合多种业态，建立综合服务型合作社",
                "base_score": 78,
                "required_keywords": ["合作社", "组织", "服务"],
                "supporting_factors": ["整合", "规模", "管理", "服务", "品牌"],
                "implementation_difficulty": "高",
                "investment_range": "50-200万元",
                "return_cycle": "3-5年",
                "key_resources": ["组织能力", "管理团队", "资金支持", "政策对接"]
            }
        ]
    }
}


# ==================== 业态可行性评估权重配置 ====================

FEASIBILITY_WEIGHTS = {
    "keyword_frequency": 0.25,      # 关键词频次权重
    "emotion_score": 0.20,          # 情感倾向权重
    "policy_support": 0.25,         # 政策支持权重
    "resource_availability": 0.30   # 资源可用性权重
}


# ==================== 可持续性评估权重配置 ====================

SUSTAINABILITY_WEIGHTS = {
    "coverage": 0.35,    # 覆盖度权重
    "emotion": 0.35,     # 情感倾向权重
    "trend": 0.30        # 时间趋势权重
}
