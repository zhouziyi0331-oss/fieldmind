#!/bin/bash
# FieldMind 测试套件执行脚本

echo "=========================================="
echo "🧪 FieldMind 测试套件"
echo "=========================================="
echo ""

# 检查后端是否运行
echo "检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行中"
else
    echo "❌ 后端服务未运行，请先启动:"
    echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "=========================================="
echo "测试 1: 前端集成测试"
echo "=========================================="
python3 test_frontend_integration.py
TEST1_RESULT=$?

echo ""
echo "=========================================="
echo "测试 2: 反幻觉四锁验证"
echo "=========================================="
python3 test_anti_hallucination.py
TEST2_RESULT=$?

echo ""
echo "=========================================="
echo "测试 3: API端到端测试"
echo "=========================================="
python3 test_api_e2e.py
TEST3_RESULT=$?

echo ""
echo "=========================================="
echo "📊 测试总结"
echo "=========================================="

TOTAL_TESTS=3
PASSED_TESTS=0

if [ $TEST1_RESULT -eq 0 ]; then
    echo "✅ 前端集成测试: PASSED"
    ((PASSED_TESTS++))
else
    echo "❌ 前端集成测试: FAILED"
fi

if [ $TEST2_RESULT -eq 0 ]; then
    echo "✅ 反幻觉四锁验证: PASSED"
    ((PASSED_TESTS++))
else
    echo "❌ 反幻觉四锁验证: FAILED"
fi

if [ $TEST3_RESULT -eq 0 ]; then
    echo "✅ API端到端测试: PASSED"
    ((PASSED_TESTS++))
else
    echo "❌ API端到端测试: FAILED"
fi

echo ""
echo "通过: $PASSED_TESTS/$TOTAL_TESTS"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "🎉 所有测试通过！"
    exit 0
else
    echo "⚠️  部分测试失败，请查看详细报告"
    exit 1
fi
