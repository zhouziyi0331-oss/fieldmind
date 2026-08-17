#!/bin/bash

echo "=========================================="
echo "  FieldMind 认证系统测试脚本"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000/api"

# 测试1: 注册新用户
echo "📝 测试1: 用户注册"
echo "----------------------------------------"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "password123"
  }')

echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"
echo ""

# 测试2: 登录获取token
echo "🔐 测试2: 用户登录"
echo "----------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123"
  }')

echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

# 提取access_token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
echo ""

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ 无法获取access_token，使用已有用户测试"
    # 使用已有用户登录
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "testuser",
        "password": "testpass"
      }')

    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    echo ""
fi

# 测试3: 获取当前用户信息
echo "👤 测试3: 获取当前用户信息"
echo "----------------------------------------"
if [ -n "$ACCESS_TOKEN" ]; then
    USER_INFO=$(curl -s -X GET "$BASE_URL/auth/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    echo "$USER_INFO" | python3 -m json.tool 2>/dev/null || echo "$USER_INFO"
else
    echo "❌ 没有有效的access_token"
fi
echo ""

# 测试4: 访问受保护的项目列表
echo "📁 测试4: 访问受保护的项目列表"
echo "----------------------------------------"
if [ -n "$ACCESS_TOKEN" ]; then
    PROJECTS=$(curl -s -X GET "$BASE_URL/projects" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    echo "$PROJECTS" | python3 -m json.tool 2>/dev/null || echo "$PROJECTS"
else
    echo "❌ 没有有效的access_token"
fi
echo ""

# 测试5: 无token访问（应该失败）
echo "🚫 测试5: 无token访问（应该返回401）"
echo "----------------------------------------"
UNAUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/projects")
echo "$UNAUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UNAUTH_RESPONSE"
echo ""

# 测试6: 错误的密码
echo "❌ 测试6: 错误的密码（应该失败）"
echo "----------------------------------------"
WRONG_PASS=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "wrongpassword"
  }')

echo "$WRONG_PASS" | python3 -m json.tool 2>/dev/null || echo "$WRONG_PASS"
echo ""

echo "=========================================="
echo "  测试完成"
echo "=========================================="
