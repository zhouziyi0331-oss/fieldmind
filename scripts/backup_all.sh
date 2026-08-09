#!/bin/bash
#
# 完整备份脚本
# 功能：备份数据库和文件存储
#

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🚀 开始完整备份"
log "================================================"

# 备份 PostgreSQL
log ""
log "📦 步骤 1/2: 备份 PostgreSQL 数据库"
log "------------------------------------------------"
bash "${SCRIPT_DIR}/backup_postgres.sh"

# 备份文件
log ""
log "📦 步骤 2/2: 备份文件存储"
log "------------------------------------------------"
bash "${SCRIPT_DIR}/backup_files.sh"

log ""
log "================================================"
log "🎉 完整备份完成！"
log ""
log "📁 备份位置："
log "   - 数据库: ~/FieldMind-Rebuild/backups/postgres/"
log "   - 文件:   ~/FieldMind-Rebuild/backups/files/"
log ""
log "💡 恢复方法："
log "   bash ${SCRIPT_DIR}/restore.sh [数据库备份文件] [文件备份文件]"

exit 0
