#!/bin/bash

# 删除苹果系统自带应用脚本
# 使用前必须先关闭SIP（系统完整性保护）

echo "========================================"
echo "删除苹果系统自带应用"
echo "========================================"
echo ""

# 检查SIP状态
SIP_STATUS=$(csrutil status | grep -o "enabled\|disabled")
if [ "$SIP_STATUS" == "enabled" ]; then
    echo "❌ 错误：SIP（系统完整性保护）仍然开启"
    echo ""
    echo "请按以下步骤关闭SIP："
    echo "1. 重启 Mac，按住 Command + R 进入恢复模式"
    echo "2. 选择 实用工具 > 终端"
    echo "3. 输入：csrutil disable"
    echo "4. 重启后再运行此脚本"
    echo ""
    exit 1
fi

echo "✅ SIP 已关闭，可以删除系统应用"
echo ""

# 要删除的应用列表
apps=(
    "/System/Applications/Podcasts.app"
    "/System/Applications/Chess.app"
    "/System/Applications/Stocks.app"
    "/System/Applications/TV.app"
    "/System/Applications/Games.app"
    "/System/Applications/Weather.app"
)

# 删除应用
for app in "${apps[@]}"; do
    if [ -d "$app" ]; then
        echo "正在删除: $app"
        sudo rm -rf "$app"
        if [ $? -eq 0 ]; then
            echo "✅ 已删除: $(basename "$app")"
        else
            echo "❌ 删除失败: $(basename "$app")"
        fi
    else
        echo "⚠️  未找到: $(basename "$app")"
    fi
    echo ""
done

echo "========================================"
echo "删除完成！"
echo "========================================"
echo ""
echo "⚠️  重要提示："
echo "为了系统安全，建议重新开启SIP："
echo "1. 重启 Mac，按住 Command + R 进入恢复模式"
echo "2. 选择 实用工具 > 终端"
echo "3. 输入：csrutil enable"
echo "4. 重启"
echo ""
