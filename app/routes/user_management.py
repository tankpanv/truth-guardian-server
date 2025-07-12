from flask import Blueprint, request, jsonify
from app.models.user import User
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

user_management_bp = Blueprint('user_management', __name__, url_prefix='/api/users')

@user_management_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['用户管理'],
    'summary': '获取用户列表',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'schema': {'type': 'integer', 'default': 1},
            'description': '页码'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'schema': {'type': 'integer', 'default': 10},
            'description': '每页条数'
        },
        {
            'name': 'search',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '搜索关键词（用户名或姓名）'
        },
        {
            'name': 'all',
            'in': 'query',
            'schema': {'type': 'boolean', 'default': False},
            'description': '是否获取所有用户'
        }
    ],
    'responses': {
        200: {
            'description': '获取用户列表成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'users': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'id': {'type': 'integer'},
                                                'user_name': {'type': 'string'},
                                                'name': {'type': 'string'},
                                                'phone': {'type': 'string'},
                                                'bio': {'type': 'string'},
                                                'avatar_url': {'type': 'string'},
                                                'created_at': {'type': 'string'},
                                                'updated_at': {'type': 'string'}
                                            }
                                        }
                                    },
                                    'total': {'type': 'integer'},
                                    'pages': {'type': 'integer'},
                                    'page': {'type': 'integer'},
                                    'per_page': {'type': 'integer'}
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': '未授权'
        }
    }
})
def get_users():
    """获取用户列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        all_users = request.args.get('all', 'false').lower() == 'true'
        
        # 构建查询
        query = User.query
        
        # 搜索功能
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.user_name.ilike(search_term)) | 
                (User.name.ilike(search_term))
            )
        
        # 排序
        query = query.order_by(User.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建响应
        users = []
        for user in pagination.items:
            users.append({
                'id': user.id,
                'user_name': user.user_name,
                'name': user.name,
                'phone': user.phone,
                'bio': user.bio or '',
                'avatar_url': user.avatar_url or '',
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            })
        
        return jsonify({
            'data': {
                'users': users,
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500

@user_management_bp.route('/search', methods=['GET'])
# @jwt_required()  # 移除登录限制
@swag_from({
    'tags': ['用户管理'],
    'summary': '搜索用户',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'username',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '用户名'
        },
        {
            'name': 'name',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '姓名'
        }
    ],
    'responses': {
        200: {
            'description': '搜索用户成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'users': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def search_users():
    """搜索用户"""
    try:
        username = request.args.get('username')
        name = request.args.get('name')
        
        query = User.query
        
        if username:
            query = query.filter(User.user_name.ilike(f'%{username}%'))
        if name:
            query = query.filter(User.name.ilike(f'%{name}%'))
        
        users = query.all()
        
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'user_name': user.user_name,
                'name': user.name,
                'phone': user.phone,
                'bio': user.bio or '',
                'avatar_url': user.avatar_url or ''
            })
        
        return jsonify({
            'data': {
                'users': result
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'搜索用户失败: {str(e)}'}), 500 