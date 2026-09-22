"""
知识脉络数据增强服务
自动为 chunks 补充 domain_tags 和 key_entities
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import jieba
import jieba.analyse
from collections import defaultdict
import re

from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity


class KnowledgeEnhancementService:
    """知识增强服务：为 chunks 自动打标签"""

    # 领域关键词库（扩展版）
    DOMAIN_KEYWORDS = {
        "文化传承": {
            "keywords": ["文化", "传统", "习俗", "非遗", "传承", "民俗", "节日", "仪式", "祭祀",
                        "山歌", "刺绣", "蜡染", "银饰", "服饰", "建筑", "手工艺", "技艺", "民族"],
            "subcategories": {
                "山歌传承": ["山歌", "歌谣", "民歌", "唱歌", "传承人", "老人"],
                "手工艺": ["蜡染", "刺绣", "银饰", "编织", "工艺", "图案", "纹样"],
                "传统节庆": ["节日", "春节", "六月六", "三月三", "庆典", "活动"],
                "民族服饰": ["服饰", "服装", "头饰", "绣花", "布依族", "苗族"],
                "传统建筑": ["吊脚楼", "干栏", "石板房", "木结构", "建筑"],
                "饮食文化": ["糯米", "酸汤", "腌菜", "米酒", "传统食物"]
            }
        },
        "经济结构": {
            "keywords": ["经济", "收入", "生计", "产业", "农业", "土地", "种植", "养殖",
                        "打工", "务工", "外出", "市场", "销售", "价格", "成本"],
            "subcategories": {
                "传统农业": ["水稻", "玉米", "种植", "耕地", "农作物", "播种", "收割"],
                "外出务工": ["打工", "外出", "务工", "城市", "返乡", "留守"],
                "土地流转": ["土地", "流转", "承包", "租赁", "合作社"],
                "特色种养": ["茶叶", "中药材", "果树", "养殖", "特色农业"],
                "乡村旅游": ["旅游", "游客", "民宿", "接待", "景点"],
                "电商物流": ["电商", "网店", "物流", "快递", "销售"]
            }
        },
        "社会组织": {
            "keywords": ["村委会", "党支部", "合作社", "协会", "组织", "理事会", "管理",
                        "村民", "群众", "干部", "书记", "主任", "治理", "决策"],
            "subcategories": {
                "村级组织": ["村委会", "党支部", "村干部", "村长", "书记"],
                "经济组织": ["合作社", "协会", "公司", "企业", "经营"],
                "群众组织": ["妇联", "共青团", "老年协会", "志愿者"],
                "传统组织": ["宗族", "家族", "长老", "寨老", "理事会"],
                "外部组织": ["NGO", "基金会", "帮扶单位", "对口支援"]
            }
        },
        "政策支持": {
            "keywords": ["政策", "政府", "支持", "扶贫", "补贴", "项目", "资金", "帮扶",
                        "振兴", "规划", "文件", "通知", "申报", "验收"],
            "subcategories": {
                "乡村振兴": ["乡村振兴", "振兴战略", "示范村", "试点"],
                "脱贫攻坚": ["脱贫", "扶贫", "贫困户", "帮扶", "低保"],
                "文化保护": ["非遗", "保护", "申遗", "传承", "文化遗产"],
                "产业扶持": ["产业", "扶持", "补贴", "贷款", "合作"],
                "基础设施": ["道路", "水利", "电力", "网络", "设施"],
                "教育医疗": ["学校", "医院", "卫生", "教育", "培训"]
            }
        },
        "在地业态": {
            "keywords": ["业态", "经营", "生意", "产业", "商业", "店铺", "工坊", "作坊",
                        "体验", "培训", "研学", "文创", "民宿", "餐饮"],
            "subcategories": {
                "民宿旅游": ["民宿", "客栈", "住宿", "旅游", "游客", "接待"],
                "餐饮服务": ["餐馆", "饭店", "农家乐", "餐饮", "特色美食"],
                "手工艺品": ["工坊", "作坊", "手工艺品", "纪念品", "文创"],
                "研学体验": ["研学", "体验", "培训", "教学", "课程"],
                "农产品销售": ["农产品", "特产", "销售", "市场", "电商"],
                "文化演出": ["演出", "表演", "展示", "活动", "节目"]
            }
        },
        "历史脉络": {
            "keywords": ["历史", "过去", "以前", "祖先", "传说", "故事", "迁徙", "由来",
                        "起源", "发展", "变化", "演变", "沿革"],
            "subcategories": {
                "迁徙历史": ["迁徙", "迁移", "搬迁", "来源", "祖籍"],
                "发展沿革": ["发展", "变化", "演变", "沿革", "历程"],
                "历史事件": ["事件", "战争", "灾害", "改革", "运动"],
                "人物故事": ["人物", "名人", "故事", "传说", "事迹"],
                "历史遗存": ["遗址", "古迹", "文物", "碑刻", "建筑"]
            }
        }
    }

    # 情感词典
    POSITIVE_WORDS = [
        "好", "很好", "不错", "发展", "增长", "改善", "提升", "成功", "繁荣", "兴旺",
        "满意", "高兴", "开心", "幸福", "富裕", "进步", "丰收", "增加", "提高", "改进",
        "美丽", "漂亮", "干净", "整洁", "和谐", "团结", "热情", "欢迎", "支持", "帮助"
    ]

    NEGATIVE_WORDS = [
        "难", "困难", "问题", "减少", "衰退", "流失", "断层", "危机", "贫困", "落后",
        "担心", "害怕", "失望", "不满", "矛盾", "冲突", "破坏", "污染", "浪费", "损失",
        "缺乏", "不足", "短缺", "老化", "破旧", "脏乱", "无序", "混乱", "争执", "纠纷"
    ]

    def __init__(self, db: Session, use_workflow_engine: bool = True):



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        # 加载自定义词典
        self._load_custom_dict()

    def _load_custom_dict(self):
        """加载自定义词典到 jieba"""
        for domain, data in self.DOMAIN_KEYWORDS.items():
            for keyword in data["keywords"]:
                jieba.add_word(keyword)
            for subcat, keywords in data["subcategories"].items():
                jieba.add_word(subcat)
                for kw in keywords:
                    jieba.add_word(kw)

    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词（使用 TF-IDF）"""
        keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
        return keywords

    def classify_dimension(self, text: str) -> tuple[str, str, float]:
        """
        分类文本到领域维度

        返回: (大脉络, 子脉络, 置信度)
        """
        text_lower = text.lower()
        dimension_scores = defaultdict(float)
        subcategory_scores = defaultdict(float)

        # 计算每个领域的匹配分数
        for domain, data in self.DOMAIN_KEYWORDS.items():
            score = 0
            for keyword in data["keywords"]:
                count = text_lower.count(keyword.lower())
                score += count * 2  # 主关键词权重更高

            dimension_scores[domain] = score

            # 计算子类别分数
            for subcat, keywords in data["subcategories"].items():
                subscore = 0
                for kw in keywords:
                    count = text_lower.count(kw.lower())
                    subscore += count
                if subscore > 0:
                    subcategory_scores[(domain, subcat)] = subscore

        # 找到最高分的领域
        if not dimension_scores:
            return ("其他", "未分类", 0.0)

        best_domain = max(dimension_scores.items(), key=lambda x: x[1])
        domain_name = best_domain[0]
        domain_score = best_domain[1]

        # 找到该领域下最高分的子类别
        domain_subcats = {k: v for k, v in subcategory_scores.items() if k[0] == domain_name}
        if domain_subcats:
            best_subcat = max(domain_subcats.items(), key=lambda x: x[1])
            subcat_name = best_subcat[0][1]
            confidence = min(best_subcat[1] / (len(text) / 100), 1.0)  # 归一化
        else:
            subcat_name = "未分类"
            confidence = min(domain_score / (len(text) / 100), 1.0)

        return (domain_name, subcat_name, confidence)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        提取实体（简化版）

        返回: [{"name": "实体名", "type": "类型", "confidence": 0.8}, ...]
        """
        entities = []

        # 使用分词提取名词性实体
        words = jieba.posseg.cut(text)
        for word, flag in words:
            # nr: 人名, ns: 地名, nt: 机构名, nz: 其他专有名词
            if flag in ['nr', 'ns', 'nt', 'nz'] and len(word) >= 2:
                entity_type = {
                    'nr': 'person',
                    'ns': 'location',
                    'nt': 'organization',
                    'nz': 'concept'
                }.get(flag, 'other')

                entities.append({
                    "name": word,
                    "type": entity_type,
                    "confidence": 0.7
                })

        # 去重
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity["name"] not in seen:
                seen.add(entity["name"])
                unique_entities.append(entity)

        return unique_entities[:10]  # 最多返回 10 个

    def calculate_emotion(self, text: str) -> float:
        """
        计算情感极性（-1 到 1）

        返回: 情感得分
        """
        positive_count = sum(text.count(word) for word in self.POSITIVE_WORDS)
        negative_count = sum(text.count(word) for word in self.NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    def enrich_chunk(self, chunk: DocumentChunk) -> bool:
        """
        增强单个 chunk 的数据

        返回: 是否有更新
        """
        if not chunk.text:
            return False

        updated = False

        # 1. 提取领域标签
        if not chunk.domain_tags or chunk.domain_tags == []:
            dimension, subcategory, confidence = self.classify_dimension(chunk.text)

            chunk.domain_tags = [{
                "category": dimension,
                "subcategory": subcategory,
                "confidence": confidence
            }]
            chunk.primary_domain = dimension
            updated = True

        # 2. 提取实体
        if not chunk.key_entities or chunk.key_entities == []:
            entities = self.extract_entities(chunk.text)
            if entities:
                chunk.key_entities = entities
                updated = True

        # 3. 提取时空上下文（简化版）
        if not chunk.temporal_context:
            # 提取时间相关词
            time_patterns = [
                r'\d{4}年', r'\d+月', r'春节', r'过年', r'以前', r'现在',
                r'去年', r'今年', r'明年', r'最近', r'当时'
            ]
            for pattern in time_patterns:
                match = re.search(pattern, chunk.text)
                if match:
                    chunk.temporal_context = match.group()
                    updated = True
                    break

        if not chunk.spatial_context:
            # 提取地点相关词
            spatial_keywords = ['村', '寨', '镇', '县', '市', '贵州', '云南', '广西']
            for keyword in spatial_keywords:
                if keyword in chunk.text:
                    # 提取前后文作为空间上下文
                    idx = chunk.text.find(keyword)
                    start = max(0, idx - 5)
                    end = min(len(chunk.text), idx + len(keyword) + 5)
                    chunk.spatial_context = chunk.text[start:end]
                    updated = True
                    break

        return updated

    def enrich_project_chunks(self, project_id: int, batch_size: int = 100) -> Dict[str, int]:
        """
        批量增强项目的所有 chunks

        返回: 统计信息
        """
        stats = {
            "total": 0,
            "enriched": 0,
            "skipped": 0
        }

        # 分批处理
        offset = 0
        while True:
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project_id
            ).offset(offset).limit(batch_size).all()

            if not chunks:
                break

            for chunk in chunks:
                stats["total"] += 1
                if self.enrich_chunk(chunk):
                    stats["enriched"] += 1
                else:
                    stats["skipped"] += 1

            # 提交批次
            self.db.commit()
            offset += batch_size

        return stats

    def create_sample_chunks_if_empty(self, project_id: int) -> int:
        """
        如果项目没有 chunks，创建示例数据

        返回: 创建的 chunks 数量
        """
        existing_count = self.db.query(func.count(DocumentChunk.id)).filter(
            DocumentChunk.project_id == project_id
        ).scalar()

        if existing_count > 0:
            return 0

        # 示例文本数据
        sample_texts = [
            "布依族山歌是我们村最重要的文化遗产，老一辈人都会唱，但现在年轻人都外出打工了，很少有人愿意学。传承人王大爷今年已经68岁了，他担心这门技艺会失传。",
            "村里的蜡染工艺有300多年历史，图案精美，色彩独特。最近政府支持我们成立了蜡染合作社，产品销售到了城市，收入比以前好多了。",
            "我们村主要种植水稻和玉米，每年收入不高。很多年轻人选择外出务工，留在村里的大多是老人和小孩。土地流转后，一些农户的收入有所增加。",
            "村委会和党支部组织得很好，每月都开村民大会，讨论村里的大事。去年成立了旅游合作社，大家都很支持，现在村里来的游客越来越多。",
            "国家的乡村振兴政策对我们帮助很大，修了新路，建了文化广场，还给蜡染传承人发补贴。现在村里环境好了，游客也愿意来了。",
            "我们村开了几家民宿，生意不错。每到周末和节假日都有游客来体验布依族文化，品尝特色美食。民宿老板说，旺季一个月能赚一万多。",
            "村里有个传说，说是300年前祖先从贵阳迁徙过来的。那时候这里还是荒山，后来慢慢开垦出了田地，建起了村寨。老人们还记得那些故事。",
            "春节和六月六是村里最热闹的节日。春节全村人聚在一起唱山歌、跳舞，六月六则要祭祀祖先，感谢丰收。这些传统一直保留到现在。",
            "最近村里搞研学旅游，城里的学生来这里学习蜡染、体验农耕文化。老师们说，这样的体验很有意义，孩子们都很喜欢。",
            "村里的环境污染是个问题，有些农户用的化肥太多，小河的水质变差了。村委会正在想办法，推广有机农业，希望能改善环境。",
            "年轻人越来越少，留守儿童和空巢老人的问题比较突出。村里虽然有了产业，但吸引年轻人回来还需要更多的机会和更好的待遇。",
            "我们在淘宝上开了网店，卖村里的蜡染产品和农特产品。刚开始不太会运营，后来请了专业人士培训，现在每个月都有稳定的订单。"
        ]

        created_count = 0
        for idx, text in enumerate(sample_texts):
            chunk_id = f"sample_chunk_{project_id}_{idx}"

            # 分类和提取实体
            dimension, subcategory, confidence = self.classify_dimension(text)
            entities = self.extract_entities(text)

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=1,  # 假设有一个默认文档
                project_id=project_id,
                chunk_index=idx,
                text=text,
                text_length=len(text),
                legacy_chunk_text=text,
                legacy_chunk_size=len(text),
                domain_tags=[{
                    "category": dimension,
                    "subcategory": subcategory,
                    "confidence": confidence
                }],
                key_entities=entities,
                primary_domain=dimension
            )

            self.db.add(chunk)
            created_count += 1

        self.db.commit()
        return created_count
