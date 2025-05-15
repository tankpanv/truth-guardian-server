from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flasgger import swag_from
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from app import db
from app.models.user import User

# 使用"/auth"前缀的蓝图，用于前端页面路由
auth_bp = Blueprint('auth', __name__)

# 前端路由 - 登录页面
@auth_bp.route('/login', methods=['GET'])
def login_view():
    return render_template('auth/login.html')

# 前端路由 - 注册页面
@auth_bp.route('/register', methods=['GET'])
def register_view():
    return render_template('auth/register.html')

# API路由蓝图，使用"/api/auth"前缀
authapi_bp = Blueprint('authapi', __name__, url_prefix='/api/auth')

# API路由 - 登录接口
@authapi_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['用户认证'],
    'summary': '用户登录',
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'username': {'type': 'string'},
                        'password': {'type': 'string'}
                    },
                    'required': ['username', 'password']
                }
            }
        }
    },
    'responses': {
        200: {
            'description': '登录成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'},
                            'refresh_token': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def login():
    # 获取请求数据，兼容不同的Content-Type
    if request.is_json:
        data = request.get_json()
    elif request.form:
        # 处理form表单数据
        data = request.form.to_dict()
    else:
        return jsonify({"code": 400, "message": "不支持的请求格式，请使用JSON或Form提交"}), 400

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"code": 400, "message": "缺少用户名或密码"}), 400

    user = User.query.filter_by(user_name=data.get('username')).first()

    if not user or not user.check_password(data.get('password')):
        return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

    # 创建访问令牌和刷新令牌
    access_token = create_access_token(identity={'id': user.id, 'username': user.user_name, 'type': 'admin'})
    refresh_token = create_refresh_token(identity={'id': user.id, 'username': user.user_name, 'type': 'admin'})

    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

# API路由 - 注册接口
@authapi_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['用户管理'],
    'summary': '用户注册',
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user_name': {'type': 'string'},
                        'password': {'type': 'string'},
                        'name': {'type': 'string'},
                        'phone': {'type': 'string'},
                        'bio': {'type': 'string'},
                        'tags': {'type': 'array', 'items': {'type': 'string'}},
                        'interests': {'type': 'array', 'items': {'type': 'string'}},
                        'avatar_url': {'type': 'string'}
                    },
                    'required': ['user_name', 'password', 'name']
                }
            }
        }
    },
    'responses': {
        201: {
            'description': '注册成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'msg': {'type': 'string'},
                            'user_id': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def register():
    # 获取请求数据，兼容不同的Content-Type
    if request.is_json:
        data = request.get_json()
    elif request.form:
        # 处理form表单数据
        data = request.form.to_dict()
    else:
        return jsonify({"code": 400, "message": "不支持的请求格式，请使用JSON或Form提交"}), 400

    required_fields = ['user_name', 'password', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "缺少必填字段"}), 400

    if User.query.filter_by(user_name=data['user_name']).first():
        return jsonify({"code": 409, "message": "用户名已存在"}), 409, {'Content-Type': 'application/json; charset=utf-8'}

    try:
        # 处理标签和兴趣，将列表转换为逗号分隔的字符串
        tags = ','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')
        interests = ','.join(data.get('interests', [])) if isinstance(data.get('interests'), list) else data.get('interests', '')
        
        new_user = User(
            user_name=data['user_name'],
            name=data['name'],
            phone=data.get('phone'),
            bio=data.get('bio', ''),
            tags=tags,
            interests=interests,
            avatar_url=data.get('avatar_url', '')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "用户注册成功", "user_id": new_user.id}), 201, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": str(e)}), 500

# API路由 - 刷新令牌
@authapi_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@swag_from({
    'tags': ['用户认证'],
    'summary': '刷新令牌',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'required': True,
            'schema': {
                'type': 'string',
                'example': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImV4cCI6MTYxNDUwMzYwMH0.7w8-q4nO5VlbVn5omPTUpnR2yDwxhd0OjAqP_pFYzGI'
            },
            'description': '包含JWT刷新令牌的认证头'
        }
    ],
    'responses': {
        200: {
            'description': '刷新成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def refresh():
    current_user = get_jwt_identity()
    
    # 确保identity包含必要的字段
    if isinstance(current_user, dict):
        if 'type' not in current_user:
            current_user['type'] = 'admin'
    
    new_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_token)

# API路由 - 获取当前用户信息
@authapi_bp.route('/user', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    获取当前登录用户的信息
    ---
    tags:
      - 认证
    security:
      - jwt: []
    responses:
      200:
        description: 用户信息获取成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: 用户ID
                    user_name:
                      type: string
                      description: 用户名
                    name:
                      type: string
                      description: 用户姓名
                    phone:
                      type: string
                      description: 电话号码
                    bio:
                      type: string
                      description: 个人签名
                    tags:
                      type: array
                      items:
                        type: string
                      description: 用户标签
                    interests:
                      type: array
                      items:
                        type: string
                      description: 用户兴趣
                    avatar_url:
                      type: string
                      description: 头像URL
                    created_at:
                      type: string
                      format: date-time
                      description: 注册时间
                    updated_at:
                      type: string
                      format: date-time
                      description: 最后更新时间
      401:
        description: 未授权或令牌无效
    """
    current_user = get_jwt_identity()
    user_id = None
    
    # 解析用户ID
    if isinstance(current_user, dict):
        user_id = current_user.get('id')
    elif isinstance(current_user, str):
        try:
            if current_user.startswith('"') and current_user.endswith('"'):
                current_user = current_user[1:-1]
            
            import json
            user_data = json.loads(current_user.replace('\\', ''))
            user_id = user_data.get('id')
        except:
            try:
                user_id = int(current_user)
            except:
                return jsonify({"error": "无法识别用户身份"}), 401
    
    if not user_id:
        return jsonify({"error": "无法识别用户身份"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    # 构建用户信息响应，包含新增字段
    response = {
        "data": {
            "id": user.id,
            "user_name": user.user_name,
            "name": user.name,
            "phone": user.phone,
            "bio": user.bio or "",
            "tags": user.tags_list(),
            "interests": user.interests_list(),
            "avatar_url": user.avatar_url or "",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    }
    
    return jsonify(response), 200

# API路由 - 更新当前用户信息
@authapi_bp.route('/user', methods=['PUT'])
@jwt_required()
def update_current_user():
    """
    更新当前登录用户的信息
    ---
    tags:
      - 认证
    security:
      - jwt: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                description: 用户姓名
              phone:
                type: string
                description: 电话号码
              bio:
                type: string
                description: 个人签名
              tags:
                type: array
                items:
                  type: string
                description: 用户标签
              interests:
                type: array
                items:
                  type: string
                description: 用户兴趣
              avatar_url:
                type: string
                description: 头像URL
              current_password:
                type: string
                description: 当前密码，如果要修改密码则必须提供
              new_password:
                type: string
                description: 新密码，可选项
    responses:
      200:
        description: 用户信息更新成功
      400:
        description: 请求参数错误
      401:
        description: 未授权或密码验证失败
      404:
        description: 用户不存在
    """
    current_user = get_jwt_identity()
    user_id = None
    
    # 解析用户ID
    if isinstance(current_user, dict):
        user_id = current_user.get('id')
    elif isinstance(current_user, str):
        try:
            if current_user.startswith('"') and current_user.endswith('"'):
                current_user = current_user[1:-1]
            
            import json
            user_data = json.loads(current_user.replace('\\', ''))
            user_id = user_data.get('id')
        except:
            try:
                user_id = int(current_user)
            except:
                return jsonify({"error": "无法识别用户身份"}), 401
    
    if not user_id:
        return jsonify({"error": "无法识别用户身份"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "无效的请求数据"}), 400
    
    # 如果要更新密码，需要验证当前密码
    if 'new_password' in data:
        current_password = data.get('current_password')
        if not current_password or not user.check_password(current_password):
            return jsonify({"error": "当前密码验证失败"}), 401
        
        user.set_password(data['new_password'])
    
    # 更新基本信息
    for field in ['name', 'phone', 'bio', 'avatar_url']:
        if field in data:
            setattr(user, field, data[field])
    
    # 更新标签和兴趣，将列表转换为逗号分隔的字符串
    if 'tags' in data:
        user.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']
    
    if 'interests' in data:
        user.interests = ','.join(data['interests']) if isinstance(data['interests'], list) else data['interests']
    
    db.session.commit()
    
    return jsonify({"message": "用户信息更新成功"}), 200

# 前端路由 - 用户资料页面
@auth_bp.route('/profile', methods=['GET'])
def user_profile_page():
    """用户个人资料页面"""
    return render_template('auth/user_profile.html') 