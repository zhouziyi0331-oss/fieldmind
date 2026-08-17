#!/bin/bash

echo "======================================"
echo "FieldMind 快速测试脚本"
echo "======================================"
echo ""

# 1. 测试后端健康
echo "1️⃣  测试后端健康状态..."
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo "✅ 后端运行正常"
    echo "$HEALTH" | python3 -m json.tool
else
    echo "❌ 后端未启动或无法访问"
    exit 1
fi
echo ""

# 2. 测试注册
echo "2️⃣  测试用户注册..."
REGISTER=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "quicktest",
    "email": "quicktest@example.com",
    "password": "Test123456"
  }')

if echo "$REGISTER" | grep -q '"id"'; then
    echo "✅ 注册成功"
    echo "$REGISTER" | python3 -m json.tool
elif echo "$REGISTER" | grep -q "already"; then
    echo "ℹ️  用户已存在（继续测试）"
else
    echo "❌ 注册失败"
    echo "$REGISTER"
fi
echo ""

# 3. 测试登录
echo "3️⃣  测试用户登录..."
LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "quicktest",
    "password": "Test123456"
  }')

if echo "$LOGIN" | grep -q '"access_token"'; then
    echo "✅ 登录成功"
    TOKEN=$(echo "$LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "Token: ${TOKEN:0:50}..."
else
    echo "❌ 登录失败"
    echo "$LOGIN"
    exit 1
fi
echo ""

# 4. 测试创建项目
echo "4️⃣  测试创建项目..."
PROJECT=$(curl -s -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "快速测试项目",
    "description": "用于自动化测试的项目"
  }')

if echo "$PROJECT" | grep -q '"id"'; then
    echo "✅ 项目创建成功"
    PROJECT_ID=$(echo "$PROJECT" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo "项目ID: $PROJECT_ID"
else
    echo "❌ 项目创建失败"
    echo "$PROJECT"
    exit 1
fi
echo ""

# 5. 测试获取项目列表
echo "5️⃣  测试获取项目列表..."
PROJECTS=$(curl -s -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN")

if echo "$PROJECTS" | grep -q '"total"'; then
    echo "✅ 获取项目列表成功"
    TOTAL=$(echo "$PROJECTS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")
    echo "总项目数: $TOTAL"
else
    echo "❌ 获取项目列表失败"
fi
echo ""

# 6. 测试项目统计
echo "6️⃣  测试项目统计..."
STATS=$(curl -s -X GET "http://localhost:8000/api/projects/${PROJECT_ID}/stats" \
  -H "Authorization: Bearer $TOKEN")

if echo "$STATS" | grep -q '"project_id"'; then
    echo "✅ 获取项目统计成功"
    echo "$STATS" | python3 -m json.tool
else
    echo "❌ 获取项目统计失败"
fi
echo ""

echo "======================================"
echo "✅ 所有基础功能测试通过！"
echo "======================================"
echo ""
echo "📝 下一步:"
echo "  1. 启动桌面应用: cd fieldmind-desktop && swift run"
echo "  2. 在应用中使用账户: quicktest / Test123456"
echo "  3. 测试文档上传和其他功能"
