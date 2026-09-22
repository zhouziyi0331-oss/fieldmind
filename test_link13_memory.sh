#!/bin/bash

BASE_URL="http://localhost:8000"
PROJECT_ID=1

echo "=========================================="
echo "链路十三测试：Agent记忆绑定"
echo "=========================================="

# 1. 创建长期记忆
echo ""
echo "1️⃣ 创建长期记忆（核心知识）"
LONG_MEMORY=$(curl -s -X POST "$BASE_URL/api/memory/create" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '"$PROJECT_ID"',
    "memory_type": "long_term",
    "content": "用户偏好：在分析布依族文化时，特别关注山歌传承和非物质文化遗产保护。用户是研究员，需要学术性的分析。",
    "summary": "用户研究偏好：布依族山歌、非遗保护",
    "source_type": "manual",
    "keywords": ["布依族", "山歌", "非遗保护", "学术分析"],
    "importance_score": 0.9
  }')

echo "$LONG_MEMORY" | jq '.'
LONG_MEMORY_ID=$(echo "$LONG_MEMORY" | jq -r '.id')

# 2. 创建中期记忆
echo ""
echo "2️⃣ 创建中期记忆（重要概念）"
MID_MEMORY=$(curl -s -X POST "$BASE_URL/api/memory/create" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '"$PROJECT_ID"',
    "memory_type": "mid_term",
    "content": "项目焦点：贵州省黔南州布依族村寨，特别关注王大娘（68岁）的山歌传承经验。调查时间为2024年3月15日。",
    "summary": "黔南州布依族村寨调查，王大娘山歌传承",
    "source_type": "document",
    "keywords": ["黔南州", "王大娘", "山歌传承"],
    "importance_score": 0.7
  }')

echo "$MID_MEMORY" | jq '.'

# 3. 创建短期记忆
echo ""
echo "3️⃣ 创建短期记忆（最近上下文）"
SHORT_MEMORY=$(curl -s -X POST "$BASE_URL/api/memory/create" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '"$PROJECT_ID"',
    "memory_type": "short_term",
    "content": "用户刚刚询问了关于山歌三种类型的问题，特别关注情歌、劳动歌和叙事歌的区别。",
    "summary": "近期关注：山歌三种类型",
    "source_type": "chat",
    "importance_score": 0.5
  }')

echo "$SHORT_MEMORY" | jq '.'

# 4. 获取项目记忆列表
echo ""
echo "4️⃣ 获取项目所有记忆"
curl -s "$BASE_URL/api/memory/project/$PROJECT_ID?limit=10" | jq '.'

# 5. 构建包含记忆的系统提示词（核心功能）
echo ""
echo "5️⃣ 构建记忆增强的系统提示词（链路十三核心）"
curl -s -X POST "$BASE_URL/api/memory/build-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '"$PROJECT_ID"',
    "base_prompt": "你是一个专业的田野调查分析助手，帮助研究员分析民族文化数据。",
    "user_query": "布依族山歌",
    "include_short_term": true,
    "include_mid_term": true,
    "include_long_term": true,
    "max_memories": 10
  }' | jq '.'

# 6. 升级记忆层级
echo ""
echo "6️⃣ 升级短期记忆到中期"
curl -s -X POST "$BASE_URL/api/memory/promote" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": '"$LONG_MEMORY_ID"',
    "target_type": "long_term"
  }' | jq '.'

# 7. 获取记忆统计
echo ""
echo "7️⃣ 获取记忆统计信息"
curl -s "$BASE_URL/api/memory/stats/$PROJECT_ID" | jq '.'

# 8. 自动升级高价值记忆
echo ""
echo "8️⃣ 自动升级高价值记忆"
curl -s -X POST "$BASE_URL/api/memory/auto-promote/$PROJECT_ID" | jq '.'

# 9. 获取长期记忆列表
echo ""
echo "9️⃣ 获取长期记忆列表"
curl -s "$BASE_URL/api/memory/project/$PROJECT_ID?memory_type=long_term&limit=5" | jq '.'

# 10. 测试记忆注入效果
echo ""
echo "🔟 测试：查看完整的记忆增强提示词"
ENHANCED_PROMPT=$(curl -s -X POST "$BASE_URL/api/memory/build-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '"$PROJECT_ID"',
    "base_prompt": "你是一个AI助手。",
    "user_query": "山歌传承",
    "include_short_term": true,
    "include_mid_term": true,
    "include_long_term": true,
    "max_memories": 5
  }')

echo "$ENHANCED_PROMPT" | jq -r '.enhanced_prompt' | head -50

echo ""
echo "=========================================="
echo "✅ 链路十三测试完成"
echo "=========================================="
