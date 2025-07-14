#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置相对路径
LOG_DIR="./logs"
PID_FILE="./crawler_daemon.pid"
LOG_FILE="$LOG_DIR/crawler_daemon_$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "守护进程已在运行 (PID: $OLD_PID)"
        exit 1
    else
        echo "清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 信号处理函数
cleanup() {
    echo "$(date): 收到停止信号，正在清理..." >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 记录当前进程PID
echo $$ > "$PID_FILE"

# 记录启动信息
echo "========================================" >> "$LOG_FILE"
echo "守护进程启动时间: $(date)" >> "$LOG_FILE"
echo "工作目录: $SCRIPT_DIR" >> "$LOG_FILE"
echo "进程PID: $$" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 执行任务的函数
run_tasks() {
    local task_log="$LOG_DIR/crawler_push_$(date +%Y%m%d).log"
    
    echo "========================================" >> "$task_log"
    echo "开始执行时间: $(date)" >> "$task_log"
    echo "========================================" >> "$task_log"
    
    # 激活虚拟环境
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "虚拟环境已激活" >> "$task_log"
    else
        echo "警告: 未找到虚拟环境，使用系统Python" >> "$task_log"
    fi
    
    # 执行爬虫
    echo "开始执行爬虫..." >> "$task_log"
    python app/scraper/spiders/xinlang_search.py >> "$task_log" 2>&1
    CRAWLER_EXIT_CODE=$?
    
    if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
        echo "爬虫执行成功" >> "$task_log"
    else
        echo "爬虫执行失败，退出码: $CRAWLER_EXIT_CODE" >> "$task_log"
    fi
    
    # 等待3秒
    sleep 3
    
    # 执行消息推送
    echo "开始执行消息推送..." >> "$task_log"
    python send_message.py --now >> "$task_log" 2>&1
    PUSH_EXIT_CODE=$?
    
    if [ $PUSH_EXIT_CODE -eq 0 ]; then
        echo "消息推送执行成功" >> "$task_log"
    else
        echo "消息推送执行失败，退出码: $PUSH_EXIT_CODE" >> "$task_log"
    fi
    
    # 记录结束时间
    echo "执行结束时间: $(date)" >> "$task_log"
    echo "========================================" >> "$task_log"
    echo "" >> "$task_log"
    
    # 退出虚拟环境
    if [ -f ".venv/bin/activate" ]; then
        deactivate
    fi
    
    # 清理旧日志文件（保留最近7天）
    find "$LOG_DIR" -name "crawler_push_*.log" -mtime +7 -delete 2>/dev/null
    find "$LOG_DIR" -name "crawler_daemon_*.log" -mtime +7 -delete 2>/dev/null
}

# 主循环
echo "$(date): 守护进程开始运行，每小时执行一次任务" >> "$LOG_FILE"

while true; do
    # 获取当前时间
    current_minute=$(date +%M)
    current_second=$(date +%S)
    
    # 如果是整点（0分钟），执行任务
    if [ "$current_minute" = "00" ] && [ "$current_second" -lt "10" ]; then
        echo "$(date): 开始执行定时任务" >> "$LOG_FILE"
        run_tasks
        echo "$(date): 定时任务执行完成" >> "$LOG_FILE"
        
        # 等待65秒，避免在同一分钟内重复执行
        sleep 65
    else
        # 计算到下一个整点还需要等待的时间
        minutes_to_wait=$((59 - current_minute))
        seconds_to_wait=$((60 - current_second))
        
        if [ $minutes_to_wait -eq 0 ]; then
            sleep_time=$seconds_to_wait
        else
            sleep_time=$((minutes_to_wait * 60 + seconds_to_wait))
        fi
        
        # 最少等待10秒，最多等待60秒（避免长时间等待）
        if [ $sleep_time -gt 60 ]; then
            sleep_time=60
        elif [ $sleep_time -lt 10 ]; then
            sleep_time=10
        fi
        
        sleep $sleep_time
    fi
done 