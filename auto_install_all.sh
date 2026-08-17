#!/bin/bash

# FieldMind 自动安装全部22个组件
# 持续运行直到全部完成

cd /Users/alwan/FieldMind-Rebuild

echo "🚀 开始自动安装 FieldMind 全部22个组件"
echo "开始时间: $(date)"
echo ""

install_count=0
max_attempts=30

while [ $install_count -lt $max_attempts ]; do
    # 检查当前已安装数量
    current=$(ls -1 repos/ 2>/dev/null | grep -v "^\." | wc -l | tr -d ' ')

    if [ "$current" -ge 22 ]; then
        echo ""
        echo "🎉 全部22个组件安装完成！"
        echo "完成时间: $(date)"

        echo ""
        echo "📊 安装摘要:"
        ls -1 repos/ | grep -v "^\." | nl

        echo ""
        echo "📝 生成的日志文件:"
        ls -1 logs/*.log 2>/dev/null | xargs -n1 basename | nl

        exit 0
    fi

    echo "[$((install_count+1))/$max_attempts] 当前进度: $current/22"
    echo "运行下一个安装..."

    # 运行安装脚本
    ./install_one_by_one.sh

    # 检查是否成功
    new_count=$(ls -1 repos/ 2>/dev/null | grep -v "^\." | wc -l | tr -d ' ')

    if [ "$new_count" -gt "$current" ]; then
        echo "✅ 成功安装 1 个组件 ($current → $new_count)"
        install_count=0  # 重置计数器
    else
        echo "⏳ 等待克隆完成..."
        install_count=$((install_count + 1))
        sleep 10
    fi

    echo ""
done

echo "❌ 安装超时或失败"
echo "当前进度: $(ls -1 repos/ 2>/dev/null | grep -v "^\." | wc -l | tr -d ' ')/22"
exit 1
