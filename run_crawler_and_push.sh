#!/bin/bash

# 设置工作目录
WORK_DIR="/home/ubuntu/workspace/truth-guardian-server"
LOG_DIR="$WORK_DIR/logs"
LOG_FILE="$LOG_DIR/crawler_push_$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "开始执行时间: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 进入工作目录
cd "$WORK_DIR" || {
    echo "错误: 无法进入工作目录 $WORK_DIR" >> "$LOG_FILE"
    exit 1
}

# 激活虚拟环境
source .venv/bin/activate || {
    echo "错误: 无法激活虚拟环境" >> "$LOG_FILE"
    exit 1
}

# 执行爬虫
echo "开始执行爬虫..." >> "$LOG_FILE"
python app/scraper/spiders/xinlang_search.py >> "$LOG_FILE" 2>&1
CRAWLER_EXIT_CODE=$?

if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
    echo "爬虫执行成功" >> "$LOG_FILE"
else
    echo "爬虫执行失败，退出码: $CRAWLER_EXIT_CODE" >> "$LOG_FILE"
fi

# 等待3秒
sleep 3

# 执行消息推送
echo "开始执行消息推送..." >> "$LOG_FILE"
python send_message.py --now >> "$LOG_FILE" 2>&1
PUSH_EXIT_CODE=$?

if [ $PUSH_EXIT_CODE -eq 0 ]; then
    echo "消息推送执行成功" >> "$LOG_FILE"
else
    echo "消息推送执行失败，退出码: $PUSH_EXIT_CODE" >> "$LOG_FILE"
fi

# 记录结束时间
echo "执行结束时间: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 清理旧日志文件（保留最近7天）
find "$LOG_DIR" -name "crawler_push_*.log" -mtime +7 -delete

# 退出虚拟环境
deactivate

exit 0 