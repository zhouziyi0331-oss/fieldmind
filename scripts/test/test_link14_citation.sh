#!/bin/bash

BASE_URL="http://localhost:8000"
PROJECT_ID=1

echo "=========================================="
echo "链路十四测试：引用溯源系统"
echo "=========================================="

# 测试1：处理PDF文档（带页码）
echo ""
echo "1️⃣ 测试PDF文档处理（带页码元数据）"
PDF_RESULT=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/process" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 101,
    "text": "布依族是中国西南地区的少数民族，主要分布在贵州省。布依族有着悠久的历史和独特的文化传统。\n\n布依族的山歌艺术特别发达，分为情歌、劳动歌、叙事歌三种类型。山歌是布依族文化的重要组成部分。",
    "filename": "布依族文化研究报告.pdf",
    "file_type": "pdf",
    "project_id": '"$PROJECT_ID"',
    "page_number": 23,
    "source_level": 0,
    "tags": ["民族文化", "布依族"]
  }')

echo "$PDF_RESULT" | jq '.'

# 测试2：处理音频转录（带时间戳和说话人）
echo ""
echo "2️⃣ 测试音频转录处理（带时间戳和说话人）"
AUDIO_RESULT=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/process" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 102,
    "text": "我叫王大娘，今年68岁了。我从小就会唱山歌，我妈妈教我的。\n\n山歌啊，有三种：一种是情歌，年轻人谈恋爱唱的；一种是劳动歌，干活的时候唱；还有一种是叙事歌，讲故事的。",
    "filename": "访谈王大娘_20240315.mp3",
    "file_type": "mp3",
    "project_id": '"$PROJECT_ID"',
    "timestamp_start": 750.5,
    "timestamp_end": 780.3,
    "speaker": "王大娘",
    "document_date": "2024-03-15",
    "source_level": 0,
    "tags": ["田野调查", "口述史", "王大娘"]
  }')

echo "$AUDIO_RESULT" | jq '.'

# 测试3：处理二度报告（报告优先级）
echo ""
echo "3️⃣ 测试二度报告处理（链路17的基础）"
REPORT_RESULT=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/process" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 103,
    "text": "经过初步分析，布依族山歌传承面临以下问题：\n1. 年轻人不愿学习传统山歌\n2. 会唱的老人越来越少\n3. 缺乏系统的保护措施",
    "filename": "布依族山歌传承分析报告（二度）.docx",
    "file_type": "docx",
    "project_id": '"$PROJECT_ID"',
    "page_number": 5,
    "source_level": 2,
    "tags": ["分析报告", "二度报告", "非遗保护"]
  }')

echo "$REPORT_RESULT" | jq '.'

# 等待向量化完成
echo ""
echo "⏳ 等待向量化完成..."
sleep 5

# 测试4：带引用的检索（核心功能）
echo ""
echo "4️⃣ 带引用的检索测试"
echo "查询: 山歌有哪些类型？"
SEARCH_RESULT=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/search-with-citation" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "山歌有哪些类型",
    "project_id": '"$PROJECT_ID"',
    "n_results": 3,
    "include_citation": true
  }')

echo "$SEARCH_RESULT" | jq '.results[] | {text: .text[0:100], citation: .citation, source_file: .metadata.source_file}'

# 测试5：按文档类型过滤检索
echo ""
echo "5️⃣ 只检索音频来源"
AUDIO_ONLY=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/search-with-citation" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "布依族",
    "project_id": '"$PROJECT_ID"',
    "n_results": 2,
    "document_types": ["audio"],
    "include_citation": true
  }')

echo "$AUDIO_ONLY" | jq '.results[] | {citation: .citation, speaker: .metadata.speaker}'

# 测试6：按来源层级过滤（只检索报告）
echo ""
echo "6️⃣ 只检索报告层级（source_level >= 1）"
REPORT_ONLY=$(curl -s -X POST "$BASE_URL/api/document-processing-v2/search-with-citation" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "山歌传承",
    "project_id": '"$PROJECT_ID"',
    "n_results": 2,
    "source_levels": [1, 2, 3],
    "include_citation": true
  }')

echo "$REPORT_ONLY" | jq '.results[] | {citation: .citation, source_level: .metadata.source_level}'

# 测试7：获取chunk详情（模拟点击引用跳转）
echo ""
echo "7️⃣ 获取chunk详情（点击引用跳转）"
CHUNK_ID="doc102_chunk0000"
curl -s "$BASE_URL/api/document-processing-v2/chunk/$CHUNK_ID" | jq '.'

# 测试8：元数据完整度统计
echo ""
echo "8️⃣ 获取项目元数据统计"
curl -s "$BASE_URL/api/document-processing-v2/metadata-stats/$PROJECT_ID" | jq '.'

echo ""
echo "=========================================="
echo "✅ 链路十四测试完成"
echo "=========================================="
echo ""
echo "📋 验收要点："
echo "  ✓ PDF引用显示页码：[来源：xxx.pdf P23]"
echo "  ✓ 音频引用显示时间戳+说话人：[来源：xxx.mp3 王大娘 12:30-13:00]"
echo "  ✓ 报告引用标注层级：[来源：二度报告 xxx P5]"
echo "  ✓ 检索结果可按文档类型过滤"
echo "  ✓ 检索结果可按来源层级过滤（为链路17铺垫）"
echo ""
