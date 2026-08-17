"""
业态分析服务
分析现有业态 + 建议新业态（基于调研数据，有理有据）
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from anthropic import Anthropic
import os
import json
import re

from app.models.project import ProjectDocument


class BusinessAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze_business_formats(self, project_id: int) -> Dict[str, Any]:
        """
        业态分析系统

        输出：
        1. 现有业态梳理
        2. 可能的新业态
        3. 可行性评分（有理有据）
        4. 所需资源和条件
        5. 业态协同效应

        Raises:
            ValueError: 缺少必需的配置（ANTHROPIC_API_KEY）
            RuntimeError: API调用失败
        """

        # 0. 验证配置
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY未配置。业态分析功能需要Claude API。"
                "请在环境变量中设置ANTHROPIC_API_KEY。"
            )

        # 1. 提取项目信息
        project_context = await self._get_project_context(project_id)

        # 2. 提取现有业态
        existing_formats = await self._extract_existing_formats(project_context)

        # 3. 构建业态分析 Prompt
        prompt = self._build_business_prompt(project_context, existing_formats)

        # 4. 调用 Claude 分析
        try:
            response = self.anthropic.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 5. 解析结果
            analysis = self._parse_business_response(response, existing_formats)

        except Exception as e:
            # 记录错误但抛出异常，让调用方处理
            print(f"业态分析API调用失败: {e}")
            raise RuntimeError(f"业态分析失败: {str(e)}") from e

        analysis["project_id"] = project_id
        return analysis

    async def _get_project_context(self, project_id: int) -> str:
        """
        提取项目相关信息
        """
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            return "暂无调研数据"

        # 合并所有文档内容
        all_text = []
        for doc in documents[:5]:  # 最多取5个文档
            content = doc.text_content or ""
            if content:
                all_text.append(f"## 文档：{doc.filename}\n{content[:1000]}...")

        context = "\n\n".join(all_text)
        return context

    async def _extract_existing_formats(self, context: str) -> List[Dict[str, str]]:
        """
        从调研数据中提取现有业态
        """
        existing = []

        # 业态关键词
        format_keywords = {
            "咖啡馆": ["咖啡", "咖啡馆", "咖啡店"],
            "民宿": ["民宿", "客栈", "住宿"],
            "餐厅": ["餐厅", "饭店", "农家乐"],
            "研学基地": ["研学", "研学基地", "教育基地"],
            "文创店": ["文创", "手工艺品", "纪念品"],
            "茶室": ["茶室", "茶馆", "茶文化"],
            "工作坊": ["工作坊", "体验馆", "手工体验"],
        }

        for format_name, keywords in format_keywords.items():
            for keyword in keywords:
                if keyword in context:
                    # 尝试提取状态信息
                    status = "运营中"
                    if any(s in context for s in ["筹备", "计划", "准备"]):
                        status = "筹备中"
                    elif any(s in context for s in ["已关闭", "停业", "不再"]):
                        status = "已停业"

                    existing.append({
                        "name": format_name,
                        "status": status,
                        "scale": "小型",  # 默认
                        "description": f"从调研数据中发现提到{keyword}"
                    })
                    break  # 每种业态只添加一次

        return existing

    def _build_business_prompt(self, context: str, existing_formats: List[Dict]) -> str:
        """
        构建业态分析 Prompt
        """
        existing_str = "\n".join([
            f"- {f['name']}（{f['status']}）"
            for f in existing_formats
        ]) if existing_formats else "暂无明确的现有业态信息"

        prompt = f"""
你是一位资深的乡村运营顾问，专注于业态规划和可行性分析。现在需要你基于调研数据，分析现有业态并建议新的业态可能性。

## 调研数据
{context}

## 现有业态
{existing_str}

## 分析要求

请提供：

1. **现有业态评估**（如果有）
   - 运营状况
   - 优势和问题
   - 改进建议

2. **建议的新业态**（3-5个）
   每个业态需要包括：
   - 业态名称
   - 可行性评分（0-100）
   - 理由（基于调研数据中的具体证据）
   - 所需投资规模
   - 收入潜力
   - 风险点
   - 所需条件
   - 具体实施步骤

3. **业态协同效应**
   - 不同业态之间如何相互支持
   - 资源共享可能性
   - 客流导流策略

## 关键原则
- **有理有据**：所有建议必须基于调研数据中的具体内容
- **实事求是**：评估要客观，不夸大可行性
- **因地制宜**：业态选择要符合当地实际条件
- **可持续性**：考虑长期运营的可能性

## 输出格式

请以 JSON 格式返回：

```json
{{
  "suggested_formats": [
    {{
      "name": "研学基地",
      "feasibility_score": 78,
      "reason": "调研数据显示：村落有丰富的非遗资源（XX、XX），且XX小学多次咨询研学活动，市场需求明确",
      "investment": "50-100万（场地改造、安全设施、教学材料）",
      "revenue_potential": "中等（单次研学300-500元/人，预计年接待1000人次）",
      "risk_points": ["安全设施需完善", "需要专业研学导师", "季节性明显"],
      "required_conditions": ["改造2-3个体验场地", "配备安全设备", "培训3-5名当地导师"],
      "evidence": ["调研中提到：XX小学校长表示有研学需求", "村中有3位非遗传承人愿意参与教学"],
      "implementation_steps": [
        "第1步：与学校签订合作意向",
        "第2步：场地改造和安全设施完善（3个月）",
        "第3步：开发3-5个研学课程",
        "第4步：试运营并收集反馈"
      ]
    }}
  ],
  "synergy_analysis": "研学基地可与现有咖啡馆形成协同：研学团队用餐需求可带动咖啡馆营收。民宿与研学基地结合，可开发'研学+住宿'套餐产品...",
  "recommendations": [
    "优先发展研学基地，市场需求明确且投资回报周期较短",
    "咖啡馆可升级为'茶+咖啡+轻食'复合业态，提高坪效",
    "建议成立统一的运营公司，实现业态间资源共享"
  ]
}}
```

请开始你的业态分析。
"""
        return prompt

    def _parse_business_response(self, response, existing_formats: List[Dict]) -> Dict[str, Any]:
        """
        解析 Claude 的响应
        """
        try:
            content = response.content[0].text

            # 提取 JSON
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
            else:
                result = json.loads(content)

            result["existing_formats"] = existing_formats
            return result

        except Exception as e:
            print(f"解析响应失败: {e}")
            return {
                "existing_formats": existing_formats,
                "suggested_formats": [],
                "synergy_analysis": "",
                "recommendations": []
            }


    async def get_existing_formats(self, project_id: int) -> List[Dict[str, str]]:
        """
        获取现有业态列表
        """
        context = await self._get_project_context(project_id)
        existing = await self._extract_existing_formats(context)
        return existing

    async def analyze_synergy(self, project_id: int) -> str:
        """
        分析业态协同效应
        """
        analysis = await self.analyze_business_formats(project_id)
        return analysis.get("synergy_analysis", "")
