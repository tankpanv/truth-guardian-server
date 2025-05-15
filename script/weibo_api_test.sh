#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置参数
SERVER="http://localhost:5005"
USERNAME="user1"
PASSWORD="user1123456"
RESPONSE_FILE="response.json"

# 辅助函数：解析JSON
parse_json() {
    python3 -c "import sys, json; print(json.load(sys.stdin).get('$1', ''))"
}

# 辅助函数：分隔符
separator() {
    echo -e "\n${YELLOW}===== $1 =====${NC}\n"
}

# 1. 登录获取token
separator "1. 登录获取访问令牌"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X POST \"${SERVER}/api/auth/login\" -H \"Content-Type: application/json\" -d '{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}'"

# 执行登录请求
curl -s -X POST "${SERVER}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"password\": \"${PASSWORD}\"
  }" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 提取访问令牌
ACCESS_TOKEN=$(cat "$RESPONSE_FILE" | parse_json "access_token")

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}登录成功!${NC}"
    echo -e "${GREEN}访问令牌: ${ACCESS_TOKEN}${NC}\n"
else
    echo -e "${RED}登录失败!${NC}\n"
    exit 1
fi

# 2. 获取微博热搜
separator "2. 获取微博热搜"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/weibo/hot-search\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/weibo/hot-search" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 3. 搜索微博
separator "3. 搜索微博"
KEYWORD="新冠"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/weibo/search?keyword=${KEYWORD}\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/weibo/search?keyword=${KEYWORD}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 4. 获取微博详情
separator "4. 获取微博详情"
WEIBO_ID="4893551923103694"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/weibo/detail/${WEIBO_ID}\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/weibo/detail/${WEIBO_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 5. 获取微博评论
separator "5. 获取微博评论"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/weibo/comments/${WEIBO_ID}\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/weibo/comments/${WEIBO_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 6. 获取谣言分析可视化数据
separator "6. 获取谣言分析可视化数据"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/visualization/rumor-analysis\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/visualization/rumor-analysis" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Accept: application/json" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 检查响应是否包含预期的数据结构
if cat "$RESPONSE_FILE" | grep -q "\"success\""; then
    echo -e "${GREEN}获取谣言分析数据成功!${NC}"
else
    echo -e "${RED}获取谣言分析数据失败!${NC}"
fi

# 6.5 创建或验证用户2
separator "6.5 创建或验证用户2"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X POST \"${SERVER}/api/auth/register\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"username\": \"user2\",
    \"password\": \"user2123456\",
    \"name\": \"测试用户2\",
    \"phone\": \"13800138002\"
  }'"

curl -s -X POST "${SERVER}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user2",
    "password": "user2123456",
    "name": "测试用户2",
    "phone": "13800138002"
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 7. 测试IM消息推送
separator "7. 测试IM消息推送"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X POST \"${SERVER}/api/im/push\" \
  -H \"Authorization: Bearer ${ACCESS_TOKEN}\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"receiver_id\": 2,
    \"title\": \"测试消息标题\",
    \"msg_type\": \"text\",
    \"content\": \"测试消息内容\",
    \"priority\": 1,
    \"expire_time\": \"2025-10-31 23:59:59\"
  }'"

curl -s -X POST "${SERVER}/api/im/push" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 2,
    "title": "测试消息标题",
    "msg_type": "text",
    "content": "测试消息内容",
    "priority": 1,
    "expire_time": "2025-10-31 23:59:59"
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 检查响应是否成功
if cat "$RESPONSE_FILE" | grep -q "\"success\": true"; then
    echo -e "${GREEN}消息推送成功!${NC}"
else
    echo -e "${RED}消息推送失败!${NC}"
fi

# 8. 获取消息列表
separator "8. 获取消息列表"

# 8.1 获取收到的消息
echo -e "${YELLOW}8.1 获取收到的消息:${NC}"
echo "curl -X GET \"${SERVER}/api/im/messages?direction=received&unread_only=1&page=1&per_page=10\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/im/messages?direction=received&unread_only=1&page=1&per_page=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 8.2 获取发送的消息
echo -e "${YELLOW}8.2 获取发送的消息:${NC}"
echo "curl -X GET \"${SERVER}/api/im/messages?direction=sent&page=1&per_page=10\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/im/messages?direction=sent&page=1&per_page=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 8.3 获取所有消息
echo -e "${YELLOW}8.3 获取所有消息:${NC}"
echo "curl -X GET \"${SERVER}/api/im/messages?direction=all&page=1&per_page=10\" -H \"Authorization: Bearer ${ACCESS_TOKEN}\""

curl -s -X GET "${SERVER}/api/im/messages?direction=all&page=1&per_page=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 从响应中获取消息ID，确保是当前用户接收的消息
MESSAGE_ID=$(cat "$RESPONSE_FILE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
messages = data.get('data', {}).get('messages', [])
received_messages = [msg for msg in messages if msg.get('receiver_id') == 1]
print(received_messages[0].get('id', '') if received_messages else '')
")

# 9. 标记消息已读（如果找到了接收的消息）
if [ -n "$MESSAGE_ID" ]; then
    separator "9. 标记消息已读"
    echo -e "${YELLOW}请求:${NC}"
    echo "curl -X POST \"${SERVER}/api/im/messages/read\" \
      -H \"Authorization: Bearer ${ACCESS_TOKEN}\" \
      -H \"Content-Type: application/json\" \
      -d '{\"message_ids\": [${MESSAGE_ID}]}'"

    curl -s -X POST "${SERVER}/api/im/messages/read" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"message_ids\": [${MESSAGE_ID}]}" > "$RESPONSE_FILE"

    echo -e "\n${YELLOW}响应:${NC}"
    cat "$RESPONSE_FILE"
    echo -e "\n"

    # 检查响应是否成功
    if cat "$RESPONSE_FILE" | grep -q "\"success\": true"; then
        echo -e "${GREEN}标记消息已读成功!${NC}"
    else
        echo -e "${RED}标记消息已读失败!${NC}"
    fi
else
    echo -e "${YELLOW}没有找到当前用户接收的未读消息，跳过标记已读测试${NC}"
fi

# 清理临时文件
rm -f "$RESPONSE_FILE"

echo -e "${GREEN}测试完成!${NC}" 