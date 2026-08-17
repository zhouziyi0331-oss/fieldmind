#!/bin/bash

# 简单的进度监控脚本
cd /Users/alwan/FieldMind-Rebuild

while true; do
    clear
    echo "==================================="
    echo "  FieldMind 安装进度监控"
    echo "==================================="
    echo ""

    # 统计已安装数量
    count=$(ls -1 repos/ 2>/dev/null | grep -v "^\." | wc -l | tr -d ' ')
    echo "📊 进度: $count/22"
    echo ""

    # 列出已安装的组件
    echo "✅ 已安装组件:"
    ls -1 repos/ 2>/dev/null | grep -v "^\." | nl
    echo ""

    # 显示各组件大小
    echo "💾 仓库大小:"
    du -sh repos/* 2>/dev/null
    echo ""

    # 检查是否有git clone进程
    if ps aux | grep "git clone" | grep -v grep > /dev/null; then
        echo "🔄 正在克隆仓库..."
        ps aux | grep "git clone" | grep -v grep | awk '{print $NF}'
    else
        echo "⏸️  等待下一个安装..."
    fi

    echo ""
    echo "⏰ $(date '+%H:%M:%S')"
    echo ""
    echo "按 Ctrl+C 停止监控"

    sleep 10
done
