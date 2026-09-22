#!/bin/bash
# 前端构建脚本

set -e

echo "开始构建前端..."

if [ -d "web" ]; then
    cd web
    echo "安装依赖..."
    npm install
    echo "构建生产版本..."
    npm run build
    echo "✓ 前端构建完成"
    echo "输出目录: frontend/web/dist"
else
    echo "警告: frontend/web 目录不存在"
fi
