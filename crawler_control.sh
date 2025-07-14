#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置相对路径
DAEMON_SCRIPT="./crawler_daemon.sh"
PID_FILE="./crawler_daemon.pid"
LOG_DIR="./logs"

# 显示使用帮助
show_help() {
    echo "用法: $0 {start|stop|restart|status|logs|tail}"
    echo ""
    echo "命令说明:"
    echo "  start   - 启动守护进程"
    echo "  stop    - 停止守护进程"
    echo "  restart - 重启守护进程"
    echo "  status  - 查看守护进程状态"
    echo "  logs    - 查看守护进程日志"
    echo "  tail    - 实时查看日志"
    echo ""
}

# 启动守护进程
start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "守护进程已在运行 (PID: $PID)"
            return 1
        else
            echo "清理旧的PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "正在启动守护进程..."
    chmod +x "$DAEMON_SCRIPT"
    nohup "$DAEMON_SCRIPT" > /dev/null 2>&1 &
    
    # 等待一下让进程启动
    sleep 2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "守护进程启动成功 (PID: $PID)"
            echo "日志文件: $LOG_DIR/crawler_daemon_$(date +%Y%m%d).log"
            return 0
        else
            echo "守护进程启动失败"
            return 1
        fi
    else
        echo "守护进程启动失败，未找到PID文件"
        return 1
    fi
}

# 停止守护进程
stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "守护进程未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "守护进程未运行，清理PID文件"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo "正在停止守护进程 (PID: $PID)..."
    kill -TERM "$PID"
    
    # 等待进程停止
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "守护进程已停止"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 如果进程还在运行，强制杀死
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "强制停止守护进程..."
        kill -KILL "$PID"
        sleep 1
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "守护进程已强制停止"
            rm -f "$PID_FILE"
            return 0
        else
            echo "无法停止守护进程"
            return 1
        fi
    fi
}

# 查看守护进程状态
check_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "守护进程未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "守护进程正在运行 (PID: $PID)"
        echo "启动时间: $(ps -o lstart= -p "$PID")"
        echo "运行时间: $(ps -o etime= -p "$PID")"
        echo "内存使用: $(ps -o rss= -p "$PID") KB"
        echo "CPU使用: $(ps -o pcpu= -p "$PID")%"
        return 0
    else
        echo "守护进程未运行，清理PID文件"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 查看日志
view_logs() {
    LOG_FILE="$LOG_DIR/crawler_daemon_$(date +%Y%m%d).log"
    if [ -f "$LOG_FILE" ]; then
        echo "显示今天的守护进程日志:"
        echo "=================================="
        cat "$LOG_FILE"
    else
        echo "未找到今天的日志文件: $LOG_FILE"
    fi
}

# 实时查看日志
tail_logs() {
    LOG_FILE="$LOG_DIR/crawler_daemon_$(date +%Y%m%d).log"
    TASK_LOG="$LOG_DIR/crawler_push_$(date +%Y%m%d).log"
    
    echo "实时查看日志 (按 Ctrl+C 退出):"
    echo "=================================="
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE" "$TASK_LOG" 2>/dev/null
    else
        echo "等待日志文件生成..."
        while [ ! -f "$LOG_FILE" ]; do
            sleep 1
        done
        tail -f "$LOG_FILE" "$TASK_LOG" 2>/dev/null
    fi
}

# 主程序
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 2
        start_daemon
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    tail)
        tail_logs
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit $? 