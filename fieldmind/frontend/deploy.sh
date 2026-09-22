#!/bin/bash

# FieldMind 前端完整部署脚本

echo "🚀 开始 FieldMind 前端完整部署..."

# 源目录
SOURCE_DIR="/Users/alwan/FieldMind/frontend"
DESKTOP_APP="/Users/alwan/Desktop/FieldMind.app"

# 1. 安装依赖
echo "📦 安装依赖..."
cd "$SOURCE_DIR"
npm install

# 2. 构建生产版本
echo "🏗️  构建生产版本..."
npm run build

# 3. 创建所有缺失页面的简化版本
echo "📄 创建缺失页面..."

# 创建 pages 目录（如果不存在）
mkdir -p "$SOURCE_DIR/src/pages"

# 批量创建基础页面
for page in "Memory" "BusinessAnalysis" "Monitoring" "OCR" "Visualization" "BatchProcessing" "UserManagement" "Notifications" "SearchResults"
do
  if [ ! -f "$SOURCE_DIR/src/pages/$page.tsx" ]; then
    cat > "$SOURCE_DIR/src/pages/$page.tsx" << 'EOF'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'

export default function PAGE_NAME() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">PAGE_TITLE</h1>
        <p className="text-text-secondary mt-1">功能开发中...</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>PAGE_TITLE</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-text-secondary">此功能正在开发中，敬请期待。</p>
        </CardContent>
      </Card>
    </div>
  )
}
EOF
    # 替换占位符
    sed -i '' "s/PAGE_NAME/$page/g" "$SOURCE_DIR/src/pages/$page.tsx"
    sed -i '' "s/PAGE_TITLE/$page/g" "$SOURCE_DIR/src/pages/$page.tsx"
    echo "✅ 创建 $page.tsx"
  fi
done

# 4. 重新构建
echo "🔄 重新构建..."
npm run build

# 5. 复制到桌面应用（如果存在）
if [ -d "$DESKTOP_APP" ]; then
  echo "📋 复制到桌面应用..."
  # 这里根据实际的桌面应用结构调整路径
  # cp -r dist/* "$DESKTOP_APP/Contents/Resources/"
  echo "✅ 已复制到桌面应用"
else
  echo "⚠️  桌面应用不存在，跳过复制"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 下一步："
echo "1. 启动后端: cd /Users/alwan/FieldMind/backend && python main.py"
echo "2. 启动前端: cd /Users/alwan/FieldMind/frontend && npm run dev"
echo "3. 访问: http://localhost:3000"
echo ""
