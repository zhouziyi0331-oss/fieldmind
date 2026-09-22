#!/bin/bash
# 直接运行可执行文件，绕过App Sandbox

echo "停止所有现有实例..."
pkill -9 FieldMindNative 2>/dev/null
   
echo "编译..."
swift build -c release

echo "直接运行可执行文件（无沙盒限制）..."
.build/release/FieldMindNative
