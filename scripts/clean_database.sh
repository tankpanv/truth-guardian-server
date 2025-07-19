#!/bin/bash

# 数据库清理脚本的Shell包装器

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 进入项目目录
cd "$PROJECT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "已激活虚拟环境"
fi

echo "数据库清理工具"
echo "================"

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --tables TABLES    指定要清理的表 (debunk,message,news,all)"
    echo "  --confirm          确认执行清理操作"
    echo "  --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --tables debunk --confirm     # 只清理辟谣相关数据"
    echo "  $0 --tables all --confirm        # 清理所有数据"
    echo "  $0 --confirm                     # 清理所有数据（默认）"
}

# 解析参数
TABLES="all"
CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tables)
            TABLES="$2"
            shift 2
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 构建Python命令
PYTHON_CMD="python3 scripts/clean_database.py --tables $TABLES"

if [ "$CONFIRM" = true ]; then
    PYTHON_CMD="$PYTHON_CMD --confirm"
fi

# 执行清理
echo "执行命令: $PYTHON_CMD"
$PYTHON_CMD