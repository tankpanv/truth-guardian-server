from flask import Blueprint, jsonify, request, render_template, redirect, url_for, abort
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.debunk import DebunkArticle, RumorReport, ClarificationReport, WeiboDebunk
from datetime import datetime
import json
from urllib.parse import unquote
from app.models.user import User

# API 蓝图
debunk_bp = Blueprint('debunk', __name__, url_prefix='/api/debunk')

# 前端页面蓝图
debunk_view_bp = Blueprint('debunk_view', __name__, url_prefix='/debunk')

@debunk_bp.route('/articles', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '发布辟谣文章',
    'security': [{'BearerAuth': []}],
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'description': '文章标题'},
                        'content': {'type': 'string', 'description': '文章内容'},
                        'summary': {'type': 'string', 'description': '文章摘要'},
                        'source': {'type': 'string', 'description': '文章来源'},
                        'tags': {'type': 'array', 'items': {'type': 'string'}, 'description': '标签'},
                        'rumor_reports': {'type': 'array', 'items': {'type': 'integer'}, 'description': '关联谣言报道ID列表'},
                        'clarification_reports': {'type': 'array', 'items': {'type': 'integer'}, 'description': '关联澄清报道ID列表'}
                    },
                    'required': ['title', 'content']
                }
            }
        }
    },
    'responses': {
        201: {
            'description': '文章发布成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'},
                            'article_id': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def create_article():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"code": 400, "message": "缺少必填字段"}), 400, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        # 处理JWT身份，可能返回字符串或字典
        author_id = None
        user_type = None
        
        if isinstance(current_user, dict):
            author_id = current_user.get('id')
            user_type = current_user.get('type', 'admin')
        elif isinstance(current_user, str):
            # 尝试解析JSON字符串
            try:
                # 处理可能被二次转义的JSON字符串
                if current_user.startswith('"') and current_user.endswith('"'):
                    current_user = current_user[1:-1]
                
                user_data = json.loads(current_user.replace('\\', ''))
                author_id = user_data.get('id')
                user_type = user_data.get('type', 'admin')
            except Exception as e:
                # 如果是单个数字，可能是老版本的用户ID
                try:
                    author_id = int(current_user)
                    user_type = 'admin'  # 默认为admin
                except (ValueError, TypeError):
                    return jsonify({"code": 401, "message": f"无效的用户身份: {str(e)}"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify({"code": 401, "message": "无效的用户身份格式"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
            
        if not author_id:
            return jsonify({"code": 401, "message": "缺少用户ID"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
            
        # 创建新文章
        article = DebunkArticle(
            title=data['title'],
            content=data['content'],
            summary=data.get('summary', ''),
            source=data.get('source', ''),
            author_id=author_id,
            published_at=datetime.now(),
            status='published'  # 默认为已发布状态
        )
        
        # 添加标签
        if 'tags' in data and isinstance(data['tags'], list):
            article.tags = ','.join(data['tags'])
        
        db.session.add(article)
        db.session.flush()  # 获取文章ID
        
        # 关联谣言报道
        if 'rumor_reports' in data and isinstance(data['rumor_reports'], list):
            for report_id in data['rumor_reports']:
                report = RumorReport.query.get(report_id)
                if report:
                    article.rumor_reports.append(report)
        
        # 关联澄清报道
        if 'clarification_reports' in data and isinstance(data['clarification_reports'], list):
            for report_id in data['clarification_reports']:
                report = ClarificationReport.query.get(report_id)
                if report:
                    article.clarification_reports.append(report)
        
        db.session.commit()
        return jsonify({"message": "辟谣文章发布成功", "article_id": article.id}), 201, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/articles/<int:article_id>', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '编辑辟谣文章',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'article_id',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'description': '文章标题'},
                        'content': {'type': 'string', 'description': '文章内容'},
                        'summary': {'type': 'string', 'description': '文章摘要'},
                        'source': {'type': 'string', 'description': '文章来源'},
                        'tags': {'type': 'array', 'items': {'type': 'string'}, 'description': '标签'},
                        'rumor_reports': {'type': 'array', 'items': {'type': 'integer'}, 'description': '关联谣言报道ID列表'},
                        'clarification_reports': {'type': 'array', 'items': {'type': 'integer'}, 'description': '关联澄清报道ID列表'}
                    }
                }
            }
        }
    },
    'responses': {
        200: {
            'description': '文章更新成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def update_article(article_id):
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"code": 400, "message": "缺少更新数据"}), 400, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        article = DebunkArticle.query.get(article_id)
        if not article:
            return jsonify({"code": 404, "message": "文章不存在"}), 404, {'Content-Type': 'application/json; charset=utf-8'}
        
        # 处理JWT身份，可能返回字符串或字典
        author_id = None
        user_type = None
        
        if isinstance(current_user, dict):
            author_id = current_user.get('id')
            user_type = current_user.get('type')
        elif isinstance(current_user, str):
            # 尝试解析JSON字符串
            try:
                # 处理可能被二次转义的JSON字符串
                if current_user.startswith('"') and current_user.endswith('"'):
                    current_user = current_user[1:-1]
                
                user_data = json.loads(current_user.replace('\\', ''))
                author_id = user_data.get('id')
                user_type = user_data.get('type', 'admin')
            except Exception as e:
                # 如果是单个数字，可能是老版本的用户ID
                try:
                    author_id = int(current_user)
                    user_type = 'admin'  # 默认为admin
                except (ValueError, TypeError):
                    return jsonify({"code": 401, "message": f"无效的用户身份: {str(e)}"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify({"code": 401, "message": "无效的用户身份格式"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
            
        # 检查权限
        if article.author_id != author_id and user_type != 'admin':
            return jsonify({"code": 403, "message": "无权限编辑此文章"}), 403, {'Content-Type': 'application/json; charset=utf-8'}
        
        # 更新基本字段
        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'summary' in data:
            article.summary = data['summary']
        if 'source' in data:
            article.source = data['source']
        if 'tags' in data and isinstance(data['tags'], list):
            article.tags = ','.join(data['tags'])
        
        # 更新关联的谣言报道
        if 'rumor_reports' in data and isinstance(data['rumor_reports'], list):
            # 清除现有关联
            article.rumor_reports = []
            # 添加新关联
            for report_id in data['rumor_reports']:
                report = RumorReport.query.get(report_id)
                if report:
                    article.rumor_reports.append(report)
        
        # 更新关联的澄清报道
        if 'clarification_reports' in data and isinstance(data['clarification_reports'], list):
            # 清除现有关联
            article.clarification_reports = []
            # 添加新关联
            for report_id in data['clarification_reports']:
                report = ClarificationReport.query.get(report_id)
                if report:
                    article.clarification_reports.append(report)
        
        article.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({"message": "辟谣文章更新成功"}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '删除辟谣文章',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'article_id',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    'responses': {
        200: {
            'description': '文章删除成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def delete_article(article_id):
    current_user = get_jwt_identity()
    
    try:
        article = DebunkArticle.query.get(article_id)
        if not article:
            return jsonify({"code": 404, "message": "文章不存在"}), 404, {'Content-Type': 'application/json; charset=utf-8'}
        
        # 处理JWT身份，可能返回字符串或字典
        author_id = None
        user_type = None
        
        if isinstance(current_user, dict):
            author_id = current_user.get('id')
            user_type = current_user.get('type')
        elif isinstance(current_user, str):
            # 尝试解析JSON字符串
            try:
                # 处理可能被二次转义的JSON字符串
                if current_user.startswith('"') and current_user.endswith('"'):
                    current_user = current_user[1:-1]
                
                user_data = json.loads(current_user.replace('\\', ''))
                author_id = user_data.get('id')
                user_type = user_data.get('type', 'admin')
            except Exception as e:
                # 如果是单个数字，可能是老版本的用户ID
                try:
                    author_id = int(current_user)
                    user_type = 'admin'  # 默认为admin
                except (ValueError, TypeError):
                    return jsonify({"code": 401, "message": f"无效的用户身份: {str(e)}"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify({"code": 401, "message": "无效的用户身份格式"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
            
        # 检查权限
        if article.author_id != author_id and user_type != 'admin':
            return jsonify({"code": 403, "message": "无权限删除此文章"}), 403, {'Content-Type': 'application/json; charset=utf-8'}
        
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({"message": "辟谣文章已删除"}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/articles/<int:article_id>/status', methods=['PATCH'])
@jwt_required()
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '修改辟谣文章状态',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'article_id',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['draft', 'published', 'archived']}
                    },
                    'required': ['status']
                }
            }
        }
    },
    'responses': {
        200: {
            'description': '状态更新成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def update_article_status(article_id):
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({"code": 400, "message": "缺少状态信息"}), 400, {'Content-Type': 'application/json; charset=utf-8'}
    
    if data['status'] not in ['draft', 'published', 'archived']:
        return jsonify({"code": 400, "message": "无效的状态值"}), 400, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        article = DebunkArticle.query.get(article_id)
        if not article:
            return jsonify({"code": 404, "message": "文章不存在"}), 404, {'Content-Type': 'application/json; charset=utf-8'}
        
        # 处理JWT身份，可能返回字符串或字典
        author_id = None
        user_type = None
        
        if isinstance(current_user, dict):
            author_id = current_user.get('id')
            user_type = current_user.get('type')
        elif isinstance(current_user, str):
            # 尝试解析JSON字符串
            try:
                # 处理可能被二次转义的JSON字符串
                if current_user.startswith('"') and current_user.endswith('"'):
                    current_user = current_user[1:-1]
                
                user_data = json.loads(current_user.replace('\\', ''))
                author_id = user_data.get('id')
                user_type = user_data.get('type', 'admin')
            except Exception as e:
                # 如果是单个数字，可能是老版本的用户ID
                try:
                    author_id = int(current_user)
                    user_type = 'admin'  # 默认为admin
                except (ValueError, TypeError):
                    return jsonify({"code": 401, "message": f"无效的用户身份: {str(e)}"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify({"code": 401, "message": "无效的用户身份格式"}), 401, {'Content-Type': 'application/json; charset=utf-8'}
            
        # 检查权限
        if article.author_id != author_id and user_type != 'admin':
            return jsonify({"code": 403, "message": "无权限修改此文章状态"}), 403, {'Content-Type': 'application/json; charset=utf-8'}
        
        article.status = data['status']
        article.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({"message": f"文章状态已更新为 {data['status']}"}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/articles', methods=['GET'])
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '获取辟谣文章列表',
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
            'name': 'status',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '文章状态筛选，使用"all"获取所有状态'
        },
        {
            'name': 'search',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '搜索关键词'
        },
        {
            'name': 'tags',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '标签筛选，多个标签用逗号分隔，例如：tags=科技,健康'
        }
    ],
    'responses': {
        200: {
            'description': '获取文章列表成功'
        }
    }
})
def get_articles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    tags = request.args.get('tags')
    
    # 调试信息：打印收到的所有参数
    print(f"DEBUG - 请求参数: page={page}, per_page={per_page}, status={status}, search={search}, tags={tags}")
    
    query = DebunkArticle.query
    
    # 筛选状态
    if status and status.lower() != 'all':
        print(f"DEBUG - 筛选状态: {status}")
        query = query.filter(DebunkArticle.status == status)
    else:
        print(f"DEBUG - 不筛选状态，返回所有状态的文章")
    
    # 标签筛选
    if tags and tags.strip():  # 确保tags参数存在且不为空字符串
        print(f"DEBUG - 启用标签筛选: {tags}")
        tag_list = tags.split(',')
        for tag in tag_list:
            # 对标签进行URL解码
            clean_tag = unquote(tag.strip())
            
            # 跳过空标签
            if not clean_tag:
                continue
                
            print(f"DEBUG - 筛选标签: {clean_tag}")
            
            # 使用更精确的标签匹配方式:
            # 1. 使用 ILIKE 而不是 LIKE 来忽略大小写
            # 2. 确保完全匹配单词而不是部分匹配
            tag_filter = (
                # 精确匹配单个标签（整个标签字段就是这一个标签）
                (DebunkArticle.tags.ilike(clean_tag)) | 
                # 标签在开头，后面跟着逗号
                (DebunkArticle.tags.ilike(f'{clean_tag},%')) |
                # 标签在中间，前后都有逗号
                (DebunkArticle.tags.ilike(f'%,{clean_tag},%')) |
                # 标签在结尾，前面有逗号
                (DebunkArticle.tags.ilike(f'%,{clean_tag}'))
            )
            
            # 检查数据库中是否存在匹配的标签
            tag_check = DebunkArticle.query.filter(tag_filter).first()
            if tag_check:
                print(f"DEBUG - 找到匹配标签 '{clean_tag}' 的文章，ID: {tag_check.id}, 标签: {tag_check.tags}")
            else:
                print(f"DEBUG - 未找到匹配标签 '{clean_tag}' 的文章")
                # 打印所有标签供对比
                all_tags = set()
                for article in DebunkArticle.query.all():
                    if article.tags:
                        for t in article.tags.split(','):
                            all_tags.add(t.strip())
                print(f"DEBUG - 数据库中所有可用标签: {all_tags}")
            
            query = query.filter(tag_filter)
    else:
        print("DEBUG - 未启用标签筛选，返回所有符合条件的文章")
    
    # 打印最终的SQL语句（如果可能）
    try:
        sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        print(f"DEBUG - 最终SQL: {sql}")
    except Exception as e:
        print(f"DEBUG - 无法打印SQL: {str(e)}")
        
    # 搜索功能
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (DebunkArticle.title.ilike(search_term)) | 
            (DebunkArticle.content.ilike(search_term)) |
            (DebunkArticle.summary.ilike(search_term)) |
            (DebunkArticle.tags.ilike(search_term))
        )
    
    # 排序：最新的文章优先
    query = query.order_by(DebunkArticle.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 调试日志：输出找到的文章及其标签
    print(f"DEBUG - 找到 {pagination.total} 篇文章")
    
    articles = []
    for article in pagination.items:
        # 获取文章标签
        article_tags = article.tags.split(',') if article.tags else []
        print(f"DEBUG - 文章ID: {article.id}, 标题: {article.title}, 标签: {article_tags}")
        
        # 获取作者信息
        author_info = None
        if article.author:
            author_info = {
                'id': article.author.id,
                'username': article.author.username if hasattr(article.author, 'username') else '辟谣小能手'
            }
            
        articles.append({
            'id': article.id,
            'title': article.title,
            'summary': article.summary,
            'source': article.source,
            'author_id': article.author_id,
            'author': author_info,  # 添加作者信息
            'status': article.status,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
            'updated_at': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
            'published_at': article.published_at.strftime('%Y-%m-%d %H:%M:%S') if article.published_at else None,
            'tags': article_tags
        })
    
    return jsonify({
        'data': {
            'items': articles,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page
        }
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/articles/<int:article_id>', methods=['GET'])
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '获取辟谣文章详情',
    'parameters': [
        {
            'name': 'article_id',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'}
        }
    ],
    'responses': {
        200: {
            'description': '获取文章详情成功'
        }
    }
})
def get_article_detail(article_id):
    article = DebunkArticle.query.get(article_id)
    
    if not article:
        return jsonify({"code": 404, "message": "文章不存在"}), 404, {'Content-Type': 'application/json; charset=utf-8'}
    
    # 获取关联的谣言报道
    rumor_reports = []
    for report in article.rumor_reports:
        rumor_reports.append({
            'id': report.id,
            'title': report.title,
            'source': report.source,
            'published_at': report.published_at.strftime('%Y-%m-%d %H:%M:%S') if report.published_at else None
        })
    
    # 获取关联的澄清报道
    clarification_reports = []
    for report in article.clarification_reports:
        clarification_reports.append({
            'id': report.id,
            'title': report.title,
            'source': report.source,
            'published_at': report.published_at.strftime('%Y-%m-%d %H:%M:%S') if report.published_at else None
        })
    
    # 获取作者信息
    author_info = None
    if article.author:
        author_info = {
            'id': article.author.id,
            'username': article.author.username if hasattr(article.author, 'username') else '辟谣小能手'
        }
        
    article_data = {
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'summary': article.summary,
        'source': article.source,
        'author_id': article.author_id,
        'author': author_info,  # 添加作者信息
        'status': article.status,
        'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
        'updated_at': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
        'published_at': article.published_at.strftime('%Y-%m-%d %H:%M:%S') if article.published_at else None,
        'tags': article.tags.split(',') if article.tags else [],
        'rumor_reports': rumor_reports,
        'clarification_reports': clarification_reports
    }
    
    return jsonify(article_data), 200, {'Content-Type': 'application/json; charset=utf-8'}

# 前端路由 - 文章列表页面
@debunk_view_bp.route('/articles', methods=['GET'])
def get_articles_view():
    return render_template('debunk/article_list.html')

# 前端路由 - 文章创建页面
@debunk_view_bp.route('/articles/create', methods=['GET'])
def create_article_view():
    return render_template('debunk/article_create.html')

# 前端路由 - 文章详情页面
@debunk_view_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article_detail_view(article_id):
    return render_template('debunk/article_detail.html')

# 前端路由 - 文章编辑页面
@debunk_view_bp.route('/articles/<int:article_id>/edit', methods=['GET'])
def edit_article_view(article_id):
    article = DebunkArticle.query.get_or_404(article_id)
    return render_template('debunk/article_edit.html', article=article)

# 微博辟谣数据相关接口
@debunk_bp.route('/weibo/debunks', methods=['GET'])
def get_weibo_debunks():
    """获取微博辟谣数据列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    search_query = request.args.get('search_query')
    
    query = WeiboDebunk.query
    
    if status:
        query = query.filter(WeiboDebunk.status == status)
    if search_query:
        query = query.filter(WeiboDebunk.search_query == search_query)
        
    pagination = query.order_by(WeiboDebunk.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'items': [item.to_dict() for item in pagination.items]
    })

@debunk_bp.route('/weibo/debunks/<int:id>', methods=['GET'])
def get_weibo_debunk(id):
    """获取单条微博辟谣数据"""
    debunk = WeiboDebunk.query.get_or_404(id)
    return jsonify(debunk.to_dict())

@debunk_bp.route('/weibo/debunks', methods=['POST'])
def create_weibo_debunk():
    """创建微博辟谣数据"""
    data = request.get_json()
    
    # 检查是否已存在相同的微博ID
    if WeiboDebunk.query.filter_by(weibo_mid_id=data.get('weibo_mid_id')).first():
        return jsonify({'error': '该微博已存在'}), 400
        
    try:
        debunk = WeiboDebunk(
            content=data['content'],
            weibo_mid_id=data['weibo_mid_id'],
            weibo_user_id=data['weibo_user_id'],
            weibo_user_name=data['weibo_user_name'],
            user_verified=data.get('user_verified', False),
            user_verified_type=data.get('user_verified_type'),
            user_verified_reason=data.get('user_verified_reason'),
            region=data.get('region'),
            attitudes_count=data.get('attitudes_count', 0),
            comments_count=data.get('comments_count', 0),
            reposts_count=data.get('reposts_count', 0),
            pics=','.join(data['pics']) if data.get('pics') else None,
            created_at=datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S') if isinstance(data.get('created_at'), str) else data.get('created_at'),
            search_query=data.get('search_query'),
            status=data.get('status', 'pending')
        )
        
        db.session.add(debunk)
        db.session.commit()
        return jsonify(debunk.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@debunk_bp.route('/weibo/debunks/<int:id>', methods=['PUT'])
def update_weibo_debunk(id):
    """更新微博辟谣数据"""
    debunk = WeiboDebunk.query.get_or_404(id)
    data = request.get_json()
    
    try:
        for key, value in data.items():
            if key == 'pics' and isinstance(value, list):
                value = ','.join(value)
            elif key == 'created_at' and isinstance(value, str):
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            setattr(debunk, key, value)
            
        db.session.commit()
        return jsonify(debunk.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@debunk_bp.route('/weibo/debunks/<int:id>', methods=['DELETE'])
def delete_weibo_debunk(id):
    """删除微博辟谣数据"""
    debunk = WeiboDebunk.query.get_or_404(id)
    
    try:
        db.session.delete(debunk)
        db.session.commit()
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@debunk_bp.route('/weibo/debunks/batch', methods=['POST'])
def batch_create_weibo_debunks():
    """批量创建微博辟谣数据"""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'error': '请提供数据列表'}), 400
        
    results = []
    for item in data:
        # 检查是否已存在
        if WeiboDebunk.query.filter_by(weibo_mid_id=item.get('weibo_mid_id')).first():
            results.append({
                'weibo_mid_id': item.get('weibo_mid_id'),
                'status': 'skipped',
                'message': '已存在'
            })
            continue
            
        try:
            debunk = WeiboDebunk(
                content=item['content'],
                weibo_mid_id=item['weibo_mid_id'],
                weibo_user_id=item['weibo_user_id'],
                weibo_user_name=item['weibo_user_name'],
                user_verified=item.get('user_verified', False),
                user_verified_type=item.get('user_verified_type'),
                user_verified_reason=item.get('user_verified_reason'),
                region=item.get('region'),
                attitudes_count=item.get('attitudes_count', 0),
                comments_count=item.get('comments_count', 0),
                reposts_count=item.get('reposts_count', 0),
                pics=','.join(item['pics']) if item.get('pics') else None,
                created_at=datetime.strptime(item['created_at'], '%Y-%m-%d %H:%M:%S') if isinstance(item.get('created_at'), str) else item.get('created_at'),
                search_query=item.get('search_query'),
                status=item.get('status', 'pending')
            )
            
            db.session.add(debunk)
            results.append({
                'weibo_mid_id': item.get('weibo_mid_id'),
                'status': 'success'
            })
            
        except Exception as e:
            results.append({
                'weibo_mid_id': item.get('weibo_mid_id'),
                'status': 'error',
                'message': str(e)
            })
            
    try:
        db.session.commit()
        return jsonify(results)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@debunk_bp.route('/user/articles', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['辟谣管理'],
    'summary': '获取当前用户发布的辟谣文章列表',
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
            'name': 'status',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '文章状态筛选，使用"all"获取所有状态'
        },
        {
            'name': 'search',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '搜索关键词'
        },
        {
            'name': 'tags',
            'in': 'query',
            'schema': {'type': 'string'},
            'description': '标签筛选，多个标签用逗号分隔，例如：tags=科技,健康'
        }
    ],
    'responses': {
        200: {
            'description': '获取用户文章列表成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'items': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object'
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
def get_my_articles():
    """获取当前登录用户发布的文章列表"""
    print("##########################################")
    print("# 进入用户文章API - get_my_articles函数 #")
    print("##########################################")
    
    # 打印请求信息
    print("====== 请求详情 ======")
    print(f"请求路径: {request.path}")
    print(f"请求方法: {request.method}")
    print(f"请求查询参数: {dict(request.args)}")
    print(f"请求头:")
    for key, value in request.headers:
        print(f" - {key}: {value if key.lower() != 'authorization' else value[:15] + '...'}")
    
    # 尝试获取JWT身份
    try:
        current_user = get_jwt_identity()
        print(f"JWT身份: {current_user}, 类型: {type(current_user)}")
    except Exception as e:
        print(f"JWT错误: {str(e)}")
        return jsonify({"error": "认证失败", "detail": str(e)}), 401
    
    user_id = None
    
    # 解析用户ID
    if isinstance(current_user, dict):
        user_id = current_user.get('id')
        print(f"从字典中提取用户ID: {user_id}")
    elif isinstance(current_user, str):
        print(f"处理字符串形式的身份: '{current_user}'")
        try:
            # 检查是否被引号包围
            if current_user.startswith('"') and current_user.endswith('"'):
                current_user = current_user[1:-1]
                print(f"去除引号后: '{current_user}'")
            
            # 尝试作为JSON解析
            import json
            try:
                cleaned_str = current_user.replace('\\', '')
                print(f"处理转义后: '{cleaned_str}'")
                user_data = json.loads(cleaned_str)
                print(f"JSON解析结果: {user_data}")
                if isinstance(user_data, dict):
                    user_id = user_data.get('id')
                    print(f"从JSON提取用户ID: {user_id}")
            except json.JSONDecodeError as je:
                print(f"JSON解析失败: {str(je)}")
                # 不是JSON，尝试作为纯数字
                try:
                    user_id = int(current_user)
                    print(f"作为整数解析: {user_id}")
                except ValueError as ve:
                    print(f"整数转换失败: {str(ve)}")
                    return jsonify({"error": "无法识别用户身份", "detail": "无法将身份转换为用户ID"}), 401
        except Exception as e:
            print(f"处理身份时出错: {str(e)}")
            return jsonify({"error": "无法识别用户身份", "detail": str(e)}), 401
    elif isinstance(current_user, int):
        # 直接是数字
        user_id = current_user
        print(f"直接使用整数用户ID: {user_id}")
    else:
        print(f"未知的身份类型: {type(current_user)}")
        return jsonify({"error": "无法识别用户身份", "detail": f"不支持的身份类型: {type(current_user)}"}), 401
    
    if not user_id:
        print(f"未能提取有效的用户ID")
        return jsonify({"error": "无法识别用户身份", "detail": "从身份信息中未找到用户ID"}), 401
    
    # 确认用户存在
    user = User.query.get(user_id)
    if not user:
        print(f"用户ID={user_id}不存在")
        return jsonify({"error": "用户不存在"}), 404
    
    print(f"成功识别用户: ID={user_id}, 用户名={user.user_name}")
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    tags = request.args.get('tags')
    
    # 调试信息：打印收到的所有参数
    print(f"DEBUG - 用户文章请求参数: user_id={user_id}, page={page}, per_page={per_page}, status={status}, search={search}, tags={tags}")
    
    # 构建查询
    query = DebunkArticle.query.filter(DebunkArticle.author_id == user_id)
    
    # 筛选状态
    if status and status.lower() != 'all':
        print(f"DEBUG - 筛选状态: {status}")
        query = query.filter(DebunkArticle.status == status)
    else:
        print(f"DEBUG - 不筛选状态，返回所有状态的文章")
    
    # 标签筛选
    if tags and tags.strip():  # 确保tags参数存在且不为空字符串
        print(f"DEBUG - 启用标签筛选: {tags}")
        tag_list = tags.split(',')
        for tag in tag_list:
            # 对标签进行URL解码
            clean_tag = unquote(tag.strip())
            
            # 跳过空标签
            if not clean_tag:
                continue
                
            print(f"DEBUG - 筛选标签: {clean_tag}")
            
            # 使用更精确的标签匹配方式
            tag_filter = (
                # 精确匹配单个标签（整个标签字段就是这一个标签）
                (DebunkArticle.tags.ilike(clean_tag)) | 
                # 标签在开头，后面跟着逗号
                (DebunkArticle.tags.ilike(f'{clean_tag},%')) |
                # 标签在中间，前后都有逗号
                (DebunkArticle.tags.ilike(f'%,{clean_tag},%')) |
                # 标签在结尾，前面有逗号
                (DebunkArticle.tags.ilike(f'%,{clean_tag}'))
            )
            
            # 检查数据库中是否存在匹配的标签
            tag_check = DebunkArticle.query.filter(DebunkArticle.author_id == user_id).filter(tag_filter).first()
            if tag_check:
                print(f"DEBUG - 找到用户 {user_id} 匹配标签 '{clean_tag}' 的文章，ID: {tag_check.id}, 标签: {tag_check.tags}")
            else:
                print(f"DEBUG - 未找到用户 {user_id} 匹配标签 '{clean_tag}' 的文章")
            
            query = query.filter(tag_filter)
    else:
        print(f"DEBUG - 未启用标签筛选，返回用户 {user_id} 的所有符合条件的文章")
    
    # 搜索功能
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (DebunkArticle.title.ilike(search_term)) | 
            (DebunkArticle.content.ilike(search_term)) |
            (DebunkArticle.summary.ilike(search_term)) |
            (DebunkArticle.tags.ilike(search_term))
        )
    
    # 排序：最新的文章优先
    query = query.order_by(DebunkArticle.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 调试日志：输出找到的文章及其标签
    print(f"DEBUG - 找到用户 {user_id} 的 {pagination.total} 篇文章")
    
    # 构建响应
    articles = []
    for article in pagination.items:
        # 获取文章标签
        article_tags = article.tags.split(',') if article.tags else []
        print(f"DEBUG - 文章ID: {article.id}, 标题: {article.title}, 标签: {article_tags}")
        
        # 获取作者信息
        author_info = None
        if article.author:
            author_info = {
                'id': article.author.id,
                'username': article.author.username if hasattr(article.author, 'username') else '匿名'
            }
            
        articles.append({
            'id': article.id,
            'title': article.title,
            'summary': article.summary,
            'source': article.source,
            'author_id': article.author_id,
            'author': author_info,
            'status': article.status,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
            'updated_at': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None,
            'published_at': article.published_at.strftime('%Y-%m-%d %H:%M:%S') if article.published_at else None,
            'tags': article_tags
        })
    
    return jsonify({
        'data': {
            'items': articles,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page
        }
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@debunk_bp.route('/test/user/articles', methods=['GET'])
def test_get_my_articles():
    """测试用户文章API（无需认证）"""
    print("##########################################")
    print("# 测试路由 - 无需认证 #")
    print("##########################################")
    
    # 打印请求信息
    print("====== 请求详情 ======")
    print(f"请求路径: {request.path}")
    print(f"请求方法: {request.method}")
    print(f"请求查询参数: {dict(request.args)}")
    print(f"请求头:")
    for key, value in request.headers:
        print(f" - {key}: {value}")
    
    # 使用固定的测试用户ID
    user_id = 1
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    tags = request.args.get('tags')
    
    # 构建查询
    query = DebunkArticle.query.filter(DebunkArticle.author_id == user_id)
    
    # 筛选状态
    if status and status.lower() != 'all':
        query = query.filter(DebunkArticle.status == status)
    
    # 排序：最新的文章优先
    query = query.order_by(DebunkArticle.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 调试日志
    print(f"找到用户ID={user_id}的文章数: {pagination.total}")
    
    # 构建响应
    articles = []
    for article in pagination.items:
        article_tags = article.tags.split(',') if article.tags else []
        
        articles.append({
            'id': article.id,
            'title': article.title,
            'summary': article.summary,
            'status': article.status,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else None,
            'tags': article_tags
        })
    
    return jsonify({
        'data': {
            'items': articles,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page
        }
    }), 200, {'Content-Type': 'application/json; charset=utf-8'} 