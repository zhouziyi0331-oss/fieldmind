#!/bin/bash
echo "🔍 扫描电脑里所有 FieldMind 相关目录..."
echo ""

# 常见位置
SEARCH_PATHS=(
    "$HOME"
    "$HOME/Desktop"
    "$HOME/Documents"
    "$HOME/Projects"
    "$HOME/Developer"
    "$HOME/code"
    "/Applications"
)

for path in "${SEARCH_PATHS[@]}"; do
    if [ -d "$path" ]; then
        find "$path" -maxdepth 3 -type d \( -iname "*fieldmind*" -o -iname "*field_mind*" \) 2>/dev/null
    fi
done | sort -u > /tmp/fieldmind_instances.txt

echo "找到以下实例："
cat /tmp/fieldmind_instances.txt
echo ""

# 分析每个实例
while IFS= read -r dir; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📁 $dir"
    echo "   大小: $(du -sh "$dir" 2>/dev/null | cut -f1)"
    echo "   最后修改: $(stat -f "%Sm" "$dir" 2>/dev/null)"
    echo "   文件数: $(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')"

    # 检查是否是git仓库
    if [ -d "$dir/.git" ]; then
        echo "   Git: $(cd "$dir" && git log -1 --format='%h %s' 2>/dev/null | head -1)"
    fi

    # 检查关键文件
    [ -f "$dir/requirements.txt" ] && echo "   ✓ requirements.txt"
    [ -f "$dir/app.py" ] && echo "   ✓ app.py"
    [ -f "$dir/main.py" ] && echo "   ✓ main.py"
    [ -d "$dir/frontend" ] && echo "   ✓ frontend/"
    [ -d "$dir/services" ] && echo "   ✓ services/"
done < /tmp/fieldmind_instances.txt
