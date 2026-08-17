#!/bin/bash

# FieldMind API 测试脚本
# 演示完整的项目隔离、文档上传、AI对话和技能框架功能

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api"

echo "========================================"
echo "FieldMind API 功能测试"
echo "========================================"
echo ""

# 1. 创建新项目
echo "1. 创建新项目..."
PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "田野调查示例项目",
    "description": "这是一个用于演示的田野调查项目，包含人类学研究资料"
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ 项目创建成功，ID: $PROJECT_ID"
echo ""

# 2. 查看项目详情
echo "2. 查看项目详情..."
curl -s "$API_URL/projects/$PROJECT_ID" | python3 -m json.tool
echo ""

# 3. 创建测试文档
echo "3. 创建测试文档并上传..."
cat > /tmp/test_document.txt << 'EOF'
# 田野调查笔记

## 调查地点
某村落，位于山区，人口约500人

## 调查时间
2026年7月

## 主要发现
1. 当地保留了传统的节日庆祝方式
2. 年轻人大多外出务工，留守老人和儿童居多
3. 村落建筑以传统木结构为主
4. 村民主要收入来源于农业和外出务工

## 关键信息
- 村长：张三，60岁
- 主要作物：水稻、玉米
- 特色产业：竹编工艺品
- 教育：一所小学，约50名学生

## 待深入研究的问题
1. 传统文化的传承机制
2. 外出务工对村落社会结构的影响
3. 现代化进程中的文化适应
EOF

curl -s -X POST "$API_URL/documents/upload?project_id=$PROJECT_ID" \
  -F "file=@/tmp/test_document.txt" | python3 -m json.tool
echo ""

# 4. 创建AI对话会话
echo "4. 创建AI对话会话..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/chat/sessions" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": $PROJECT_ID,
    \"name\": \"田野调查分析对话\"
  }")

SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ 对话会话创建成功，ID: $SESSION_ID"
echo ""

# 5. 发送消息测试AI对话
echo "5. 发送消息测试AI对话..."
echo "提问: 根据我的田野调查资料，这个村落面临的主要社会问题是什么？"
echo ""

curl -s -X POST "$API_URL/chat/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "根据我的田野调查资料，这个村落面临的主要社会问题是什么？请结合长记忆进行深度分析。"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print('AI回复:\n' + data['content']); print('\n思考过程:\n' + (data.get('thinking_process', '无') or '无')[:200] + '...')"
echo ""

# 6. 运行智能分析生成技能框架
echo "6. 运行项目智能分析（生成AI技能框架）..."
curl -s -X POST "$API_URL/projects/$PROJECT_ID/analyze" | python3 -m json.tool
echo ""

# 7. 查看项目统计
echo "7. 查看项目统计数据..."
curl -s "$API_URL/projects/$PROJECT_ID/stats" | python3 -m json.tool
echo ""

echo "========================================"
echo "测试完成！"
echo "========================================"
echo ""
echo "📝 访问 API 文档: $BASE_URL/docs"
echo "🌐 访问前端界面: http://localhost:3000"
echo "📊 查看项目详情: http://localhost:3000/projects/$PROJECT_ID"
echo ""
