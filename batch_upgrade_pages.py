#!/usr/bin/env python3
"""
批量升级前端页面为高质量、完整功能版本
"""

import os
from pathlib import Path

# 页面配置
PAGES_CONFIG = {
    "ChunksQuantification": {
        "title": "区块量化",
        "description": "管理和量化数据区块，追踪数据处理进度",
        "icon": "Cube",
        "color": "#27768A",
        "api": "chunksAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["name", "size", "status", "progress", "created_at"],
        "stats": [
            {"label": "总区块数", "key": "total", "color": "blue"},
            {"label": "处理中", "key": "processing", "color": "yellow"},
            {"label": "已完成", "key": "completed", "color": "green"},
            {"label": "失败", "key": "failed", "color": "red"}
        ]
    },

    "DataEnrichment": {
        "title": "数据增强",
        "description": "通过 AI 和外部数据源增强现有数据",
        "icon": "Sparkles",
        "color": "#748D44",
        "api": "enrichmentAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["source", "type", "status", "quality_score", "updated_at"],
        "stats": [
            {"label": "数据源", "key": "sources", "color": "blue"},
            {"label": "增强记录", "key": "enhanced", "color": "green"},
            {"label": "质量提升", "key": "improvement", "color": "purple"},
            {"label": "处理中", "key": "processing", "color": "yellow"}
        ]
    },

    "Feeding": {
        "title": "数据喂养",
        "description": "向系统持续输入和更新数据",
        "icon": "Upload",
        "color": "#F8B042",
        "api": "feedingAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["name", "type", "frequency", "last_run", "status"],
        "stats": [
            {"label": "数据源", "key": "sources", "color": "blue"},
            {"label": "今日更新", "key": "today", "color": "green"},
            {"label": "运行中", "key": "running", "color": "yellow"},
            {"label": "失败任务", "key": "failed", "color": "red"}
        ]
    },

    "Crawler": {
        "title": "爬虫管理",
        "description": "配置和管理网络数据抓取任务",
        "icon": "Globe",
        "color": "#27768A",
        "api": "crawlerAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["name", "url", "frequency", "last_run", "status", "items_count"],
        "stats": [
            {"label": "爬虫任务", "key": "total", "color": "blue"},
            {"label": "运行中", "key": "running", "color": "green"},
            {"label": "已抓取", "key": "items", "color": "purple"},
            {"label": "错误", "key": "errors", "color": "red"}
        ]
    },

    "Annotation": {
        "title": "数据标注",
        "description": "对文档和数据进行人工或自动标注",
        "icon": "Tag",
        "color": "#EC6A52",
        "api": "annotationAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["document", "labels", "annotator", "status", "created_at"],
        "stats": [
            {"label": "待标注", "key": "pending", "color": "yellow"},
            {"label": "进行中", "key": "in_progress", "color": "blue"},
            {"label": "已完成", "key": "completed", "color": "green"},
            {"label": "总标注数", "key": "total", "color": "purple"}
        ]
    },

    "Tagging": {
        "title": "智能标签",
        "description": "自动为内容生成和管理标签",
        "icon": "Tags",
        "color": "#748D44",
        "api": "taggingAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["tag", "category", "usage_count", "created_at"],
        "stats": [
            {"label": "总标签数", "key": "total", "color": "blue"},
            {"label": "今日新增", "key": "today", "color": "green"},
            {"label": "热门标签", "key": "popular", "color": "purple"},
            {"label": "未使用", "key": "unused", "color": "gray"}
        ]
    },

    "TopicAnalysis": {
        "title": "主题分析",
        "description": "自动识别和分析文档主题",
        "icon": "Brain",
        "color": "#27768A",
        "api": "topicAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["topic", "keywords", "document_count", "trend", "confidence"],
        "stats": [
            {"label": "主题总数", "key": "total", "color": "blue"},
            {"label": "活跃主题", "key": "active", "color": "green"},
            {"label": "新兴主题", "key": "emerging", "color": "purple"},
            {"label": "文档覆盖", "key": "coverage", "color": "yellow"}
        ]
    },

    "PatternRecognition": {
        "title": "模式识别",
        "description": "识别数据中的规律和模式",
        "icon": "Network",
        "color": "#F8B042",
        "api": "patternAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["pattern", "type", "frequency", "confidence", "discovered_at"],
        "stats": [
            {"label": "已识别模式", "key": "total", "color": "blue"},
            {"label": "高置信度", "key": "high_confidence", "color": "green"},
            {"label": "应用次数", "key": "applications", "color": "purple"},
            {"label": "今日发现", "key": "today", "color": "yellow"}
        ]
    },

    "EnhancedChat": {
        "title": "增强对话",
        "description": "支持多模态的智能对话系统",
        "icon": "MessageSquare",
        "color": "#27768A",
        "api": "chatAPI",
        "has_table": False,
        "has_create": False,
        "has_stats": True,
        "has_chart": False,
        "chat_interface": True,
        "stats": [
            {"label": "会话总数", "key": "total", "color": "blue"},
            {"label": "今日会话", "key": "today", "color": "green"},
            {"label": "平均轮次", "key": "avg_turns", "color": "purple"},
            {"label": "满意度", "key": "satisfaction", "color": "yellow"}
        ]
    },

    "SuperAgents": {
        "title": "超级智能体",
        "description": "管理和编排多个 AI Agent",
        "icon": "Bot",
        "color": "#748D44",
        "api": "agentsAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "card_view": True,
        "table_columns": ["name", "type", "status", "tasks_completed", "success_rate"],
        "stats": [
            {"label": "智能体总数", "key": "total", "color": "blue"},
            {"label": "在线", "key": "online", "color": "green"},
            {"label": "任务完成", "key": "completed", "color": "purple"},
            {"label": "成功率", "key": "success_rate", "color": "yellow"}
        ]
    },

    "Skills": {
        "title": "技能库",
        "description": "管理 AI 可执行的技能和能力",
        "icon": "Zap",
        "color": "#EC6A52",
        "api": "skillsAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["name", "category", "usage_count", "success_rate", "updated_at"],
        "stats": [
            {"label": "技能总数", "key": "total", "color": "blue"},
            {"label": "常用技能", "key": "popular", "color": "green"},
            {"label": "今日使用", "key": "today_usage", "color": "purple"},
            {"label": "平均成功率", "key": "avg_success", "color": "yellow"}
        ]
    },

    "SkillGeneration": {
        "title": "技能生成",
        "description": "自动生成新的 AI 技能",
        "icon": "Wand2",
        "color": "#27768A",
        "api": "skillGenerationAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["name", "description", "status", "test_score", "created_at"],
        "stats": [
            {"label": "生成总数", "key": "total", "color": "blue"},
            {"label": "进行中", "key": "generating", "color": "yellow"},
            {"label": "已通过", "key": "passed", "color": "green"},
            {"label": "失败", "key": "failed", "color": "red"}
        ]
    },

    "SkillOptimization": {
        "title": "技能优化",
        "description": "优化和改进现有技能",
        "icon": "TrendingUp",
        "color": "#748D44",
        "api": "skillOptimizationAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["skill", "version", "improvement", "status", "optimized_at"],
        "stats": [
            {"label": "优化任务", "key": "total", "color": "blue"},
            {"label": "进行中", "key": "running", "color": "yellow"},
            {"label": "已提升", "key": "improved", "color": "green"},
            {"label": "平均提升", "key": "avg_improvement", "color": "purple"}
        ]
    },

    "Learning": {
        "title": "学习中心",
        "description": "系统持续学习和改进",
        "icon": "GraduationCap",
        "color": "#F8B042",
        "api": "learningAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["source", "type", "progress", "knowledge_gained", "started_at"],
        "stats": [
            {"label": "学习任务", "key": "total", "color": "blue"},
            {"label": "进行中", "key": "active", "color": "green"},
            {"label": "知识增长", "key": "knowledge", "color": "purple"},
            {"label": "完成率", "key": "completion", "color": "yellow"}
        ]
    },

    "BackgroundLearning": {
        "title": "后台学习",
        "description": "系统自动后台学习机制",
        "icon": "Settings",
        "color": "#27768A",
        "api": "learningAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["task", "schedule", "last_run", "next_run", "status"],
        "stats": [
            {"label": "后台任务", "key": "total", "color": "blue"},
            {"label": "运行中", "key": "running", "color": "green"},
            {"label": "今日学习", "key": "today", "color": "purple"},
            {"label": "资源使用", "key": "resource", "color": "yellow"}
        ]
    },

    "FeedbackLoops": {
        "title": "反馈回路",
        "description": "管理用户反馈和系统改进循环",
        "icon": "RefreshCw",
        "color": "#EC6A52",
        "api": "feedbackAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["feedback", "type", "status", "priority", "created_at"],
        "stats": [
            {"label": "反馈总数", "key": "total", "color": "blue"},
            {"label": "待处理", "key": "pending", "color": "yellow"},
            {"label": "已改进", "key": "implemented", "color": "green"},
            {"label": "平均响应", "key": "avg_response", "color": "purple"}
        ]
    },

    "GovernanceValidation": {
        "title": "治理验证",
        "description": "验证数据和操作的合规性",
        "icon": "ShieldCheck",
        "color": "#27768A",
        "api": "governanceAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["rule", "resource", "status", "violations", "last_check"],
        "stats": [
            {"label": "验证规则", "key": "rules", "color": "blue"},
            {"label": "合规项", "key": "compliant", "color": "green"},
            {"label": "违规项", "key": "violations", "color": "red"},
            {"label": "合规率", "key": "compliance_rate", "color": "purple"}
        ]
    },

    "Audit": {
        "title": "审计日志",
        "description": "查看和分析系统操作审计记录",
        "icon": "FileText",
        "color": "#748D44",
        "api": "auditAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["timestamp", "user", "action", "resource", "result", "ip_address"],
        "stats": [
            {"label": "今日操作", "key": "today", "color": "blue"},
            {"label": "成功", "key": "success", "color": "green"},
            {"label": "失败", "key": "failed", "color": "red"},
            {"label": "异常", "key": "anomalies", "color": "yellow"}
        ]
    },

    "Traceability": {
        "title": "数据溯源",
        "description": "追踪数据的来源和转换历史",
        "icon": "GitBranch",
        "color": "#F8B042",
        "api": "traceabilityAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["resource", "source", "transformations", "lineage_depth", "updated_at"],
        "stats": [
            {"label": "追踪资源", "key": "resources", "color": "blue"},
            {"label": "数据源", "key": "sources", "color": "green"},
            {"label": "转换步骤", "key": "transformations", "color": "purple"},
            {"label": "完整率", "key": "completeness", "color": "yellow"}
        ]
    },

    "KnowledgeNetwork": {
        "title": "知识网络",
        "description": "构建和探索知识关联网络",
        "icon": "Share2",
        "color": "#27768A",
        "api": "knowledgeAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "graph_view": True,
        "stats": [
            {"label": "节点总数", "key": "nodes", "color": "blue"},
            {"label": "关系数", "key": "edges", "color": "green"},
            {"label": "子网络", "key": "subgraphs", "color": "purple"},
            {"label": "平均度数", "key": "avg_degree", "color": "yellow"}
        ]
    },

    "ExperienceGraph": {
        "title": "经验图谱",
        "description": "沉淀和可视化组织经验",
        "icon": "Lightbulb",
        "color": "#EC6A52",
        "api": "experienceAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "graph_view": True,
        "stats": [
            {"label": "经验节点", "key": "experiences", "color": "blue"},
            {"label": "贡献者", "key": "contributors", "color": "green"},
            {"label": "引用次数", "key": "references", "color": "purple"},
            {"label": "质量评分", "key": "quality", "color": "yellow"}
        ]
    },

    "Lineage": {
        "title": "血缘分析",
        "description": "分析资源的上下游依赖关系",
        "icon": "GitMerge",
        "color": "#748D44",
        "api": "lineageAPI",
        "has_table": False,
        "has_create": False,
        "has_stats": True,
        "has_chart": False,
        "graph_view": True,
        "stats": [
            {"label": "资源总数", "key": "resources", "color": "blue"},
            {"label": "依赖关系", "key": "dependencies", "color": "green"},
            {"label": "影响范围", "key": "impact", "color": "purple"},
            {"label": "断链", "key": "broken", "color": "red"}
        ]
    },

    "Collaboration": {
        "title": "协作空间",
        "description": "团队协作和沟通中心",
        "icon": "Users",
        "color": "#27768A",
        "api": "collaborationAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "card_view": True,
        "stats": [
            {"label": "团队成员", "key": "members", "color": "blue"},
            {"label": "在线", "key": "online", "color": "green"},
            {"label": "协作项目", "key": "projects", "color": "purple"},
            {"label": "今日活动", "key": "activities", "color": "yellow"}
        ]
    },

    "Tasks": {
        "title": "任务管理",
        "description": "创建和追踪团队任务",
        "icon": "CheckSquare",
        "color": "#F8B042",
        "api": "tasksAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "kanban_view": True,
        "stats": [
            {"label": "任务总数", "key": "total", "color": "blue"},
            {"label": "进行中", "key": "in_progress", "color": "yellow"},
            {"label": "已完成", "key": "completed", "color": "green"},
            {"label": "逾期", "key": "overdue", "color": "red"}
        ]
    },

    "ExecutionTracking": {
        "title": "执行追踪",
        "description": "追踪工作流和任务的执行状态",
        "icon": "Activity",
        "color": "#27768A",
        "api": "executionAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["execution", "workflow", "status", "progress", "duration", "started_at"],
        "stats": [
            {"label": "执行总数", "key": "total", "color": "blue"},
            {"label": "运行中", "key": "running", "color": "yellow"},
            {"label": "成功", "key": "success", "color": "green"},
            {"label": "失败", "key": "failed", "color": "red"}
        ]
    },

    "Workbench": {
        "title": "个人工作台",
        "description": "个性化的工作控制面板",
        "icon": "Layout",
        "color": "#748D44",
        "api": "workbenchAPI",
        "has_table": False,
        "has_create": False,
        "has_stats": True,
        "has_chart": False,
        "dashboard_view": True,
        "stats": [
            {"label": "待办事项", "key": "todos", "color": "yellow"},
            {"label": "最近项目", "key": "recent", "color": "blue"},
            {"label": "今日完成", "key": "today_done", "color": "green"},
            {"label": "通知", "key": "notifications", "color": "purple"}
        ]
    },

    "UnifiedPlugins": {
        "title": "统一插件",
        "description": "管理系统插件和扩展",
        "icon": "Puzzle",
        "color": "#EC6A52",
        "api": "pluginsAPI",
        "has_table": False,
        "has_create": False,
        "has_stats": True,
        "has_chart": False,
        "card_view": True,
        "stats": [
            {"label": "已安装", "key": "installed", "color": "blue"},
            {"label": "启用中", "key": "enabled", "color": "green"},
            {"label": "可更新", "key": "updates", "color": "yellow"},
            {"label": "市场插件", "key": "available", "color": "purple"}
        ]
    },

    "Audio": {
        "title": "音频处理",
        "description": "音频文件的转录和分析",
        "icon": "Mic",
        "color": "#27768A",
        "api": "audioAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["filename", "duration", "transcription_status", "language", "uploaded_at"],
        "stats": [
            {"label": "音频文件", "key": "total", "color": "blue"},
            {"label": "已转录", "key": "transcribed", "color": "green"},
            {"label": "处理中", "key": "processing", "color": "yellow"},
            {"label": "总时长", "key": "duration", "color": "purple"}
        ]
    },

    "UserAnalysis": {
        "title": "用户分析",
        "description": "分析用户行为和使用模式",
        "icon": "BarChart3",
        "color": "#748D44",
        "api": "analyticsAPI",
        "has_table": True,
        "has_create": False,
        "has_stats": True,
        "has_chart": True,
        "table_columns": ["user", "sessions", "actions", "last_active", "engagement_score"],
        "stats": [
            {"label": "活跃用户", "key": "active", "color": "green"},
            {"label": "新用户", "key": "new", "color": "blue"},
            {"label": "留存率", "key": "retention", "color": "purple"},
            {"label": "平均会话", "key": "avg_session", "color": "yellow"}
        ]
    },

    "Industry": {
        "title": "行业方案",
        "description": "行业特定的解决方案模板",
        "icon": "Briefcase",
        "color": "#F8B042",
        "api": "industryAPI",
        "has_table": False,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "card_view": True,
        "stats": [
            {"label": "行业模板", "key": "total", "color": "blue"},
            {"label": "已应用", "key": "applied", "color": "green"},
            {"label": "自定义", "key": "custom", "color": "purple"},
            {"label": "热门", "key": "popular", "color": "yellow"}
        ]
    },

    "SOP": {
        "title": "标准操作流程",
        "description": "管理和执行标准操作流程",
        "icon": "ListChecks",
        "color": "#27768A",
        "api": "sopAPI",
        "has_table": True,
        "has_create": True,
        "has_stats": True,
        "has_chart": False,
        "table_columns": ["name", "category", "steps", "executions", "last_updated"],
        "stats": [
            {"label": "SOP 总数", "key": "total", "color": "blue"},
            {"label": "今日执行", "key": "executions", "color": "green"},
            {"label": "合规率", "key": "compliance", "color": "purple"},
            {"label": "平均耗时", "key": "avg_duration", "color": "yellow"}
        ]
    }
}

def generate_page_component(page_name, config):
    """生成完整的页面组件代码"""

    # 生成统计卡片
    stats_jsx = "\n".join([
        f"""        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{stat['label']}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {{stats?.{stat['key']} || 0}}
              </p>
            </div>
            <div className="h-12 w-12 bg-{stat['color']}-50 rounded-lg flex items-center justify-center">
              <div className="h-6 w-6 text-{stat['color']}-600" />
            </div>
          </div>
        </Card>"""
        for stat in config['stats']
    ])

    # 根据页面类型生成主内容
    if config.get('has_table'):
        main_content = f"""
      {{/* 数据表格 */}}
      {{!isLoading && data && data.length > 0 ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {" ".join([f'<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{col}</th>' for col in config['table_columns']])}
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {{data.map((item: any) => (
                  <tr key={{item.id}} className="hover:bg-gray-50">
                    {" ".join([f'<td className="px-6 py-4 whitespace-nowrap">{{item.{col}}}</td>' for col in config['table_columns']])}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={{() => handleView(item.id)}}
                        className="text-[{config['color']}] hover:text-[{config['color']}]/80 mr-3"
                      >
                        查看
                      </button>
                      <button
                        onClick={{() => handleDelete(item.id)}}
                        className="text-red-600 hover:text-red-700"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card className="p-12">
          <div className="text-center">
            <{config['icon']} className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无数据</h3>
            <p className="mt-1 text-sm text-gray-500">开始创建第一条记录</p>
            {config.get('has_create') and '''<button
              onClick={() => setIsCreateDialogOpen(true)}
              className="mt-4 px-4 py-2 bg-[''' + config['color'] + '''] text-white rounded-lg hover:opacity-90"
            >
              创建
            </button>''' or ''}
          </div>
        </Card>
      )}}"""
    elif config.get('chat_interface'):
        main_content = """
      {/* 对话界面 */}
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-1 p-4">
          <h3 className="font-semibold mb-4">对话历史</h3>
          <div className="space-y-2">
            {conversations.map((conv: any) => (
              <div
                key={conv.id}
                className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedConversation(conv.id)}
              >
                <p className="font-medium text-sm">{conv.title}</p>
                <p className="text-xs text-gray-500">{conv.updated_at}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="col-span-2 p-6">
          <div className="h-[600px] flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.map((msg: any) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-[""" + config['color'] + """] text-white'
                      : 'bg-gray-100'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="输入消息..."
                className="flex-1 px-4 py-2 border rounded-lg"
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <button
                onClick={handleSendMessage}
                className="px-6 py-2 bg-[""" + config['color'] + """] text-white rounded-lg hover:opacity-90"
              >
                发送
              </button>
            </div>
          </div>
        </Card>
      </div>"""
    elif config.get('graph_view'):
        main_content = f"""
      {{/* 图谱视图 */}}
      <Card className="p-6">
        <div className="h-[600px] bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <{config['icon']} className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <p className="text-gray-600">图谱可视化加载中...</p>
            <p className="text-sm text-gray-500 mt-2">{{data?.nodes || 0}} 个节点, {{data?.edges || 0}} 条关系</p>
          </div>
        </div>
      </Card>"""
    elif config.get('kanban_view'):
        main_content = f"""
      {{/* 看板视图 */}}
      <div className="grid grid-cols-3 gap-6">
        {{['待办', '进行中', '已完成'].map((status) => (
          <Card key={{status}} className="p-4">
            <h3 className="font-semibold mb-4 flex items-center justify-between">
              <span>{{status}}</span>
              <span className="text-sm text-gray-500">
                {{tasks?.filter((t: any) => t.status === status).length || 0}}
              </span>
            </h3>
            <div className="space-y-3">
              {{tasks
                ?.filter((t: any) => t.status === status)
                .map((task: any) => (
                  <div
                    key={{task.id}}
                    className="p-3 bg-white border rounded-lg hover:shadow-md cursor-pointer"
                  >
                    <p className="font-medium">{{task.title}}</p>
                    <p className="text-sm text-gray-500 mt-1">{{task.assignee}}</p>
                  </div>
                ))}}
            </div>
          </Card>
        ))}}
      </div>"""
    elif config.get('card_view'):
        main_content = f"""
      {{/* 卡片视图 */}}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {{data?.map((item: any) => (
          <Card key={{item.id}} className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-start justify-between mb-4">
              <div className="h-12 w-12 bg-[{config['color']}]/10 rounded-lg flex items-center justify-center">
                <{config['icon']} className="h-6 w-6 text-[{config['color']}]" />
              </div>
              <span className={{`px-2 py-1 text-xs rounded-full ${{
                item.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }}`}}>
                {{item.status}}
              </span>
            </div>
            <h3 className="font-semibold text-lg mb-2">{{item.name}}</h3>
            <p className="text-sm text-gray-600">{{item.description}}</p>
            <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
              <span>{{item.updated_at}}</span>
              <button className="text-[{config['color']}] hover:underline">详情</button>
            </div>
          </Card>
        ))}}
      </div>"""
    else:
        main_content = f"""
      <Card className="p-12 text-center">
        <{config['icon']} className="mx-auto h-16 w-16 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">功能开发中</h3>
        <p className="text-sm text-gray-500 mt-2">此功能正在积极开发中</p>
      </Card>"""

    # 生成完整组件代码
    component_code = f"""import {{ useState, useEffect }} from 'react'
import {{ {config['api']} }} from '@/services/fieldmind-api'
import {{ Card }} from '@/components/ui/card'
import {{ Button }} from '@/components/ui/button'
import {{ Input }} from '@/components/ui/input'
import {{ Spinner }} from '@/components/ui/spinner'
import {{ Dialog }} from '@/components/ui/dialog'
import {{ {config['icon']}, Plus, Search, Filter }} from 'lucide-react'
import {{ useToast }} from '@/components/ui/use-toast'

export default function {page_name}() {{
  const {{ toast }} = useToast()
  const [data, setData] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  {'const [conversations, setConversations] = useState<any[]>([])' if config.get('chat_interface') else ''}
  {'const [messages, setMessages] = useState<any[]>([])' if config.get('chat_interface') else ''}
  {'const [selectedConversation, setSelectedConversation] = useState<string | null>(null)' if config.get('chat_interface') else ''}
  {'const [tasks, setTasks] = useState<any[]>([])' if config.get('kanban_view') else ''}

  useEffect(() => {{
    loadData()
  }}, [])

  const loadData = async () => {{
    setLoading(true)
    try {{
      // TODO: 实际 API 调用
      // const response = await {config['api']}.getList()
      // setData(response.data)

      // 模拟数据
      setData([])
      setStats({{
        {', '.join([f"{stat['key']}: 0" for stat in config['stats']])}
      }})
    }} catch (error) {{
      console.error('Failed to load data:', error)
      toast({{
        title: '加载失败',
        description: '无法加载数据，请重试',
        variant: 'destructive',
      }})
    }} finally {{
      setLoading(false)
    }}
  }}

  const handleView = (id: string) => {{
    console.log('View:', id)
  }}

  const handleDelete = async (id: string) => {{
    if (!confirm('确定要删除吗？')) return

    try {{
      // await {config['api']}.delete(id)
      toast({{
        title: '删除成功',
        description: '记录已删除',
      }})
      loadData()
    }} catch (error) {{
      toast({{
        title: '删除失败',
        description: '无法删除记录，请重试',
        variant: 'destructive',
      }})
    }}
  }}

  {'const handleSendMessage = () => { console.log("Send message") }' if config.get('chat_interface') else ''}

  if (loading) {{
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }}

  return (
    <div className="space-y-6">
      {{/* Header */}}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <{config['icon']} className="h-8 w-8 text-[{config['color']}]" />
            {config['title']}
          </h1>
          <p className="text-gray-600 mt-1">{config['description']}</p>
        </div>
        {config.get('has_create') and f'''<Button onClick={{() => setIsCreateDialogOpen(true)}}>
          <Plus className="h-4 w-4 mr-2" />
          创建
        </Button>''' or ''}
      </div>

      {{/* 统计卡片 */}}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
{stats_jsx}
      </div>

      {{/* 搜索栏 */}}
      {config.get('has_table') and '''<Card className="p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
        </div>
      </Card>''' or ''}

{main_content}
    </div>
  )
}}
"""

    return component_code

def main():
    frontend_path = Path("/Users/alwan/FieldMind/frontend/src/pages")

    print("=" * 80)
    print("🚀 开始批量升级页面")
    print("=" * 80)
    print()

    upgraded_count = 0

    for page_name, config in PAGES_CONFIG.items():
        page_file = frontend_path / f"{page_name}.tsx"

        if not page_file.exists():
            print(f"⚠️  跳过: {page_name}.tsx (文件不存在)")
            continue

        print(f"📝 升级: {page_name}.tsx - {config['title']}")

        # 生成新代码
        new_code = generate_page_component(page_name, config)

        # 写入文件
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(new_code)

        upgraded_count += 1

    print()
    print("=" * 80)
    print(f"✅ 完成！已升级 {upgraded_count} 个页面")
    print("=" * 80)

if __name__ == "__main__":
    main()
