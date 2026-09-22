#!/bin/bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/.runtime/backend.pid"
LAUNCH_AGENT_LABEL="com.fieldmind.backend.v3"
LAUNCH_AGENT_PLIST="$HOME/Library/LaunchAgents/${LAUNCH_AGENT_LABEL}.plist"
BACKEND_PORT="${FIELDMIND_PORT:-8013}"

echo "🛑 停止 FieldMind..."

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        echo "✅ 已停止后端 PID: $PID"
    fi
    rm -f "$PID_FILE"
fi

launchctl bootout "gui/$(id -u)" "$LAUNCH_AGENT_PLIST" >/dev/null 2>&1 || true
rm -f "$LAUNCH_AGENT_PLIST"
echo "✅ 已卸载 FieldMind 后端用户服务"

for PID in $(lsof -nP -tiTCP:8000 -sTCP:LISTEN 2>/dev/null); do
    kill "$PID" 2>/dev/null || true
    echo "✅ 已停止 8000 端口进程: $PID"
done

for PID in $(lsof -nP -tiTCP:${BACKEND_PORT} -sTCP:LISTEN 2>/dev/null); do
    kill "$PID" 2>/dev/null || true
    echo "✅ 已停止 ${BACKEND_PORT} 端口进程: $PID"
done

# 旧版服务只做 best-effort 清理；新版停止流程不依赖它是否可被当前会话控制。
for PID in $(lsof -nP -tiTCP:8011 -sTCP:LISTEN 2>/dev/null); do
    kill "$PID" 2>/dev/null || true
done

for PID in $(lsof -nP -tiTCP:8012 -sTCP:LISTEN 2>/dev/null); do
    kill "$PID" 2>/dev/null || true
done

osascript -e 'tell application "FieldMind" to quit' >/dev/null 2>&1 || true
osascript -e 'tell application id "com.fieldmind.native.v3" to quit' >/dev/null 2>&1 || true
echo "✅ FieldMind 已停止"
