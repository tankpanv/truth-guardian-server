#!/bin/bash

# 设置服务器地址
SERVER="http://localhost:5005"

# 输出分隔线函数
separator() {
  echo "----------------------------------------"
  echo "$1"
  echo "----------------------------------------"
}

# 保存登录获取的token
get_token() {
  TOKEN=$(curl -s -X POST "${SERVER}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "username": "admin",
      "password": "admin123"
    }' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
  
  echo "获取到的访问令牌: $TOKEN"
}

# 获取token
get_token

# 辟谣管理相关接口
separator "辟谣管理 API"

# 1. 发布辟谣文章
separator "1. 发布辟谣文章"
curl -X POST "${SERVER}/api/debunk/articles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "关于XX谣言的辟谣",
    "content": "近日，网络上流传一则关于XX的谣言，经核实，该消息不实...",
    "summary": "XX谣言不实，官方辟谣",
    "source": "XX官方网站",
    "tags": ["健康", "社会", "官方辟谣"],
    "rumor_reports": [1, 2],
    "clarification_reports": [1]
  }'
echo -e "\n"

# 2. 获取辟谣文章列表
separator "2. 获取辟谣文章列表"
curl -X GET "${SERVER}/api/debunk/articles?page=1&per_page=10&status=published&search=谣言" \
  -H "Content-Type: application/json"
echo -e "\n"

# 3. 获取辟谣文章详情
separator "3. 获取辟谣文章详情"
curl -X GET "${SERVER}/api/debunk/articles/1" \
  -H "Content-Type: application/json"
echo -e "\n"

# 4. 编辑辟谣文章
separator "4. 编辑辟谣文章"
curl -X PUT "${SERVER}/api/debunk/articles/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "更新：关于XX谣言的辟谣",
    "content": "近日，网络上流传一则关于XX的谣言，经核实，该消息不实...(已更新)",
    "summary": "XX谣言不实，官方最新辟谣",
    "tags": ["健康", "社会", "官方辟谣", "重要更新"],
    "rumor_reports": [1, 2, 3],
    "clarification_reports": [1, 2]
  }'
echo -e "\n"

# 5. 修改辟谣文章状态
separator "5. 修改辟谣文章状态"
curl -X PATCH "${SERVER}/api/debunk/articles/1/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "archived"
  }'
echo -e "\n"

# 6. 删除辟谣文章
separator "6. 删除辟谣文章"
curl -X DELETE "${SERVER}/api/debunk/articles/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n"

# 创建辟谣文章
create_article() {
  echo "创建辟谣文章..."
  curl -X POST "${SERVER}/api/debunk/articles" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{
      "title": "测试辟谣文章",
      "content": "这是一篇测试用的辟谣文章内容",
      "summary": "测试摘要",
      "source": "测试来源",
      "tags": ["测试", "辟谣", "自动化"]
    }'
  echo -e "\n"
}

# 获取辟谣文章列表
get_articles() {
  echo "获取辟谣文章列表..."
  curl -X GET "${SERVER}/api/debunk/articles?page=1&per_page=10&status=published&search=谣言" \
    -H "Authorization: Bearer ${TOKEN}"
  echo -e "\n"
}

# 获取辟谣文章详情
get_article_detail() {
  echo "获取辟谣文章详情..."
  curl -X GET "${SERVER}/api/debunk/articles/1" \
    -H "Authorization: Bearer ${TOKEN}"
  echo -e "\n"
}

# 更新辟谣文章
update_article() {
  echo "更新辟谣文章..."
  curl -X PUT "${SERVER}/api/debunk/articles/1" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{
      "title": "更新后的辟谣文章",
      "content": "这是更新后的辟谣文章内容",
      "summary": "更新后的摘要",
      "source": "更新后的来源",
      "tags": ["更新", "辟谣", "测试"]
    }'
  echo -e "\n"
}

# 更新辟谣文章状态
update_article_status() {
  echo "更新辟谣文章状态..."
  curl -X PATCH "${SERVER}/api/debunk/articles/1/status" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{
      "status": "archived"
    }'
  echo -e "\n"
}

# 删除辟谣文章
delete_article() {
  echo "删除辟谣文章..."
  curl -X DELETE "${SERVER}/api/debunk/articles/1" \
    -H "Authorization: Bearer ${TOKEN}"
  echo -e "\n"
} 