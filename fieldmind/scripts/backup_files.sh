#!/bin/bash
#
# 文件存储备份脚本
# 功能：备份上传的文档和生成的数据
#

set -e  # 遇到错误立即退出

# ============ 配置 ============
SOURCE_DIR="${HOME}/FieldMind-Rebuild/uploads"
BACKUP_DIR="${HOME}/FieldMind-Rebuild/backups/files"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="files_${TIMESTAMP}.tar.gz"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}"
RETENTION_DAYS=30  # 保留30天的备份

# ============ 函数 ============

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ============ 主逻辑 ============

log "🚀 开始备份文件存储"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 检查源目录是否存在
if [ ! -d "${SOURCE_DIR}" ]; then
    log "⚠️  源目录不存在: ${SOURCE_DIR}"
    log "创建源目录..."
    mkdir -p "${SOURCE_DIR}"
fi

# 计算源目录大小
SOURCE_SIZE=$(du -sh "${SOURCE_DIR}" | cut -f1)
log "📊 源目录大小: ${SOURCE_SIZE}"

# 执行备份
log "📦 备份目录: ${SOURCE_DIR}"
log "📁 备份文件: ${BACKUP_FILE}"

cd "${HOME}/FieldMind-Rebuild"

if tar -czf "${BACKUP_FILE}" uploads/ 2>/dev/null; then
    log "✅ 文件备份成功"

    # 计算备份文件大小
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "📊 备份大小: ${BACKUP_SIZE}"

else
    log "❌ 文件备份失败"
    exit 1
fi

# 清理旧备份
log "🧹 清理 ${RETENTION_DAYS} 天前的旧备份..."
find "${BACKUP_DIR}" -name "files_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# 显示当前备份列表
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "files_*.tar.gz" | wc -l | tr -d ' ')
log "📚 当前共有 ${BACKUP_COUNT} 个备份"

log "🎉 备份完成！"
log "📁 备份位置: ${BACKUP_FILE}"

exit 0
