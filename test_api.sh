#!/bin/bash

echo "🧪 测试 FieldMind 后端 API..."
echo ""

BASE_URL="http://localhost:8000"

# 1. 健康检查
echo "1️⃣  健康检查:"
curl -s $BASE_URL/health | jq '.'
echo ""

# 2. 获取 API 信息
echo "2️⃣  API 信息:"
curl -s $BASE_URL/ | jq '.'
echo ""

# 3. 注册用户
echo "3️⃣  注册新用户:"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "Test User"
  }')
echo $REGISTER_RESPONSE | jq '.'
echo ""

# 4. 登录获取 token
echo "4️⃣  用户登录:"
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }')
echo $LOGIN_RESPONSE | jq '.'

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo ""
echo "Token: $TOKEN"
echo ""

# 5. 获取当前用户信息
echo "5️⃣  获取用户信息:"
curl -s $BASE_URL/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# 6. 创建项目
echo "6️⃣  创建项目:"
PROJECT_RESPONSE=$(curl -s -X POST $BASE_URL/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试项目"
  }')
echo $PROJECT_RESPONSE | jq '.'

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.id')
echo ""
echo "Project ID: $PROJECT_ID"
echo ""

# 7. 获取项目列表
echo "7️⃣  获取项目列表:"
curl -s $BASE_URL/api/projects \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

echo "✅ API 测试完成！"
