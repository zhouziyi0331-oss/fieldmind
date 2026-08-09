#!/bin/bash
#
# PostgreSQL 数据库备份脚本
# 功能：自动备份 PostgreSQL 数据库
#

set -e  # 遇到错误立即退出

# ============ 配置 ============
BACKUP_DIR="${HOME}/FieldMind-Rebuild/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/fieldmind_${TIMESTAMP}.sql"
RETENTION_DAYS=30  # 保留30天的备份

# 数据库配置（从环境变量读取，或使用默认值）
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fieldmind}"
DB_USER="${DB_USER:-postgres}"

# ============ 函数 ============

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ============ 主逻辑 ============

log "🚀 开始备份 PostgreSQL 数据库"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 检查 pg_dump 是否存在
if ! command -v pg_dump &> /dev/null; then
    log "❌ 错误: pg_dump 未安装"
    log "请安装 PostgreSQL 客户端工具"
    exit 1
fi

# 执行备份
log "📦 备份数据库: ${DB_NAME}"
log "📁 备份文件: ${BACKUP_FILE}"

if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_FILE}" 2>/dev/null; then
    log "✅ 数据库备份成功"

    # 压缩备份文件
    log "🗜️  压缩备份文件..."
    gzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"

    # 计算文件大小
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "📊 备份大小: ${BACKUP_SIZE}"

else
    log "❌ 数据库备份失败"
    exit 1
fi

# 清理旧备份
log "🧹 清理 ${RETENTION_DAYS} 天前的旧备份..."
find "${BACKUP_DIR}" -name "fieldmind_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
OLD_COUNT=$(find "${BACKUP_DIR}" -name "fieldmind_*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l | tr -d ' ')
log "✅ 已删除 ${OLD_COUNT} 个旧备份"

# 显示当前备份列表
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "fieldmind_*.sql.gz" | wc -l | tr -d ' ')
log "📚 当前共有 ${BACKUP_COUNT} 个备份"

log "🎉 备份完成！"
log "📁 备份位置: ${BACKUP_FILE}"

exit 0
