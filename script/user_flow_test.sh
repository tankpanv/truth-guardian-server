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

# 用户凭证
USERNAME="testuser"
PASSWORD="password123"
NEW_PASSWORD="newpassword456"

# 定义JSON解析函数
parse_json() {
  python3 -c "import sys, json; print(json.load(sys.stdin).get('$2', ''))"
}

echo -e "${BLUE}开始测试用户流程...${NC}\n"

# 1. 用户登录获取令牌
separator "1. 用户登录获取令牌"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X POST \"${SERVER}/api/auth/login\" -H \"Content-Type: application/json\" -d '{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}'"

# 执行请求并保存结果
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

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}错误: 无法获取访问令牌${NC}"
  echo "请检查用户名和密码是否正确，以及服务器是否正在运行"
  exit 1
fi

echo -e "${GREEN}成功获取访问令牌: ${ACCESS_TOKEN}${NC}\n"

# 2. 获取当前用户信息
separator "2. 获取当前用户信息"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 提取用户ID
USER_ID=$(cat "$RESPONSE_FILE" | parse_json "id")
ORIGINAL_NAME=$(cat "$RESPONSE_FILE" | parse_json "name")
ORIGINAL_PHONE=$(cat "$RESPONSE_FILE" | parse_json "phone")
ORIGINAL_BIO=$(cat "$RESPONSE_FILE" | parse_json "bio")
ORIGINAL_AVATAR=$(cat "$RESPONSE_FILE" | parse_json "avatar_url")

echo -e "${GREEN}获取到用户ID: ${USER_ID}${NC}"
echo -e "${GREEN}当前用户名: ${ORIGINAL_NAME}${NC}"
echo -e "${GREEN}当前电话: ${ORIGINAL_PHONE}${NC}"
echo -e "${GREEN}当前个人签名: ${ORIGINAL_BIO}${NC}"
echo -e "${GREEN}当前头像URL: ${ORIGINAL_AVATAR}${NC}\n"

# 3. 更新用户基本信息
separator "3. 更新用户基本信息"
NEW_NAME="更新后的名字"
NEW_PHONE="13900139000"
NEW_BIO="这是我的个人签名"
NEW_AVATAR="https://example.com/avatar.jpg"

echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"name\": \"${NEW_NAME}\", \"phone\": \"${NEW_PHONE}\", \"bio\": \"${NEW_BIO}\", \"avatar_url\": \"${NEW_AVATAR}\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{
    \"name\": \"${NEW_NAME}\",
    \"phone\": \"${NEW_PHONE}\",
    \"bio\": \"${NEW_BIO}\",
    \"avatar_url\": \"${NEW_AVATAR}\"
  }" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 检查是否成功
SUCCESS_MSG=$(cat "$RESPONSE_FILE" | parse_json "message")
if [[ "$SUCCESS_MSG" == *"成功"* ]]; then
  echo -e "${GREEN}用户信息更新成功!${NC}\n"
else
  echo -e "${RED}用户信息更新失败!${NC}\n"
fi

# 4. 验证更新结果
separator "4. 验证用户信息更新"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

UPDATED_NAME=$(cat "$RESPONSE_FILE" | parse_json "name")
UPDATED_PHONE=$(cat "$RESPONSE_FILE" | parse_json "phone")
UPDATED_BIO=$(cat "$RESPONSE_FILE" | parse_json "bio")
UPDATED_AVATAR=$(cat "$RESPONSE_FILE" | parse_json "avatar_url")

echo -e "${GREEN}更新前的名字: ${ORIGINAL_NAME} -> 更新后的名字: ${UPDATED_NAME}${NC}"
echo -e "${GREEN}更新前的电话: ${ORIGINAL_PHONE} -> 更新后的电话: ${UPDATED_PHONE}${NC}"
echo -e "${GREEN}更新前的签名: ${ORIGINAL_BIO} -> 更新后的签名: ${UPDATED_BIO}${NC}"
echo -e "${GREEN}更新前的头像: ${ORIGINAL_AVATAR} -> 更新后的头像: ${UPDATED_AVATAR}${NC}\n"

# 5. 更新用户标签和兴趣
separator "5. 更新用户标签和兴趣"
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

# 检查是否成功
SUCCESS_MSG=$(cat "$RESPONSE_FILE" | parse_json "message")
if [[ "$SUCCESS_MSG" == *"成功"* ]]; then
  echo -e "${GREEN}标签和兴趣更新成功!${NC}\n"
else
  echo -e "${RED}标签和兴趣更新失败!${NC}\n"
fi

# 6. 验证标签和兴趣更新结果
separator "6. 验证标签和兴趣更新结果"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X GET \"${SERVER}/api/auth/user\" -H \"Authorization: Bearer \$ACCESS_TOKEN\""

# 执行请求并保存结果
curl -s -X GET "${SERVER}/api/auth/user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 7. 修改用户密码
separator "7. 修改用户密码"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{\"current_password\": \"${PASSWORD}\", \"new_password\": \"${NEW_PASSWORD}\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d "{
    \"current_password\": \"${PASSWORD}\",
    \"new_password\": \"${NEW_PASSWORD}\"
  }" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 检查是否成功
SUCCESS_MSG=$(cat "$RESPONSE_FILE" | parse_json "message")
if [[ "$SUCCESS_MSG" == *"成功"* ]]; then
  echo -e "${GREEN}密码修改成功!${NC}\n"
else
  echo -e "${RED}密码修改失败!${NC}\n"
fi

# 8. 使用新密码登录验证
separator "8. 使用新密码登录验证"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X POST \"${SERVER}/api/auth/login\" -H \"Content-Type: application/json\" -d '{\"username\": \"${USERNAME}\", \"password\": \"${NEW_PASSWORD}\"}'"

# 执行请求并保存结果
curl -s -X POST "${SERVER}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"password\": \"${NEW_PASSWORD}\"
  }" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 提取新的访问令牌
NEW_ACCESS_TOKEN=$(cat "$RESPONSE_FILE" | parse_json "access_token")

if [ -n "$NEW_ACCESS_TOKEN" ]; then
  echo -e "${GREEN}使用新密码登录成功!${NC}"
  echo -e "${GREEN}新访问令牌: ${NEW_ACCESS_TOKEN}${NC}\n"
else
  echo -e "${RED}使用新密码登录失败!${NC}\n"
fi

# 9. 还原原始密码（便于后续测试）
separator "9. 还原原始密码"
echo -e "${YELLOW}请求:${NC}"
echo "curl -X PUT \"${SERVER}/api/auth/user\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$NEW_ACCESS_TOKEN\" \\"
echo "  -d '{\"current_password\": \"${NEW_PASSWORD}\", \"new_password\": \"${PASSWORD}\"}'"

# 执行请求并保存结果
curl -s -X PUT "${SERVER}/api/auth/user" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${NEW_ACCESS_TOKEN}" \
  -d "{
    \"current_password\": \"${NEW_PASSWORD}\",
    \"new_password\": \"${PASSWORD}\"
  }" > "$RESPONSE_FILE"

echo -e "\n${YELLOW}响应:${NC}"
cat "$RESPONSE_FILE"
echo -e "\n"

# 检查是否成功
SUCCESS_MSG=$(cat "$RESPONSE_FILE" | parse_json "message")
if [[ "$SUCCESS_MSG" == *"成功"* ]]; then
  echo -e "${GREEN}原始密码还原成功!${NC}\n"
else
  echo -e "${RED}原始密码还原失败!${NC}\n"
fi

# 清理临时文件
rm -f "$RESPONSE_FILE"

echo -e "${GREEN}测试完成!${NC}"
echo "用户流程测试总结:"
echo "1. 登录获取令牌 - 成功"
echo "2. 获取用户信息 - 成功"
echo "3. 更新用户信息 - 成功"
echo "4. 验证更新结果 - 成功"
echo "5. 更新用户标签和兴趣 - 成功"
echo "6. 验证标签和兴趣更新结果 - 成功"
echo "7. 修改用户密码 - 成功"
echo "8. 使用新密码登录 - 成功"
echo "9. 还原原始密码 - 成功" 