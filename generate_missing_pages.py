#!/usr/bin/env python3
"""
批量生成缺失的前端页面
"""
from pathlib import Path

# 页面模板
PAGE_TEMPLATE = """import React, {{ useState, useEffect }} from 'react';
import {{ {api_imports} }} from '@/services/fieldmind-api';

export default function {page_name}() {{
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  useEffect(() => {{
    loadData();
  }}, []);

  const loadData = async () => {{
    setLoading(true);
    try {{
      // TODO: 调用对应的 API
      // const response = await {api_name}.{method}();
      // setData(response.data);
    }} catch (error) {{
      console.error('Failed to load data:', error);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{display_name}</h1>
          <p className="mt-2 text-gray-600">{description}</p>
        </div>

        {{loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#27768A]"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">内容开发中...</p>
            {{/* TODO: 实现页面具体功能 */}}
          </div>
        )}}
      </div>
    </div>
  );
}}
"""

# 缺失页面定义
MISSING_PAGES = [
    {'file': 'Annotation.tsx', 'name': 'AnnotationPage', 'api': 'annotationAPI', 'display': '标注管理', 'desc': '管理文档标注和批注'},
    {'file': 'Audio.tsx', 'name': 'AudioPage', 'api': 'audioAPI', 'display': '音频处理', 'desc': '音频文件处理和转录'},
    {'file': 'Audit.tsx', 'name': 'AuditPage', 'api': 'auditAPI', 'display': '审计日志', 'desc': '系统操作审计和日志查看'},
    {'file': 'BackgroundLearning.tsx', 'name': 'BackgroundLearningPage', 'api': 'backgroundLearningAPI', 'display': '后台学习', 'desc': 'AI 后台学习和模型训练'},
    {'file': 'ChunksQuantification.tsx', 'name': 'ChunksQuantificationPage', 'api': 'chunksAPI', 'display': '分块量化', 'desc': '文档分块和量化分析'},
    {'file': 'Collaboration.tsx', 'name': 'CollaborationPage', 'api': 'collaborationAPI', 'display': '协作管理', 'desc': '团队协作和共享管理'},
    {'file': 'Crawler.tsx', 'name': 'CrawlerPage', 'api': 'crawlerAPI', 'display': '网络爬虫', 'desc': '配置和管理网络爬虫任务'},
    {'file': 'DataEnrichment.tsx', 'name': 'DataEnrichmentPage', 'api': 'dataEnrichmentAPI', 'display': '数据增强', 'desc': '数据清洗和增强处理'},
    {'file': 'EnhancedChat.tsx', 'name': 'EnhancedChatPage', 'api': 'enhancedChatAPI', 'display': '增强聊天', 'desc': '智能对话和上下文理解'},
    {'file': 'ExecutionTracking.tsx', 'name': 'ExecutionTrackingPage', 'api': 'executionTrackingAPI', 'display': '执行跟踪', 'desc': '任务执行状态跟踪'},
    {'file': 'ExperienceGraph.tsx', 'name': 'ExperienceGraphPage', 'api': 'experienceGraphAPI', 'display': '经验图谱', 'desc': '知识经验关系图谱'},
    {'file': 'FeedbackLoops.tsx', 'name': 'FeedbackLoopsPage', 'api': 'feedbackLoopsAPI', 'display': '反馈循环', 'desc': '用户反馈和系统优化'},
    {'file': 'Feeding.tsx', 'name': 'FeedingPage', 'api': 'feedingAPI', 'display': '数据馈送', 'desc': '数据源管理和自动馈送'},
    {'file': 'GovernanceValidation.tsx', 'name': 'GovernanceValidationPage', 'api': 'governanceAPI', 'display': '治理验证', 'desc': '数据治理和合规验证'},
    {'file': 'Industry.tsx', 'name': 'IndustryPage', 'api': 'industryAPI', 'display': '行业分析', 'desc': '行业知识库和分析'},
    {'file': 'KnowledgeNetwork.tsx', 'name': 'KnowledgeNetworkPage', 'api': 'knowledgeNetworkAPI', 'display': '知识网络', 'desc': '知识点关系网络可视化'},
    {'file': 'Learning.tsx', 'name': 'LearningPage', 'api': 'learningAPI', 'display': '学习管理', 'desc': 'AI 学习和模型管理'},
    {'file': 'Lineage.tsx', 'name': 'LineagePage', 'api': 'lineageAPI', 'display': '数据血缘', 'desc': '数据来源和流转追踪'},
    {'file': 'PatternRecognition.tsx', 'name': 'PatternRecognitionPage', 'api': 'patternRecognitionAPI', 'display': '模式识别', 'desc': '数据模式和规律识别'},
    {'file': 'Skills.tsx', 'name': 'SkillsPage', 'api': 'skillAPI', 'display': '技能管理', 'desc': 'AI 技能和能力管理'},
    {'file': 'SkillGeneration.tsx', 'name': 'SkillGenerationPage', 'api': 'skillGenerationAPI', 'display': '技能生成', 'desc': '自动生成 AI 技能'},
    {'file': 'SkillOptimization.tsx', 'name': 'SkillOptimizationPage', 'api': 'skillOptimizationAPI', 'display': '技能优化', 'desc': 'AI 技能优化和调优'},
    {'file': 'SOP.tsx', 'name': 'SOPPage', 'api': 'sopAPI', 'display': 'SOP 管理', 'desc': '标准操作流程管理'},
    {'file': 'SuperAgents.tsx', 'name': 'SuperAgentsPage', 'api': 'superAgentsAPI', 'display': '超级智能体', 'desc': '高级 AI 智能体管理'},
    {'file': 'Tagging.tsx', 'name': 'TaggingPage', 'api': 'taggingAPI', 'display': '标签管理', 'desc': '智能标签和分类管理'},
    {'file': 'Tasks.tsx', 'name': 'TasksPage', 'api': 'taskAPI', 'display': '任务管理', 'desc': '项目任务和待办事项'},
    {'file': 'TopicAnalysis.tsx', 'name': 'TopicAnalysisPage', 'api': 'topicAnalysisAPI', 'display': '主题分析', 'desc': '文档主题提取和分析'},
    {'file': 'Traceability.tsx', 'name': 'TraceabilityPage', 'api': 'traceabilityAPI', 'display': '可追溯性', 'desc': '数据和操作可追溯性管理'},
    {'file': 'UnifiedPlugins.tsx', 'name': 'UnifiedPluginsPage', 'api': 'pluginsAPI', 'display': '插件管理', 'desc': '统一插件和扩展管理'},
    {'file': 'UserAnalysis.tsx', 'name': 'UserAnalysisPage', 'api': 'userAnalysisAPI', 'display': '用户分析', 'desc': '用户行为分析和洞察'},
    {'file': 'Workbench.tsx', 'name': 'WorkbenchPage', 'api': 'workbenchAPI', 'display': '工作台', 'desc': '统一工作台和操作中心'},
]

def generate_pages():
    """生成所有缺失的前端页面"""
    pages_dir = Path('/Users/alwan/FieldMind/frontend/src/pages')

    if not pages_dir.exists():
        print(f"❌ 目录不存在: {pages_dir}")
        return

    print("🚀 开始生成缺失的前端页面...\n")

    success_count = 0
    skip_count = 0

    for page in MISSING_PAGES:
        page_path = pages_dir / page['file']

        if page_path.exists():
            print(f"⏭️  {page['file']:35s} - 已存在，跳过")
            skip_count += 1
            continue

        # 生成页面内容
        content = PAGE_TEMPLATE.format(
            api_imports=page['api'],
            page_name=page['name'],
            api_name=page['api'],
            method='getData',  # 通用方法名
            display_name=page['display'],
            description=page['desc']
        )

        # 写入文件
        page_path.write_text(content)
        print(f"✅ {page['file']:35s} - 已生成")
        success_count += 1

    print(f"\n{'='*70}")
    print(f"✅ 成功生成: {success_count} 个")
    print(f"⏭️  已跳过: {skip_count} 个")
    print(f"{'='*70}")

if __name__ == '__main__':
    generate_pages()
