#!/bin/bash

# 设置脚本路径
SCRIPT_PATH="/home/ubuntu/workspace/truth-guardian-server/run_crawler_and_push.sh"

# 给脚本添加执行权限
chmod +x "$SCRIPT_PATH"

# 备份当前crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "当前没有crontab任务"

# 创建新的crontab条目
CRON_ENTRY="0 * * * * $SCRIPT_PATH"

# 检查是否已经存在相同的任务
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "定时任务已存在，正在更新..."
    # 移除旧的任务
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# 添加新的定时任务
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "定时任务设置成功！"
echo "任务详情: 每小时执行一次爬虫和消息推送"
echo "执行时间: 每小时的0分钟"
echo "脚本路径: $SCRIPT_PATH"
echo ""
echo "当前crontab任务列表:"
crontab -l

echo ""
echo "如需查看日志，请查看: /home/ubuntu/workspace/truth-guardian-server/logs/crawler_push_YYYYMMDD.log"
echo "如需停止定时任务，请运行: crontab -e 然后删除相应行" 