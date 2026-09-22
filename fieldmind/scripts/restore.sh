#!/bin/bash
#
# 恢复脚本
# 功能：从备份恢复数据库和文件
#

set -e  # 遇到错误立即退出

# ============ 配置 ============
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fieldmind}"
DB_USER="${DB_USER:-postgres}"

# ============ 函数 ============

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

show_usage() {
    cat << EOF
用法: $0 [选项]

选项:
  --db FILE         恢复数据库（指定 .sql.gz 文件）
  --files FILE      恢复文件存储（指定 .tar.gz 文件）
  --latest          恢复最新的备份
  --list            列出所有可用备份
  -h, --help        显示此帮助信息

示例:
  # 列出所有备份
  $0 --list

  # 恢复最新备份
  $0 --latest

  # 恢复指定备份
  $0 --db backups/postgres/fieldmind_20260802.sql.gz --files backups/files/files_20260802.tar.gz

EOF
}

list_backups() {
    log "📚 可用的备份："
    log ""
    log "数据库备份："
    ls -lh ~/FieldMind-Rebuild/backups/postgres/fieldmind_*.sql.gz 2>/dev/null || echo "  无备份"
    log ""
    log "文件备份："
    ls -lh ~/FieldMind-Rebuild/backups/files/files_*.tar.gz 2>/dev/null || echo "  无备份"
}

restore_database() {
    local DB_FILE="$1"

    log "📦 恢复数据库: ${DB_FILE}"

    if [ ! -f "${DB_FILE}" ]; then
        log "❌ 错误: 文件不存在: ${DB_FILE}"
        return 1
    fi

    # 解压
    log "🗜️  解压备份文件..."
    gunzip -c "${DB_FILE}" > /tmp/restore_db.sql

    # 恢复
    log "💾 恢复到数据库: ${DB_NAME}"
    log "⚠️  警告: 这将覆盖现有数据！"
    read -p "确认继续？(yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        log "❌ 取消恢复"
        rm /tmp/restore_db.sql
        return 1
    fi

    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" < /tmp/restore_db.sql

    rm /tmp/restore_db.sql
    log "✅ 数据库恢复成功"
}

restore_files() {
    local FILES_ARCHIVE="$1"

    log "📦 恢复文件存储: ${FILES_ARCHIVE}"

    if [ ! -f "${FILES_ARCHIVE}" ]; then
        log "❌ 错误: 文件不存在: ${FILES_ARCHIVE}"
        return 1
    fi

    log "⚠️  警告: 这将覆盖现有文件！"
    read -p "确认继续？(yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        log "❌ 取消恢复"
        return 1
    fi

    # 解压
    log "🗜️  解压文件..."
    cd ~/FieldMind-Rebuild
    tar -xzf "${FILES_ARCHIVE}"

    log "✅ 文件恢复成功"
}

restore_latest() {
    log "🔍 查找最新备份..."

    # 最新的数据库备份
    DB_BACKUP=$(ls -t ~/FieldMind-Rebuild/backups/postgres/fieldmind_*.sql.gz 2>/dev/null | head -1)

    # 最新的文件备份
    FILES_BACKUP=$(ls -t ~/FieldMind-Rebuild/backups/files/files_*.tar.gz 2>/dev/null | head -1)

    if [ -z "${DB_BACKUP}" ] && [ -z "${FILES_BACKUP}" ]; then
        log "❌ 错误: 未找到任何备份"
        return 1
    fi

    log ""
    log "📁 将恢复以下备份："
    [ -n "${DB_BACKUP}" ] && log "   数据库: ${DB_BACKUP}"
    [ -n "${FILES_BACKUP}" ] && log "   文件:   ${FILES_BACKUP}"
    log ""

    # 恢复数据库
    if [ -n "${DB_BACKUP}" ]; then
        restore_database "${DB_BACKUP}"
    fi

    # 恢复文件
    if [ -n "${FILES_BACKUP}" ]; then
        restore_files "${FILES_BACKUP}"
    fi

    log "🎉 恢复完成！"
}

# ============ 主逻辑 ============

log "🚀 FieldMind 恢复工具"
log "================================================"

# 解析参数
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

case "$1" in
    --list)
        list_backups
        ;;
    --latest)
        restore_latest
        ;;
    --db)
        if [ -z "$2" ]; then
            log "❌ 错误: 请指定数据库备份文件"
            exit 1
        fi
        restore_database "$2"
        ;;
    --files)
        if [ -z "$2" ]; then
            log "❌ 错误: 请指定文件备份文件"
            exit 1
        fi
        restore_files "$2"
        ;;
    -h|--help)
        show_usage
        ;;
    *)
        log "❌ 错误: 未知选项: $1"
        show_usage
        exit 1
        ;;
esac

exit 0
