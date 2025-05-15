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

# 用户管理相关接口
separator "用户管理 API"

# 1. 用户注册
separator "1. 用户注册"
echo "请求:"
echo "curl -X POST \"${SERVER}/api/auth/register\" -H \"Content-Type: application/json\" -d '{\"user_name\": \"testuser\", \"password\": \"password123\", \"name\": \"测试用户\", \"phone\": \"13800138000\"}'"

# 执行请求并保存结果
curl -s -X POST "${SERVER}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "testuser",
    "password": "password123",
    "name": "测试用户",
    "phone": "13800138000"
  }' > "$RESPONSE_FILE"

echo -e "\n响应:"
cat "$RESPONSE_FILE"
echo -e "\n"
echo "可能的成功响应 (201):"
echo '{
  "msg": "用户注册成功",
  "user_id": 1
}'
echo -e "\n"
echo "可能的错误响应:"
echo '{
  "code": 400,
  "message": "缺少必填字段"
}'
echo '{
  "code": 409,
  "message": "用户名已存在"
}'
echo '{
  "code": 500,
  "message": "服务器内部错误"
}'
echo -e "\n"

# 2. 用户登录
separator "2. 用户登录"
echo "请求:"
echo "curl -X POST \"${SERVER}/api/auth/login\" -H \"Content-Type: application/json\" -d '{\"username\": \"testuser\", \"password\": \"password123\"}'"

# 执行请求并保存结果
curl -s -X POST "${SERVER}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "password": "user1123456"
  }' > "$RESPONSE_FILE"

echo -e "\n响应:"
cat "$RESPONSE_FILE"
echo -e "\n"
echo "可能的成功响应 (200):"
echo '{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}'
echo -e "\n"
echo "可能的错误响应:"
echo '{
  "code": 400,
  "message": "需要用户名和密码"
}'
echo '{
  "code": 400,
  "message": "不支持的请求格式，请使用JSON或Form提交"
}'
echo '{
  "code": 401,
  "message": "用户名或密码错误"
}'
echo -e "\n"

# 提取并保存token (取消注释以启用)
# ACCESS_TOKEN=$(cat "$RESPONSE_FILE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
# echo "获取到的访问令牌: $ACCESS_TOKEN"

# 清理临时文件
rm -f "$RESPONSE_FILE" 