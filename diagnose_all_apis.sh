#!/bin/bash
# 完整诊断脚本 - 测试所有API并生成报告

echo "=================================="
echo "FieldMind API 完整诊断"
echo "=================================="
echo ""

BASE_URL="http://127.0.0.1:8013"

# 测试函数
test_api() {
    local name=$1
    local url=$2

    echo "测试: $name"
    echo "URL: $url"

    response=$(curl -s "$url")
    status=$?

    if [ $status -eq 0 ]; then
        echo "✅ 请求成功"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -30
    else
        echo "❌ 请求失败"
    fi
    echo ""
    echo "---"
    echo ""
}

# 测试所有API
test_api "照片列表" "$BASE_URL/api/photos?project_id=1&page=1&page_size=10"
test_api "照片统计" "$BASE_URL/api/photos/stats/1"
test_api "表格列表" "$BASE_URL/api/v1/projects/1/tables/"
test_api "表格统计" "$BASE_URL/api/v1/projects/1/tables/statistics/"
test_api "文件树" "$BASE_URL/api/file-tree/1"

echo "=================================="
echo "诊断完成"
echo "=================================="
