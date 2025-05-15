#!/bin/bash

# 配置
API_BASE_URL="http://localhost:5005"
USERNAME="user1"
PASSWORD="user1123456"

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取token
get_token() {
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
        "$API_BASE_URL/api/auth/login")
    
    local token=$(echo "$response" | jq -r '.access_token')
    if [ "$token" != "null" ]; then
        echo "$token"
        return 0
    else
        log_error "获取token失败: $response"
        return 1
    fi
}

# 执行迁移
do_migration() {
    local token="$1"
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        "$API_BASE_URL/api/migration/content-to-article")
    
    # 检查是否成功
    if [ $? -ne 0 ]; then
        log_error "请求失败"
        return 1
    fi
    
    # 解析响应
    local code=$(echo "$response" | jq -r '.code')
    if [ "$code" = "0" ]; then
        # 获取统计信息
        local total=$(echo "$response" | jq -r '.data.stats.total')
        local success=$(echo "$response" | jq -r '.data.stats.success')
        local skipped=$(echo "$response" | jq -r '.data.stats.skipped')
        local error=$(echo "$response" | jq -r '.data.stats.error')
        
        # 打印统计信息
        log_info "迁移完成:"
        log_info "总数: $total"
        log_info "成功: $success"
        log_warn "跳过: $skipped"
        
        # 如果有错误，打印错误详情
        if [ "$error" -gt 0 ]; then
            log_error "错误: $error"
            echo "$response" | jq -r '.data.error_details[] | "错误ID: \(.content_id), 原因: \(.error)"' | while read -r line; do
                log_error "$line"
            done
        fi
        
        return 0
    else
        local message=$(echo "$response" | jq -r '.message')
        log_error "迁移失败: $message"
        return 1
    fi
}

main() {
    # 检查jq是否安装
    if ! command -v jq &> /dev/null; then
        log_error "请先安装jq: sudo apt-get install jq"
        exit 1
    fi
    
    # 获取token
    log_info "正在获取token..."
    local token
    token=$(get_token)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # 执行迁移
    log_info "开始执行迁移..."
    do_migration "$token"
    if [ $? -ne 0 ]; then
        exit 1
    fi
}

# 执行主函数
main
