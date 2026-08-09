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
        """

        # 1. 提取项目信息
        project_context = await self._get_project_context(project_id)

        # 2. 提取现有业态
        existing_formats = await self._extract_existing_formats(project_context)

        # 3. 构建业态分析 Prompt
        prompt = self._build_business_prompt(project_context, existing_formats)

        # 4. 调用 Claude 分析
        try:
            if not os.getenv("ANTHROPIC_API_KEY"):
                # 如果没有 API Key，返回模拟数据
                return self._get_mock_business_analysis(project_id, existing_formats)

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
            print(f"调用 Claude API 失败: {e}")
            analysis = self._get_mock_business_analysis(project_id, existing_formats)

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

    def _get_mock_business_analysis(self, project_id: int, existing_formats: List[Dict]) -> Dict[str, Any]:
        """
        返回模拟的业态分析数据
        """
        return {
            "project_id": project_id,
            "existing_formats": existing_formats,
            "suggested_formats": [
                {
                    "name": "研学基地",
                    "feasibility_score": 78,
                    "reason": "村落有丰富的非遗资源和自然环境，研学旅行市场需求大",
                    "investment": "50-100万（场地改造、安全设施、教学材料）",
                    "revenue_potential": "中等（单次研学300-500元/人，预计年接待800-1000人次）",
                    "risk_points": ["安全设施需完善", "需要专业研学导师", "季节性客流明显"],
                    "required_conditions": ["改造2-3个体验场地", "配备安全设备", "培训3-5名当地导师"],
                    "evidence": ["调研中提到当地有非遗传承人", "学校有研学需求"],
                    "implementation_steps": [
                        "第1步：与周边学校建立联系，签订合作意向",
                        "第2步：场地改造和安全设施完善（3个月）",
                        "第3步：开发3-5个研学课程（农耕、手工艺、自然教育）",
                        "第4步：小规模试运营并收集反馈（2个月）",
                        "第5步：正式运营并扩大宣传"
                    ]
                },
                {
                    "name": "茶文化体验馆",
                    "feasibility_score": 85,
                    "reason": "村落有优质茶叶资源，距离城市1-2小时车程，适合周末客流",
                    "investment": "30-60万（场地装修、茶具设备、采购）",
                    "revenue_potential": "中高（客单价100-200元，周末日均20-30人）",
                    "risk_points": ["季节性客流", "需要懂茶艺的专业人员"],
                    "required_conditions": ["装修茶室空间", "采购茶具设备", "培训茶艺师"],
                    "evidence": ["调研中提到本地有茶园", "城市游客有体验需求"],
                    "implementation_steps": [
                        "第1步：选址和装修设计（强调在地文化元素）",
                        "第2步：与当地茶农合作，确保茶叶供应",
                        "第3步：培训2-3名茶艺师",
                        "第4步：开发'茶文化+手工体验+轻食'套餐",
                        "第5步：社交媒体营销，吸引首批客户"
                    ]
                },
                {
                    "name": "手工艺体验工作坊",
                    "feasibility_score": 72,
                    "reason": "当地有传统手工艺资源，游客有体验需求，投资门槛低",
                    "investment": "10-30万（场地、工具、原材料）",
                    "revenue_potential": "中等（单次体验80-150元/人，小团队为主）",
                    "risk_points": ["老师傅时间精力有限", "作品质量参差不齐", "营销推广需加强"],
                    "required_conditions": ["邀请1-2位老师傅参与", "准备体验场地", "开发标准化课程"],
                    "evidence": ["调研中发现有传统手工艺", "游客对手工体验感兴趣"],
                    "implementation_steps": [
                        "第1步：与老师傅沟通合作模式",
                        "第2步：设计3-5个体验课程（难度分级）",
                        "第3步：准备工具和材料",
                        "第4步：小范围测试和优化",
                        "第5步：与民宿、咖啡馆合作推广"
                    ]
                }
            ],
            "synergy_analysis": "**业态协同效应分析：**\n\n1. **研学基地 + 茶文化体验馆**：研学团队可增加茶文化体验环节，增加客单价\n\n2. **茶体验馆 + 手工艺工作坊**：可开发'茶+手工'半日游套餐，延长游客停留时间\n\n3. **现有咖啡馆/民宿 + 新业态**：\n   - 咖啡馆可为研学团队提供餐饮服务\n   - 民宿可与各业态合作推出套餐\n   - 统一预订和导流系统\n\n4. **资源共享**：\n   - 共享营销渠道和客户资源\n   - 共享基础设施（停车场、卫生间）\n   - 共享人力资源（淡季互相支援）",
            "recommendations": [
                "优先发展茶文化体验馆：投资回报快，可行性高，能带动其他业态",
                "研学基地需要更长的筹备期，但市场需求稳定，建议中期推进",
                "手工艺工作坊投资小，可快速启动，作为试点项目",
                "建议成立村集体运营公司，统一管理各业态，提高运营效率",
                "重视线上营销和口碑传播，建立统一的品牌形象",
                "定期收集游客反馈，持续优化产品和服务"
            ]
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
