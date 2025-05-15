#!/bin/bash

# 设置基础URL和认证token
BASE_URL="http://your-domain"
AUTH_TOKEN="your_jwt_token"

echo "Truth Guardian API 接口文档"
echo "=========================="

echo "1. 用户详情接口"
echo "请求示例:"
echo 'curl -X GET "${BASE_URL}/api/auth/user" \
-H "Authorization: Bearer ${AUTH_TOKEN}"'

echo "返回示例:"
echo '{
    "success": true,
    "message": "获取成功",
    "data": {
        "id": 1,
        "name": "user1",
        "user_name": "user1",
        "phone": "12345678901",
        "avatar_url": "",
        "bio": "今天好开心",
        "interests": [],
        "tags": [],
        "created_at": null,
        "updated_at": "2025-04-20T13:17:39"
    }
}'

echo -e "\n2. 获取用户发布的辟谣文章列表"
echo "请求示例:"
echo 'curl -X GET "${BASE_URL}/api/debunk/articles?author_id=123&page=1&per_page=10" \
-H "Content-Type: application/json"'

echo "返回示例:"
echo '{
    "articles": [
        {
            "id": 1,
            "title": "辟谣文章标题",
            "summary": "文章摘要",
            "source": "信息来源",
            "author_id": 123,
            "author": {
                "id": 123,
                "username": "作者名称"
            },
            "status": "published",
            "created_at": "2024-03-20 10:00:00",
            "updated_at": "2024-03-20 10:00:00",
            "published_at": "2024-03-20 10:00:00",
            "tags": ["标签1", "标签2"]
        }
    ],
    "total": 100,
    "pages": 10,
    "current_page": 1
}'

echo -e "\n3. 获取用户文章详情"
echo "请求示例:"
echo 'curl -X GET "${BASE_URL}/api/debunk/articles/1" \
-H "Content-Type: application/json"'

echo "返回示例:"
echo '{
    "id": 1,
    "title": "文章标题",
    "content": "文章详细内容",
    "summary": "文章摘要",
    "source": "信息来源",
    "author_id": 123,
    "author": {
        "id": 123,
        "username": "作者名称"
    },
    "status": "published",
    "created_at": "2024-03-20 10:00:00",
    "updated_at": "2024-03-20 10:00:00",
    "published_at": "2024-03-20 10:00:00",
    "tags": ["标签1", "标签2"],
    "rumor_reports": [
        {
            "id": 1,
            "title": "谣言报道标题",
            "source": "来源",
            "published_at": "2024-03-20 10:00:00"
        }
    ],
    "clarification_reports": [
        {
            "id": 2,
            "title": "澄清报道标题",
            "source": "来源",
            "published_at": "2024-03-20 10:00:00"
        }
    ]
}'

echo -e "\n4. 发布辟谣文章"
echo "请求示例:"
echo 'curl -X POST "${BASE_URL}/api/debunk/articles" \
-H "Authorization: Bearer ${AUTH_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
    "title": "辟谣文章标题",
    "content": "文章详细内容",
    "summary": "文章摘要",
    "source": "信息来源",
    "tags": ["标签1", "标签2"],
    "rumor_reports": [1, 2],
    "clarification_reports": [3, 4]
}''

echo "返回示例:"
echo '{
    "success": true,
    "message": "辟谣文章发布成功",
    "data": {
        "article_id": 1
    }
}'

echo -e "\n5. 编辑辟谣文章"
echo "请求示例:"
echo 'curl -X PUT "${BASE_URL}/api/debunk/articles/1" \
-H "Authorization: Bearer ${AUTH_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
    "title": "更新后的标题",
    "content": "更新后的内容",
    "summary": "更新后的摘要",
    "source": "更新后的来源",
    "tags": ["新标签1", "新标签2"],
    "rumor_reports": [5, 6],
    "clarification_reports": [7, 8]
}''

echo "返回示例:"
echo '{
    "success": true,
    "message": "辟谣文章更新成功"
}'

echo -e "\n6. 搜索辟谣文章"
echo "请求示例:"
echo 'curl -X GET "${BASE_URL}/api/debunk/articles?search=关键词&status=published&page=1&per_page=10" \
-H "Content-Type: application/json"'

echo "返回示例:"
echo '{
    "articles": [
        {
            "id": 1,
            "title": "辟谣文章标题",
            "summary": "文章摘要",
            "source": "信息来源",
            "author_id": 123,
            "author": {
                "id": 123,
                "username": "作者名称"
            },
            "status": "published",
            "created_at": "2024-03-20 10:00:00",
            "updated_at": "2024-03-20 10:00:00",
            "published_at": "2024-03-20 10:00:00",
            "tags": ["标签1", "标签2"]
        }
    ],
    "total": 100,
    "pages": 10,
    "current_page": 1
}'

echo -e "\n7. 编辑用户信息"
echo "请求示例:"
echo 'curl -X PUT "${BASE_URL}/api/auth/user" \
-H "Authorization: Bearer ${AUTH_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
    "name": "新用户名",
    "user_name": "新用户名",
    "phone": "新手机号",
    "avatar_url": "新头像URL",
    "bio": "新个人简介",
    "interests": ["兴趣1", "兴趣2"],
    "tags": ["标签1", "标签2"],
    "old_password": "旧密码",
    "new_password": "新密码"  // 可选，如果不修改密码则不需要提供
}''

echo "返回示例:"
echo '{
    "success": true,
    "message": "用户信息更新成功",
    "data": {
        "id": 1,
        "name": "新用户名",
        "user_name": "新用户名",
        "phone": "新手机号",
        "avatar_url": "新头像URL",
        "bio": "新个人简介",
        "interests": ["兴趣1", "兴趣2"],
        "tags": ["标签1", "标签2"],
        "created_at": null,
        "updated_at": "2025-04-20T13:17:39"
    }
}'

echo "错误返回示例:"
echo '{
    "success": false,
    "message": "更新失败的具体原因",
    "errors": {
        "username": "用户名已存在",
        "email": "邮箱格式不正确",
        "old_password": "旧密码不正确"
    }
}'

echo -e "\n8. 创建辟谣文章"
echo "请求示例:"
echo 'curl -X POST "${BASE_URL}/api/debunk/articles" \
-H "Authorization: Bearer ${AUTH_TOKEN}" \
-H "Content-Type: application/json" \
-d '{
    "title": "辟谣文章标题",
    "content": "文章详细内容",
    "summary": "文章摘要",
    "source": "信息来源",
    "tags": ["标签1", "标签2"],
    "rumor_reports": [
        {
            "title": "谣言标题1",
            "content": "谣言内容1",
            "source": "谣言来源1",
            "published_at": "2024-03-20 10:00:00"
        }
    ],
    "clarification_reports": [
        {
            "title": "澄清标题1",
            "content": "澄清内容1",
            "source": "澄清来源1",
            "published_at": "2024-03-20 11:00:00"
        }
    ]
}''

echo "返回示例:"
echo '{
    "success": true,
    "message": "辟谣文章创建成功",
    "data": {
        "id": 1,
        "title": "辟谣文章标题",
        "content": "文章详细内容",
        "summary": "文章摘要",
        "source": "信息来源",
        "author_id": 123,
        "author": {
            "id": 123,
            "name": "作者名称",
            "avatar_url": "作者头像"
        },
        "status": "published",
        "created_at": "2024-03-20T10:00:00",
        "updated_at": "2024-03-20T10:00:00",
        "published_at": "2024-03-20T10:00:00",
        "tags": ["标签1", "标签2"],
        "rumor_reports": [
            {
                "id": 1,
                "title": "谣言标题1",
                "content": "谣言内容1",
                "source": "谣言来源1",
                "published_at": "2024-03-20T10:00:00"
            }
        ],
        "clarification_reports": [
            {
                "id": 2,
                "title": "澄清标题1",
                "content": "澄清内容1",
                "source": "澄清来源1",
                "published_at": "2024-03-20T11:00:00"
            }
        ]
    }
}'

echo "错误返回示例:"
echo '{
    "success": false,
    "message": "创建失败",
    "errors": {
        "title": "标题不能为空",
        "content": "内容不能为空",
        "rumor_reports": "至少需要一条谣言报道",
        "clarification_reports": "至少需要一条澄清报道"
    }
}'

echo -e "\n注意事项:"
echo "1. 所有需要认证的接口都需要在请求头中携带 JWT token"
echo "2. 文章状态包括：draft(草稿)、published(已发布)、archived(已归档)"
echo "3. 分页参数：page 默认为1，per_page 默认为10，最大为100"
echo "4. 搜索功能支持标题、内容、摘要和标签的模糊匹配"
echo "5. 所有接口返回的时间格式统一为：YYYY-MM-DD HH:MM:SS"
echo "6. 用户相关接口需要认证"
echo "7. 文章列表支持按作者ID筛选"
echo "8. tags字段始终返回数组格式"
echo "9. 用户信息编辑时，密码字段是可选的"
echo "10. 修改密码时必须提供正确的旧密码"
echo "11. 用户名和邮箱更新时会检查唯一性"
echo "12. 创建文章时谣言和澄清报道至少需要一条"
echo "13. 文章创建后默认状态为published"
echo "14. 所有时间字段使用ISO格式"
