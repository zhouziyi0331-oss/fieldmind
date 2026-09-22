#!/bin/bash
# FieldMind 文件合并执行脚本
# 生成时间：2026-09-18

set -e  # 遇到错误立即退出

MAIN_DIR="/Users/alwan/FieldMind"
FIELDMIND_DIR="/Users/alwan/FieldMind/fieldmind"
BACKUP_NAME="FieldMind_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "======================================"
echo "FieldMind 文件合并脚本"
echo "======================================"
echo ""

# 步骤1：备份主程序
echo "步骤1：备份主程序到 ~/$BACKUP_NAME"
cd /Users/alwan
tar -czf "$BACKUP_NAME" FieldMind/ --exclude=node_modules --exclude=__pycache__ --exclude=.git --exclude=venv
echo "✅ 备份完成: $(du -h $BACKUP_NAME | cut -f1)"
echo ""

# 步骤2：创建合并目录
echo "步骤2：准备合并目录"
cd "$MAIN_DIR"
mkdir -p merged_files
mkdir -p merged_files/services
mkdir -p merged_files/api
mkdir -p merged_files/models
echo "✅ 目录创建完成"
echo ""

# 步骤3：合并P0关键服务 - Knowledge Pipeline
echo "步骤3：合并Knowledge Pipeline (21个文件)"
if [ -d "$FIELDMIND_DIR/backend/src/app/services/knowledge_pipeline" ]; then
    cp -r "$FIELDMIND_DIR/backend/src/app/services/knowledge_pipeline" merged_files/services/
    echo "✅ Knowledge Pipeline 已复制到 merged_files/services/"
else
    echo "❌ 找不到 knowledge_pipeline 目录"
fi
echo ""

# 步骤4：合并Document Normalization
echo "步骤4：合并Document Normalization (4个文件)"
if [ -d "$FIELDMIND_DIR/backend/src/app/services/document_normalization" ]; then
    cp -r "$FIELDMIND_DIR/backend/src/app/services/document_normalization" merged_files/services/
    echo "✅ Document Normalization 已复制到 merged_files/services/"
else
    echo "❌ 找不到 document_normalization 目录"
fi
echo ""

# 步骤5：合并Event Handlers
echo "步骤5：合并Event Handlers (3个文件)"
if [ -d "$FIELDMIND_DIR/backend/src/app/services/event_handlers" ]; then
    cp -r "$FIELDMIND_DIR/backend/src/app/services/event_handlers" merged_files/services/
    echo "✅ Event Handlers 已复制到 merged_files/services/"
else
    echo "❌ 找不到 event_handlers 目录"
fi
echo ""

# 步骤6：合并Event Bus
echo "步骤6：合并Event Bus"
if [ -f "$FIELDMIND_DIR/backend/src/app/services/event_bus.py" ]; then
    cp "$FIELDMIND_DIR/backend/src/app/services/event_bus.py" merged_files/services/
    echo "✅ event_bus.py 已复制"
else
    echo "❌ 找不到 event_bus.py"
fi
echo ""

# 步骤7：合并Knowledge Graph扩展
echo "步骤7：合并Knowledge Graph扩展 (4个文件)"
if [ -f "$FIELDMIND_DIR/backend/src/app/services/knowledge_graph/kg_analysis_service.py" ]; then
    mkdir -p merged_files/services/knowledge_graph
    cp "$FIELDMIND_DIR/backend/src/app/services/knowledge_graph/kg_analysis_service.py" merged_files/services/knowledge_graph/
    cp "$FIELDMIND_DIR/backend/src/app/services/knowledge_graph/kg_query_service.py" merged_files/services/knowledge_graph/
    cp "$FIELDMIND_DIR/backend/src/app/services/knowledge_graph/kg_visualization_api.py" merged_files/services/knowledge_graph/
    cp "$FIELDMIND_DIR/backend/src/app/services/knowledge_graph/unified_query_interface.py" merged_files/services/knowledge_graph/
    echo "✅ Knowledge Graph扩展已复制 (4个文件)"
else
    echo "⚠️ Knowledge Graph扩展文件可能不存在"
fi
echo ""

# 步骤8：合并API文件
echo "步骤8：合并API文件"
API_FILES=(
    "knowledge_pipeline.py"
    "document_normalization.py"
    "monitoring_api.py"
    "reader.py"
    "knowledge_query.py"
)

for file in "${API_FILES[@]}"; do
    if [ -f "$FIELDMIND_DIR/backend/src/app/api/$file" ]; then
        cp "$FIELDMIND_DIR/backend/src/app/api/$file" merged_files/api/
        echo "✅ 已复制 $file"
    else
        echo "⚠️ 找不到 $file"
    fi
done
echo ""

# 步骤9：合并数据库模型
echo "步骤9：合并数据库模型"
if [ -f "$FIELDMIND_DIR/backend/src/app/models/knowledge.py" ]; then
    cp "$FIELDMIND_DIR/backend/src/app/models/knowledge.py" merged_files/models/
    echo "✅ knowledge.py 已复制"
else
    echo "❌ 找不到 models/knowledge.py"
fi
echo ""

# 步骤10：合并其他关键服务
echo "步骤10：合并其他关键服务"
OTHER_SERVICES=(
    "performance_monitor.py"
    "rag_integration_service.py"
    "chunk_enricher.py"
    "boundary1_validator.py"
    "boundary1_validator_v2.py"
    "boundary2_validator.py"
    "boundary2_validator_v2.py"
    "data_contract_validator.py"
    "cache_optimization.py"
)

for file in "${OTHER_SERVICES[@]}"; do
    if [ -f "$FIELDMIND_DIR/backend/src/app/services/$file" ]; then
        cp "$FIELDMIND_DIR/backend/src/app/services/$file" merged_files/services/
        echo "✅ 已复制 $file"
    else
        echo "⚠️ 找不到 $file"
    fi
done
echo ""

# 步骤11：生成合并报告
echo "步骤11：生成合并报告"
cat > merged_files/MERGE_REPORT.txt << EOF
FieldMind 文件合并报告
生成时间: $(date)

合并的文件统计：
- 服务目录数: $(find merged_files/services -type d | wc -l)
- 服务文件数: $(find merged_files/services -type f -name "*.py" | wc -l)
- API文件数: $(find merged_files/api -type f -name "*.py" | wc -l)
- 模型文件数: $(find merged_files/models -type f -name "*.py" | wc -l)

详细文件清单：
$(find merged_files -type f -name "*.py" | sort)

备份位置：
~/$BACKUP_NAME
EOF

cat merged_files/MERGE_REPORT.txt
echo ""

echo "======================================"
echo "✅ 文件合并准备完成！"
echo "======================================"
echo ""
echo "下一步操作："
echo "1. 检查 merged_files/ 目录中的文件"
echo "2. 确认无误后，将文件复制到主程序对应位置"
echo "3. 更新 backend/src/app/main.py 注册新路由"
echo "4. 运行数据库迁移脚本"
echo "5. 测试API可用性"
echo ""
echo "回滚方法（如果需要）："
echo "cd /Users/alwan && tar -xzf $BACKUP_NAME"
