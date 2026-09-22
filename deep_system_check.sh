#!/bin/bash

# FieldMind 深度系统检测报告 - 包含所有高级功能
# Agent、Skill、工作流、Hermes、Workbench、双通道等

echo "============================================"
echo "   FieldMind 深度系统检测报告"
echo "   包含所有高级功能模块"
echo "============================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="/Users/alwan/FieldMind"
BACKEND_ROOT="$PROJECT_ROOT/backend/src"
FRONTEND_ROOT="$PROJECT_ROOT/frontend/fieldmind-native/Sources"

# 检测函数
check_exists() {
    if [ -e "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 ${RED}(缺失)${NC}"
        return 1
    fi
}

check_percentage() {
    local exists=$1
    local total=$2
    local percentage=$((exists * 100 / total))

    if [ $percentage -ge 80 ]; then
        echo -e "${GREEN}${percentage}%${NC}"
    elif [ $percentage -ge 50 ]; then
        echo -e "${YELLOW}${percentage}%${NC}"
    else
        echo -e "${RED}${percentage}%${NC}"
    fi
}

# ==================== 前端页面完整性检测 ====================
echo -e "${BLUE}【第一部分】前端页面完整性检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

frontend_total=0
frontend_exists=0

echo "核心页面:"
pages=(
    "MainView.swift:主视图"
    "SidebarView.swift:侧边栏"
    "TopBarView.swift:顶部栏"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if check_exists "$FRONTEND_ROOT/Views/$file" "  $desc"; then
        ((frontend_exists++))
    fi
done

echo ""
echo "项目管理页面:"
pages=(
    "ProjectListView.swift:项目列表"
    "ProjectDetailView.swift:项目详情"
    "NewProjectView.swift:新建项目"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if [ -f "$FRONTEND_ROOT/Views/$file" ]; then
        ((frontend_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
echo "文档管理页面:"
pages=(
    "DocumentUploadView.swift:文档上传"
    "DocumentListView.swift:文档列表"
    "FileManagerView.swift:文件管理器"
    "PhotoManagerView.swift:照片管理"
    "TableManagerView.swift:表格管理"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if [ -f "$FRONTEND_ROOT/Views/$file" ]; then
        ((frontend_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
echo "AI 和知识处理页面:"
pages=(
    "ChatView.swift:AI 对话"
    "ConversationHistoryView.swift:对话历史"
    "KeywordSearchView.swift:关键词搜索"
    "CitationView.swift:引用管理"
    "KnowledgeGraphView.swift:知识图谱"
    "KnowledgeNetworkView.swift:知识脉络 ★新增★"
    "TimelineView.swift:时间线"
    "ChronicleView.swift:编年史"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if [ -f "$FRONTEND_ROOT/Views/$file" ]; then
        ((frontend_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
echo "分析和报告页面:"
pages=(
    "DashboardView.swift:可视化看板"
    "ReportView.swift:调研报告"
    "BusinessAnalysisView.swift:业态分析 ★新增★"
    "VeinView.swift:脉络可视化"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if [ -f "$FRONTEND_ROOT/Views/$file" ]; then
        ((frontend_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
echo "高级功能页面:"
pages=(
    "SkillView.swift:Skill 生态"
    "AgentMemoryView.swift:Agent 记忆"
    "WorkflowView.swift:工作流管理"
    "SOPView.swift:SOP 管理"
    "SOPAnalysisView.swift:SOP 分析"
    "QualityMonitorView.swift:质量监控"
    "ModelConfigView.swift:模型管理"
    "SettingsView.swift:设置"
)

for item in "${pages[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((frontend_total++))
    if [ -f "$FRONTEND_ROOT/Views/$file" ]; then
        ((frontend_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
percentage=$(check_percentage $frontend_exists $frontend_total)
echo -e "前端页面统计: ${GREEN}${frontend_exists}/${frontend_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== Agent 系统检测 ====================
echo -e "${PURPLE}【第二部分】Agent 系统检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

agent_total=0
agent_exists=0

echo "Agent 核心框架:"
agents=(
    "app/agents/__init__.py:Agent 初始化"
    "app/agents/base_agent.py:基础 Agent 类"
    "app/agents/agent_registry.py:Agent 注册表"
    "app/agents/agent_coordinator.py:Agent 协调器"
)

for item in "${agents[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((agent_total++))
    if check_exists "$BACKEND_ROOT/$file" "  $desc"; then
        ((agent_exists++))
    fi
done

echo ""
echo "专业 Agent 实现:"
agents=(
    "app/agents/chunking_agent.py:文档切分 Agent"
    "app/agents/entity_relation_agent.py:实体关系 Agent"
    "app/agents/field_dimension_agent.py:田野维度 Agent"
    "app/agents/knowledge_agent.py:知识 Agent"
    "app/agents/search_agent.py:搜索 Agent"
    "app/agents/summary_agent.py:摘要 Agent"
    "app/agents/coordinator_agent.py:协调 Agent"
)

for item in "${agents[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((agent_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((agent_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
percentage=$(check_percentage $agent_exists $agent_total)
echo -e "Agent 系统统计: ${GREEN}${agent_exists}/${agent_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== Skill 系统检测 ====================
echo -e "${PURPLE}【第三部分】Skill 系统检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

skill_total=0
skill_exists=0

echo "Skill 核心框架:"
skills=(
    "app/services/skill_service.py:Skill 服务"
    "app/models/skill.py:Skill 模型"
    "app/api/v1/skills.py:Skill API"
    "app/schemas/skill.py:Skill Schema"
)

for item in "${skills[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((skill_total++))
    if check_exists "$BACKEND_ROOT/$file" "  $desc"; then
        ((skill_exists++))
    fi
done

echo ""
echo "Skill 生态系统:"
skills=(
    "app/services/skill_sandbox.py:Skill 沙盒"
    "app/services/skill_loader.py:Skill 加载器"
    "app/models/skill_optimization.py:Skill 优化"
    "app/api/v1/skill_generation.py:Skill 生成"
    "app/api/v1/skill_optimization.py:Skill 优化 API"
)

for item in "${skills[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((skill_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((skill_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
# 检查预置 skills 目录
if [ -d "$BACKEND_ROOT/skills" ]; then
    skill_count=$(find "$BACKEND_ROOT/skills" -name "*.py" -type f | wc -l | tr -d ' ')
    echo -e "${GREEN}✓${NC}   预置 Skill 数量: ${skill_count}"
fi

percentage=$(check_percentage $skill_exists $skill_total)
echo -e "Skill 系统统计: ${GREEN}${skill_exists}/${skill_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== 工作流系统检测 ====================
echo -e "${PURPLE}【第四部分】工作流系统检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

workflow_total=0
workflow_exists=0

echo "工作流核心:"
workflows=(
    "app/services/workflow_engine.py:工作流引擎"
    "app/models/workflow_execution.py:工作流执行模型"
    "app/api/v1/workflows.py:工作流 API"
    "app/api/v1/project_workflow.py:项目工作流"
)

for item in "${workflows[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((workflow_total++))
    if check_exists "$BACKEND_ROOT/$file" "  $desc"; then
        ((workflow_exists++))
    fi
done

echo ""
echo "SOP 和工作流管理:"
workflows=(
    "app/services/sop_service.py:SOP 服务"
    "app/api/v1/sop.py:SOP API"
    "app/models/sop.py:SOP 模型"
)

for item in "${workflows[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((workflow_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((workflow_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

percentage=$(check_percentage $workflow_exists $workflow_total)
echo -e "工作流系统统计: ${GREEN}${workflow_exists}/${workflow_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== Hermes 治理引擎检测 ====================
echo -e "${CYAN}【第五部分】Hermes 治理引擎检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

hermes_total=0
hermes_exists=0

echo "Hermes 核心模块:"
hermes=(
    "app/services/hermes_governance.py:Hermes 治理服务"
    "app/models/governance.py:治理模型"
    "app/api/v1/governance.py:治理 API"
)

for item in "${hermes[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((hermes_total++))
    if check_exists "$BACKEND_ROOT/$file" "  $desc"; then
        ((hermes_exists++))
    fi
done

echo ""
echo "Hermes 子系统:"
hermes=(
    "app/services/hermes_learning.py:Hermes 学习"
    "app/services/hermes_feedback.py:Hermes 反馈"
    "app/services/hermes_pattern.py:Hermes 模式识别"
)

for item in "${hermes[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((hermes_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((hermes_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

percentage=$(check_percentage $hermes_exists $hermes_total)
echo -e "Hermes 系统统计: ${GREEN}${hermes_exists}/${hermes_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== Workbench 工作舱检测 ====================
echo -e "${CYAN}【第六部分】Workbench 工作舱检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

workbench_total=0
workbench_exists=0

echo "Workbench 核心:"
workbenches=(
    "app/services/workbench_service.py:工作舱服务"
    "app/api/v1/workbench.py:工作舱 API"
    "app/models/workbench.py:工作舱模型"
)

for item in "${workbenches[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((workbench_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((workbench_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

percentage=$(check_percentage $workbench_exists $workbench_total)
echo -e "Workbench 系统统计: ${GREEN}${workbench_exists}/${workbench_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== 双通道处理系统检测 ====================
echo -e "${CYAN}【第七部分】双通道处理系统检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

pipeline_total=0
pipeline_exists=0

echo "双通道核心:"
pipelines=(
    "app/services/clean_pipeline.py:干净数据通道"
    "app/services/dirty_pipeline.py:脏数据通道"
    "app/services/document_processor.py:文档处理器"
    "app/services/data_validator.py:数据验证器"
)

for item in "${pipelines[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((pipeline_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((pipeline_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

echo ""
echo "数据质量控制:"
pipelines=(
    "app/services/quality_control.py:质量控制"
    "app/services/data_cleaner.py:数据清洗"
    "app/services/validation_service.py:验证服务"
)

for item in "${pipelines[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((pipeline_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((pipeline_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

percentage=$(check_percentage $pipeline_exists $pipeline_total)
echo -e "双通道系统统计: ${GREEN}${pipeline_exists}/${pipeline_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== 自学习系统检测 ====================
echo -e "${PURPLE}【第八部分】自学习系统检测${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

learning_total=0
learning_exists=0

echo "自学习核心模块:"
learning=(
    "app/api/v1/learning.py:学习日志 API"
    "app/api/v1/feeding.py:用户喂养 API"
    "app/api/v1/annotation.py:用户标注 API"
    "app/api/v1/tagging.py:用户标签 API"
    "app/api/v1/execution_tracking.py:执行追踪 API"
    "app/api/v1/pattern_recognition.py:模式识别 API"
    "app/api/v1/feedback_loops.py:反馈闭环 API"
    "app/api/v1/background_learning.py:后台学习 API"
    "app/api/v1/experience_graph.py:经验图谱 API"
)

for item in "${learning[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    ((learning_total++))
    if [ -f "$BACKEND_ROOT/$file" ]; then
        ((learning_exists++))
        echo -e "${GREEN}✓${NC}   $desc"
    else
        echo -e "${RED}✗${NC}   $desc ${RED}(缺失)${NC}"
    fi
done

percentage=$(check_percentage $learning_exists $learning_total)
echo -e "自学习系统统计: ${GREEN}${learning_exists}/${learning_total}${NC} 完成度: ${percentage}"
echo ""

# ==================== 系统整体总结 ====================
echo ""
echo "============================================"
echo -e "   ${BLUE}系统整体完成度总结${NC}"
echo "============================================"
echo ""

total_all=$((frontend_total + agent_total + skill_total + workflow_total + hermes_total + workbench_total + pipeline_total + learning_total))
exists_all=$((frontend_exists + agent_exists + skill_exists + workflow_exists + hermes_exists + workbench_exists + pipeline_exists + learning_exists))

echo "各模块完成度汇总:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

modules=(
    "前端页面:$frontend_exists:$frontend_total"
    "Agent系统:$agent_exists:$agent_total"
    "Skill系统:$skill_exists:$skill_total"
    "工作流系统:$workflow_exists:$workflow_total"
    "Hermes治理:$hermes_exists:$hermes_total"
    "Workbench工作舱:$workbench_exists:$workbench_total"
    "双通道处理:$pipeline_exists:$pipeline_total"
    "自学习系统:$learning_exists:$learning_total"
)

for module in "${modules[@]}"; do
    IFS=':' read -r name exists total <<< "$module"
    percentage=$((exists * 100 / total))
    bar_length=$((percentage / 5))
    bar=$(printf "█%.0s" $(seq 1 $bar_length))
    empty=$(printf "░%.0s" $(seq 1 $((20 - bar_length))))

    if [ $percentage -ge 80 ]; then
        color=$GREEN
    elif [ $percentage -ge 50 ]; then
        color=$YELLOW
    else
        color=$RED
    fi

    printf "%-15s %s%s%s %s%3d%%%s (%d/%d)\n" "$name" "$bar" "$empty" "$NC" "$color" "$percentage" "$NC" "$exists" "$total"
done

echo ""
overall_percentage=$((exists_all * 100 / total_all))
echo -e "【系统整体完成度】 ${GREEN}${overall_percentage}%${NC} (${exists_all}/${total_all})"
echo ""

# 缺失模块统计
echo "缺失模块统计:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

missing_frontend=$((frontend_total - frontend_exists))
missing_agent=$((agent_total - agent_exists))
missing_skill=$((skill_total - skill_exists))
missing_workflow=$((workflow_total - workflow_exists))
missing_hermes=$((hermes_total - hermes_exists))
missing_workbench=$((workbench_total - workbench_exists))
missing_pipeline=$((pipeline_total - pipeline_exists))
missing_learning=$((learning_total - learning_exists))

echo -e "${RED}前端页面缺失:${NC} ${missing_frontend} 个"
echo -e "${RED}Agent 模块缺失:${NC} ${missing_agent} 个"
echo -e "${RED}Skill 模块缺失:${NC} ${missing_skill} 个"
echo -e "${RED}工作流模块缺失:${NC} ${missing_workflow} 个"
echo -e "${RED}Hermes 模块缺失:${NC} ${missing_hermes} 个"
echo -e "${RED}Workbench 模块缺失:${NC} ${missing_workbench} 个"
echo -e "${RED}双通道模块缺失:${NC} ${missing_pipeline} 个"
echo -e "${RED}自学习模块缺失:${NC} ${missing_learning} 个"

echo ""
echo "============================================"
