#!/bin/bash

# 设置服务器地址
SERVER="http://localhost:5005"

# 输出分隔线函数
separator() {
  echo "----------------------------------------"
  echo "$1"
  echo "----------------------------------------"
}

# 保存返回结果到变量的函数
save_response() {
  local response=$1
  echo "$response" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
}

# 保存登录获取的token
get_token() {
  local response=$(curl -s -X POST "${SERVER}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "username": "user1",
      "password": "user1123456"
    }')
  
  TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
  
  echo "获取到的访问令牌: $TOKEN"
  echo "登录响应结构："
  save_response "$response"
}

# 获取token
get_token

# 辟谣管理相关接口
separator "辟谣管理 API"

# 1. 发布辟谣文章
separator "1. 发布辟谣文章"
echo "请求:"
echo "POST ${SERVER}/api/debunk/articles"
echo "请求体:"
cat <<EOF
{
  "title": "辟谣：饮用热水可以预防新型冠状病毒",
  "content": "网络上流传饮用热水可以预防新型冠状病毒的说法是不科学的。病毒预防需要科学的防护措施，单纯依靠饮用热水无法有效预防病毒感染。",
  "summary": "饮用热水无法有效预防新型冠状病毒",
  "source": "卫生部官方网站",
  "tags": ["健康", "新冠病毒", "谣言"]
}
EOF
echo ""

echo "响应:"
response=$(curl -s -X POST "${SERVER}/api/debunk/articles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "辟谣：饮用热水可以预防新型冠状病毒",
    "content": "网络上流传饮用热水可以预防新型冠状病毒的说法是不科学的。病毒预防需要科学的防护措施，单纯依靠饮用热水无法有效预防病毒感染。",
    "summary": "饮用热水无法有效预防新型冠状病毒",
    "source": "卫生部官方网站",
    "tags": ["健康", "新冠病毒", "谣言"]
  }')
echo $response | jq .
echo ""

# 提取文章ID供后续使用
article_id=$(echo $response | jq -r '.article_id')
if [ "$article_id" == "null" ]; then
  article_id=1
  echo "提取文章ID失败，使用默认ID: 1"
else
  echo "提取的文章ID: $article_id"
fi

# 2. 获取辟谣文章列表
separator "2. 获取辟谣文章列表"
echo "请求:"
echo "GET ${SERVER}/api/debunk/articles?page=1&per_page=10&status=published&search=谣言"
echo ""

echo "响应:"
response=$(curl -s -X GET "${SERVER}/api/debunk/articles?page=1&per_page=10&status=published&search=谣言" \
  -H "Authorization: Bearer $TOKEN")
echo $response | jq .
echo ""

# 3. 获取辟谣文章详情
separator "3. 获取辟谣文章详情"
echo "请求:"
echo "GET ${SERVER}/api/debunk/articles/${article_id}"
echo ""

echo "响应:"
response=$(curl -s -X GET "${SERVER}/api/debunk/articles/1" \
  -H "Authorization: Bearer $TOKEN")
echo $response | jq .
echo ""

# 4. 编辑辟谣文章
separator "4. 编辑辟谣文章"
echo "请求:"
echo "PUT ${SERVER}/api/debunk/articles/${article_id}"
echo "请求体:"
cat <<EOF
{
  "title": "更新：饮用热水可以预防新型冠状病毒的说法不实",
  "content": "近期社交媒体上流传饮用热水可以预防新型冠状病毒的说法是不科学的。根据世界卫生组织的指导，病毒预防需要科学的防护措施，包括勤洗手、保持社交距离、正确佩戴口罩等，单纯依靠饮用热水无法有效预防病毒感染。",
  "summary": "世卫组织：饮用热水无法有效预防新型冠状病毒",
  "source": "世界卫生组织官方声明",
  "tags": ["健康", "新冠病毒", "谣言辟谣", "世卫组织"]
}
EOF
echo ""

echo "响应:"
response=$(curl -s -X PUT "${SERVER}/api/debunk/articles/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "更新：饮用热水可以预防新型冠状病毒的说法不实",
    "content": "近期社交媒体上流传饮用热水可以预防新型冠状病毒的说法是不科学的。根据世界卫生组织的指导，病毒预防需要科学的防护措施，包括勤洗手、保持社交距离、正确佩戴口罩等，单纯依靠饮用热水无法有效预防病毒感染。",
    "summary": "世卫组织：饮用热水无法有效预防新型冠状病毒",
    "source": "世界卫生组织官方声明",
    "tags": ["健康", "新冠病毒", "谣言辟谣", "世卫组织"]
  }')
echo $response | jq .
echo ""

# 5. 修改辟谣文章状态
separator "5. 修改辟谣文章状态"
echo "请求:"
echo "PATCH ${SERVER}/api/debunk/articles/${article_id}/status"
echo "请求体:"
cat <<EOF
{
  "status": "archived"
}
EOF
echo ""

echo "响应:"
response=$(curl -s -X PATCH "${SERVER}/api/debunk/articles/1/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "archived"
  }')
echo $response | jq .
echo ""

# 6. 删除辟谣文章
separator "6. 删除辟谣文章"
echo "请求:"
echo "DELETE ${SERVER}/api/debunk/articles/${article_id}"
echo ""

echo "响应:"
response=$(curl -s -X DELETE "${SERVER}/api/debunk/articles/1" \
  -H "Authorization: Bearer $TOKEN")
echo $response | jq .
echo ""

echo "API 测试完成！"

# 通用错误响应示例
separator "常见错误响应示例"
echo "错误响应示例："
cat << 'EOF' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
{
  "status": "error",
  "message": "未找到指定的辟谣文章",
  "error_code": "article_not_found"
}
EOF 