"""
在地文创分析服务
使用 Claude Opus 5 深度思考，避免刻板建议
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from anthropic import Anthropic
import os
import json

from app.models.project import ProjectDocument


class CreativeAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze_creative_possibilities(
        self,
        project_id: int,
        keywords: List[str],
        mode: str = "creative"
    ) -> Dict[str, Any]:
        """
        使用 Claude Opus 5 深度思考文创可能性

        核心：避免刻板建议，真正结合在地特色

        Raises:
            ValueError: 缺少必需的配置（ANTHROPIC_API_KEY）
            RuntimeError: API调用失败
        """

        # 0. 验证配置
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY未配置。文创分析功能需要Claude API。"
                "请在环境变量中设置ANTHROPIC_API_KEY。"
            )

        # 1. 从数据库提取项目相关信息
        project_context = await self._get_project_context(project_id, keywords)

        # 2. 构建深度思考 Prompt
        prompt = self._build_creative_prompt(keywords, project_context, mode)

        # 3. 调用 Claude Opus 5
        try:
            response = self.anthropic.messages.create(
                model="claude-opus-4-20250514",  # Opus 5 的实际模型 ID
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 4. 解析和结构化结果
            analysis = self._parse_creative_response(response)

        except Exception as e:
            # 记录错误并抛出异常，让调用方处理
            print(f"文创分析API调用失败: {e}")
            raise RuntimeError(f"文创分析失败: {str(e)}") from e

        return analysis

    def _build_creative_prompt(
        self,
        keywords: List[str],
        context: str,
        mode: str
    ) -> str:
        """
        构建创意分析 Prompt
        """
        keywords_str = "、".join(keywords)

        prompt = f"""
你是一位深谙乡村文化的创意策划专家。现在需要你基于调研数据，为"{keywords_str}"提供**真正有创意、接地气的文创建议**。

## 调研背景
{context}

## 核心要求

### ❌ 避免这些刻板建议：
- 制作XX纪念品、文创产品
- 举办XX表演、展览
- 开发XX旅游路线
- 建设XX文化馆

### ✅ 你应该这样思考：

1. **深度理解在地特色**
   - {keywords_str} 的独特性是什么？
   - 与其他地方的同类事物有何不同？
   - 背后的文化逻辑和生活方式是什么？

2. **寻找创新结合点**
   - 能否与当代年轻人的生活方式结合？
   - 能否与新技术（AR/VR/AI）结合？
   - 能否与其他文化形式跨界？
   - 能否创造新的体验方式？

3. **确保真实可行**
   - 是否尊重当地文化？
   - 是否有实际落地可能？
   - 当地人是否愿意参与？
   - 游客是否真的感兴趣？

## 输出格式

请以 JSON 格式返回分析结果：

```json
{{
  "cultural_elements": [
    {{
      "element": "布依族山歌",
      "uniqueness": "对歌形式独特，即兴创作能力强",
      "cultural_meaning": "社交、情感表达、传承的重要方式"
    }}
  ],
  "creative_possibilities": [
    {{
      "idea": "山歌对唱互动体验",
      "description": "游客学习基本对歌技巧，与当地人现场对唱，AI实时翻译和指导，录制专属山歌作品带走",
      "innovation_point": "从被动观赏到主动参与，从表演到真实社交",
      "feasibility_score": 85,
      "required_resources": ["3-5位当地歌手", "录音设备", "AI翻译系统"],
      "target_audience": "18-35岁年轻人，喜欢社交体验",
      "market_potential": "中高",
      "unique_value": "真正的文化交流，非刻板表演",
      "risks": ["歌手时间安排", "对歌难度控制"],
      "implementation_difficulty": "中等"
    }}
  ],
  "anti_patterns": [
    "❌ 制作山歌CD/音像制品 - 过时且无互动",
    "❌ 山歌广场表演 - 游客只是旁观者",
    "❌ 山歌文创周边 - 缺乏文化深度"
  ]
}}
```

请开始你的深度思考和创意分析。
"""
        return prompt

    async def _get_project_context(self, project_id: int, keywords: List[str]) -> str:
        """
        提取项目相关信息作为背景
        """
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            return "暂无调研数据"

        # 提取包含关键词的文档内容
        relevant_texts = []
        for doc in documents:
            content = doc.text_content or ""
            for keyword in keywords:
                if keyword in content:
                    relevant_texts.append(f"文档《{doc.filename}》提到：{content[:500]}...")
                    break

        if not relevant_texts:
            # 如果没有包含关键词的文档，返回所有文档摘要
            for doc in documents[:3]:  # 最多3个
                content = doc.text_content or ""
                relevant_texts.append(f"文档《{doc.filename}》：{content[:300]}...")

        context = "\n\n".join(relevant_texts)
        return context

    def _parse_creative_response(self, response) -> Dict[str, Any]:
        """
        解析 Claude 的响应
        """
        try:
            # 提取 content
            content = response.content[0].text

            # 尝试提取 JSON
            # 查找 ```json 和 ``` 之间的内容
            import re
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                return result
            else:
                # 如果没有找到 JSON block，尝试直接解析整个内容
                result = json.loads(content)
                return result

        except Exception as e:
            print(f"解析响应失败: {e}")
            # 返回默认结构
            return {
                "cultural_elements": [],
                "creative_possibilities": [],
                "anti_patterns": []
            }


    async def extract_cultural_elements(self, project_id: int) -> List[Dict[str, str]]:
        """
        从项目文档中提取文化元素
        """
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        elements = []

        # 简单的关键词提取（实际应用中可以用 NLP）
        cultural_keywords = [
            "传统", "手工艺", "民俗", "节日", "习俗", "歌舞",
            "建筑", "服饰", "饮食", "语言", "技艺"
        ]

        for doc in documents:
            content = doc.text_content or ""
            for keyword in cultural_keywords:
                if keyword in content:
                    elements.append({
                        "element": keyword,
                        "source": doc.filename
                    })

        return elements
