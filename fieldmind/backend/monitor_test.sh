#!/bin/bash
# 监控 TranscriptAgent 测试进度

OUTPUT_FILE="/private/tmp/claude-501/-Users-alwan/6af2ff03-2884-4d29-abb5-e1ff6948f6c7/tasks/b62js5xjl.output"

while true; do
    # 检查测试是否完成
    if grep -q "测试完成！TranscriptAgent 完整链路正常工作" "$OUTPUT_FILE" 2>/dev/null; then
        echo "✅ 测试完成！"
        echo ""
        echo "=== 最终结果 ==="
        tail -30 "$OUTPUT_FILE"
        break
    fi

    # 显示当前进度
    PROGRESS=$(tail -1 "$OUTPUT_FILE" 2>/dev/null | grep -o '[0-9]\+%' | head -1)
    if [ -n "$PROGRESS" ]; then
        echo "转录进度: $PROGRESS"
    fi

    sleep 30
done
