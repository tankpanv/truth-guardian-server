#!/bin/bash

# 设置服务器地址
SERVER="http://localhost:5005"

# 输出分隔线函数
separator() {
  echo "----------------------------------------"
  echo "$1"
  echo "----------------------------------------"
}

# 创建临时文件存储响应
RESPONSE_FILE=$(mktemp)

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 检查是否提供了访问令牌
if [ -z "$1" ]; then
  echo -e "${RED}错误: 请提供访问令牌作为第一个参数${NC}"
  echo "使用方法: ./user_api.sh <access_token>"
  echo "示例: ./user_api.sh eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  exit 1
fi

# 使用提供的访问令牌
ACCESS_TOKEN=$1

echo -e "${BLUE}使用的访问令牌: ${ACCESS_TOKEN}${NC}\n"

# 用户信息相关接口
separator "用户信息 API 测试"

# 1. 获取当前用户信息
separator "1. 获取当前用户信息"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"
echo -e "${GREEN}可能的成功响应 (200):${NC}"
echo '{
  "data": {
    "id": 1,
    "user_name": "testuser",
    "name": "测试用户",
    "phone": "13800138000",
    "bio": "我是一名Truth Guardian用户",
    "tags": ["真相", "辟谣", "事实核查"],
    "interests": ["新闻", "科技", "科学"],
    "avatar_url": "https://example.com/avatar.jpg",
    "created_at": "2023-04-28T10:30:15.123456",
    "updated_at": "2023-04-28T10:30:15.123456"
  }
}'
echo -e "\n"
echo -e "${RED}可能的错误响应:${NC}"
echo '{
  "error": "无法识别用户身份"
}'
echo '{
  "error": "用户不存在"
}'
echo '{
  "msg": "Token has expired"
}'
echo -e "\n"

# 保存用户ID以备后续使用
USER_ID=$(cat "$RESPONSE_FILE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

# 2. 更新用户基本信息
separator "2. 更新用户基本信息"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"name\": \"更新后的名字\", \"phone\": \"13900139000\", \"bio\": \"这是我的个人签名\", \"avatar_url\": \"https://example.com/new_avatar.jpg\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "更新后的名字",
    "phone": "13900139000",
    "bio": "这是我的个人签名",
    "avatar_url": "https://example.com/new_avatar.jpg"
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"
echo -e "${GREEN}可能的成功响应 (200):${NC}"
echo '{
  "message": "用户信息更新成功"
}'
echo -e "\n"
echo -e "${RED}可能的错误响应:${NC}"
echo '{
  "error": "无效的请求数据"
}'
echo '{
  "error": "无法识别用户身份"
}'
echo '{
  "error": "用户不存在"
}'
echo -e "\n"

# 3. 验证更新结果
separator "3. 验证用户信息更新"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 4. 更新用户标签和兴趣
separator "4. 更新用户标签和兴趣"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"tags\": [\"辟谣\", \"真相\", \"核查\"], \"interests\": [\"新闻\", \"社会\", \"媒体\"]}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "tags": ["辟谣", "真相", "核查"],
    "interests": ["新闻", "社会", "媒体"]
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"
echo -e "${GREEN}可能的成功响应 (200):${NC}"
echo '{
  "message": "用户信息更新成功"
}'
echo -e "\n"

# 5. 验证标签和兴趣更新结果
separator "5. 验证标签和兴趣更新结果"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 6. 修改用户密码
separator "6. 修改用户密码"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"current_password\": \"password123\", \"new_password\": \"newpassword456\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "current_password": "password123",
    "new_password": "newpassword456"
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"
echo -e "${GREEN}可能的成功响应 (200):${NC}"
echo '{
  "message": "用户信息更新成功"
}'
echo -e "\n"
echo -e "${RED}可能的错误响应:${NC}"
echo '{
  "error": "当前密码验证失败"
}'
echo '{
  "error": "无法识别用户身份"
}'
echo '{
  "error": "用户不存在"
}'
echo -e "\n"

# 7. 使用错误的当前密码测试密码更新
separator "7. 使用错误的当前密码测试密码更新 (失败示例)"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"current_password\": \"错误密码\", \"new_password\": \"newpassword789\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "current_password": "错误密码",
    "new_password": "newpassword789"
  }' > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"
echo -e "${RED}期望的错误响应 (401):${NC}"
echo '{
  "error": "当前密码验证失败"
}'
echo -e "\n"

# 清理临时文件
rm -f "$RESPONSE_FILE"

echo -e "${GREEN}测试完成!${NC}"
echo "注意: 如果修改了密码，请记得在后续登录时使用新密码" 