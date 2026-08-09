#!/bin/bash
#
# 自动备份任务
# 添加到 crontab 以实现定时备份
#
# 使用方法：
#   1. 编辑 crontab: crontab -e
#   2. 添加以下行：
#      # 每天凌晨 2:00 执行完整备份
#      0 2 * * * /Users/alwan/FieldMind-Rebuild/scripts/backup_all.sh >> /tmp/backup.log 2>&1
#
#      # 每周日凌晨 3:00 清理旧备份
#      0 3 * * 0 find ~/FieldMind-Rebuild/backups -name "*.gz" -mtime +30 -delete
#

# Crontab 配置示例
cat << 'EOF'
# FieldMind 自动备份任务
#
# 每天凌晨 2:00 执行完整备份
0 2 * * * /Users/alwan/FieldMind-Rebuild/scripts/backup_all.sh >> /tmp/fieldmind_backup.log 2>&1

# 每4小时备份一次文件（工作时间）
0 9,13,17,21 * * * /Users/alwan/FieldMind-Rebuild/scripts/backup_files.sh >> /tmp/fieldmind_backup.log 2>&1

# 每周日凌晨 3:00 清理 30 天前的旧备份
0 3 * * 0 find ~/FieldMind-Rebuild/backups -name "*.gz" -mtime +30 -delete >> /tmp/fieldmind_backup.log 2>&1

EOF

echo ""
echo "================================================"
echo "安装自动备份任务"
echo "================================================"
echo ""
echo "1. 编辑 crontab:"
echo "   crontab -e"
echo ""
echo "2. 将上面的配置复制粘贴到 crontab 中"
echo ""
echo "3. 保存并退出"
echo ""
echo "4. 验证 crontab 已安装:"
echo "   crontab -l"
echo ""
