"""
生计生态Skill - 分析生计方式、收入来源与生态环境
"""
import logging

logger = logging.getLogger(__name__)

SKILL_DEFINITION = {
    "id": "livelihood_ecology",
    "name": "生计生态分析",
    "description": "生计方式、收入来源与生态环境关系分析",
    "dimensions": {
        "income_sources": {
            "name": "收入来源",
            "keywords": ["打工", "务工", "种植", "养殖", "经营", "生意", "收入", "工资", "补贴"]
        },
        "agricultural_practice": {
            "name": "农业实践",
            "keywords": ["耕地", "种植", "收成", "庄稼", "农作物", "播种", "收割", "灌溉"]
        },
        "ecological_impact": {
            "name": "生态影响",
            "keywords": ["环境", "污染", "生态", "水源", "森林", "保护", "退耕", "绿化"]
        },
        "resource_dependence": {
            "name": "资源依赖",
            "keywords": ["山林", "水资源", "土地", "自然", "资源", "采集", "利用"]
        }
    }
}

def analyze(content: str, metadata: dict = None) -> dict:
    """执行生计生态分析"""
    try:
        result = {"skill_name": SKILL_DEFINITION["name"], "dimensions": {}}
        
        for dim_id, dim_info in SKILL_DEFINITION["dimensions"].items():
            matched_count = 0
            contexts = []
            
            for keyword in dim_info["keywords"]:
                if keyword in content:
                    matched_count += 1
                    sentences = content.split('。')
                    for sent in sentences:
                        if keyword in sent and len(sent) > 5:
                            contexts.append(sent.strip() + '。')
                            if len(contexts) >= 3:
                                break
                    if len(contexts) >= 3:
                        break
            
            result["dimensions"][dim_id] = {
                "name": dim_info["name"],
                "matched_count": matched_count,
                "contexts": contexts[:3]
            }
        
        return result
    except Exception as e:
        logger.error(f"生计生态分析失败: {e}")
        return None
