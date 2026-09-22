#!/bin/bash

# FieldMind 唯一正版启动入口。
# 使用当前源码后端和同一份数据库/上传目录，不再迁移或删除旧 App 包。
set -u

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin:${PATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export DEBUG=false

REAL_USER="$(id -un)"
USER_HOME="$(dscl . -read "/Users/${REAL_USER}" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
USER_HOME="${USER_HOME:-/Users/${REAL_USER}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$ROOT_DIR/venv/bin/python"
BACKEND_DIR="$ROOT_DIR/backend/src"
PID_DIR="$ROOT_DIR/.runtime"
LOG_DIR="$ROOT_DIR/backend/logs"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
BACKEND_PORT="${FIELDMIND_PORT:-8013}"
BASE_URL="http://127.0.0.1:${BACKEND_PORT}"
RUNTIME_VERSION="fieldmind-native-v3.1-unified-data"
LAUNCH_AGENT_LABEL="com.fieldmind.backend.v3"
LAUNCH_AGENT_PLIST="$USER_HOME/Library/LaunchAgents/${LAUNCH_AGENT_LABEL}.plist"
APP_BUNDLE="${FIELDMIND_APP_BUNDLE:-/Applications/FieldMind.app}"
APP_BIN="$APP_BUNDLE/Contents/MacOS/FieldMindNative"
NATIVE_PROJECT_DIR="$ROOT_DIR/frontend/fieldmind-native"
NATIVE_BINARY="$NATIVE_PROJECT_DIR/.build/arm64-apple-macosx/release/FieldMindNative"

mkdir -p "$PID_DIR" "$LOG_DIR" "$USER_HOME/Library/LaunchAgents" "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources"
# 当前正版原生端的可执行文件名是 FieldMindNative；清掉同一 App 包里遗留的旧网页二进制，
# 避免 Finder 或旧启动脚本误把它当成应用入口。
rm -f "$APP_BUNDLE/Contents/MacOS/FieldMind"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "❌ 未找到 Python 虚拟环境: $PYTHON_BIN"
    exit 1
fi

api_ready() {
    /usr/bin/curl -fsS "$BASE_URL/api/monitoring/health" >/dev/null 2>&1 \
        && /usr/bin/curl -fsS "$BASE_URL/api/v1/dashboard/stats/1" >/dev/null 2>&1 \
        && /usr/bin/curl -fsS "$BASE_URL/api/file-tree/1" >/dev/null 2>&1 \
        && /usr/bin/curl -fsS "$BASE_URL/api/runtime/version" 2>/dev/null \
            | /usr/bin/grep -q "\"version\":\"${RUNTIME_VERSION}\""
}

kill_listeners_on_port() {
    local port="$1"
    local pids
    pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        echo "🧹 清理端口 ${port} 监听进程: ${pids}"
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null || true
        done
    fi
}

reset_legacy_backends() {
    launchctl bootout "gui/$(id -u)" "$LAUNCH_AGENT_PLIST" >/dev/null 2>&1 || true
    kill_listeners_on_port 8000
    kill_listeners_on_port 8011
    kill_listeners_on_port 8012
    kill_listeners_on_port 8013
}

wait_for_api() {
    local seconds="${1:-45}"
    for _ in $(seq 1 "$seconds"); do
        if api_ready; then return 0; fi
        sleep 1
    done
    return 1
}

write_app_plist() {
    cat >"$APP_BUNDLE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FieldMindNative</string>
    <key>CFBundleIdentifier</key>
    <string>com.fieldmind.native.v3</string>
    <key>CFBundleName</key>
    <string>FieldMind</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSDocumentsFolderUsageDescription</key>
    <string>FieldMind 需要访问文档文件夹以导入和处理材料</string>
    <key>NSDownloadsFolderUsageDescription</key>
    <string>FieldMind 需要访问下载文件夹以导入材料</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>FieldMind 需要访问文件以处理您的材料</string>
</dict>
</plist>
PLIST
}

install_current_app_binary() {
    if [ ! -x "$NATIVE_BINARY" ] || [ "${FIELDMIND_REBUILD_APP:-0}" = "1" ]; then
        echo "▶️ 构建正版桌面端..."
        if ! (cd "$NATIVE_PROJECT_DIR" && swift build -c release --disable-sandbox); then
            echo "❌ 桌面端构建失败"
            exit 1
        fi
    fi
    if [ ! -x "$NATIVE_BINARY" ]; then
        echo "❌ 未找到桌面端构建产物: $NATIVE_BINARY"
        exit 1
    fi

    rm -f "$APP_BUNDLE/Contents/MacOS/FieldMind"
    write_app_plist
    if [ ! -x "$APP_BIN" ] || [ "$NATIVE_BINARY" -nt "$APP_BIN" ]; then
        echo "▶️ 更新正版桌面二进制..."
        install -m 755 "$NATIVE_BINARY" "$APP_BIN"
        codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null 2>&1 || true
    fi
}

write_launch_agent() {
    cat >"$LAUNCH_AGENT_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LAUNCH_AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>-m</string>
        <string>app.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${BACKEND_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${PATH}</string>
        <key>PORT</key>
        <string>${BACKEND_PORT}</string>
        <key>DEBUG</key>
        <string>false</string>
        <key>OMP_NUM_THREADS</key>
        <string>${OMP_NUM_THREADS}</string>
        <key>MKL_NUM_THREADS</key>
        <string>${MKL_NUM_THREADS}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/backend.launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/backend.launchd.err.log</string>
</dict>
</plist>
PLIST
    plutil -lint "$LAUNCH_AGENT_PLIST" >/dev/null
}

start_backend() {
    reset_legacy_backends
    if api_ready; then
        echo "✅ v3 后端已运行: $BASE_URL"
        return 0
    fi

    echo "▶️ 启动 v3 后端服务..."
    write_launch_agent
    launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENT_PLIST" >/dev/null 2>&1 || true
    launchctl enable "gui/$(id -u)/${LAUNCH_AGENT_LABEL}" >/dev/null 2>&1 || true
    launchctl kickstart -k "gui/$(id -u)/${LAUNCH_AGENT_LABEL}" >/dev/null 2>&1 || true

    if wait_for_api 35; then
        launchctl print "gui/$(id -u)/${LAUNCH_AGENT_LABEL}" 2>/dev/null | awk '/pid = / {print $3; exit}' >"$BACKEND_PID_FILE" || true
        echo "✅ v3 后端已由 LaunchAgent 接管: $BASE_URL"
        return 0
    fi

    echo "⚠️ LaunchAgent 未接管，使用本地后台进程兜底..."
    (
        cd "$BACKEND_DIR" || exit 1
        export PORT="$BACKEND_PORT" DEBUG=false
        export OMP_NUM_THREADS="$OMP_NUM_THREADS" MKL_NUM_THREADS="$MKL_NUM_THREADS"
        nohup "$PYTHON_BIN" -m app.main >"$LOG_DIR/backend.manual.log" 2>&1 </dev/null &
        echo $! >"$BACKEND_PID_FILE"
        disown $! 2>/dev/null || true
    )

    if wait_for_api 45; then
        echo "✅ v3 后端已由后台进程启动: $BASE_URL"
        return 0
    fi

    echo "❌ v3 后端启动失败，请查看: $LOG_DIR/backend.launchd.err.log 或 $LOG_DIR/backend.manual.log"
    return 1
}

echo "▶️ 准备 FieldMind 正版运行环境..."
install_current_app_binary
HOME="$USER_HOME" defaults write com.fieldmind.native.v3 fieldmind_api_server_url -string "$BASE_URL" 2>/dev/null || true

if ! start_backend; then exit 1; fi

echo "▶️ 打开 FieldMind 桌面端..."
if [ -x "$APP_BIN" ]; then
    nohup "$APP_BIN" >"$LOG_DIR/app.stdout.log" 2>"$LOG_DIR/app.stderr.log" </dev/null &
    echo $! >"$PID_DIR/app.pid"
    disown $! 2>/dev/null || true
else
    echo "❌ 找不到正版桌面二进制: $APP_BIN"
    exit 1
fi

echo ""
echo "✅ FieldMind 已启动"
echo "   后端: $BASE_URL"
echo "   API 文档: $BASE_URL/docs"
echo "   桌面端: $APP_BIN"
echo "   检验脚本: $ROOT_DIR/test_connection.sh"
