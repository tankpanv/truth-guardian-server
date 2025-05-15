from flask import Blueprint, request, jsonify
from app.models.debunk import WeiboDebunk, XinlangDebunk, DebunkContent
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from datetime import datetime

spider_bp = Blueprint('spider', __name__, url_prefix='/api/spider')

# 创建一个不带参数的jwt_required实例
jwt_required_without_optional = jwt_required()

@spider_bp.route('/data', methods=['GET'])
@jwt_required_without_optional
def get_spider_data():
    """获取爬虫数据列表
    
    Query参数:
    - source: 数据来源 (weibo/xinlang/all)
    - status: 状态过滤 (pending/verified/false)
    - keyword: 搜索关键词
    - page: 页码
    - per_page: 每页数量
    """
    source = request.args.get('source', 'all')
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    
    # 构建基础查询
    query = DebunkContent.query
    
    # 应用过滤条件
    if source != 'all':
        query = query.filter(DebunkContent.source == source)
    if status:
        query = query.filter(DebunkContent.status == status)
    if keyword:
        query = query.filter(or_(
            DebunkContent.title.ilike(f'%{keyword}%'),
            DebunkContent.content.ilike(f'%{keyword}%'),
            DebunkContent.author_name.ilike(f'%{keyword}%')
        ))
    
    # 获取分页数据
    pagination = query.order_by(DebunkContent.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }
    })

@spider_bp.route('/data/<int:data_id>', methods=['GET'])
@jwt_required_without_optional
def get_spider_data_detail(data_id):
    """获取爬虫数据详情"""
    data = DebunkContent.query.get_or_404(data_id)
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': data.to_dict()
    })

@spider_bp.route('/data/<int:data_id>', methods=['PUT'])
@jwt_required_without_optional
def update_spider_data(data_id):
    """更新爬虫数据
    
    请求体参数:
    - status: 状态 (pending/verified/false)
    - title: 标题
    - content: 内容
    """
    data = DebunkContent.query.get_or_404(data_id)
    
    # 获取请求数据
    update_data = request.get_json()
    
    # 更新允许的字段
    allowed_fields = ['status', 'title', 'content']
    for field in allowed_fields:
        if field in update_data:
            setattr(data, field, update_data[field])
    
    # 同步更新原始数据
    if data.source == 'weibo':
        original = WeiboDebunk.query.filter_by(weibo_mid_id=data.content_id).first()
        if original and 'status' in update_data:
            original.status = update_data['status']
    elif data.source == 'xinlang':
        original = XinlangDebunk.query.filter_by(news_id=data.content_id).first()
        if original and 'status' in update_data:
            original.status = update_data['status']
    
    try:
        db.session.commit()
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': data.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@spider_bp.route('/data/<int:data_id>', methods=['DELETE'])
@jwt_required_without_optional
def delete_spider_data(data_id):
    """删除爬虫数据"""
    data = DebunkContent.query.get_or_404(data_id)
    
    try:
        # 同时删除原始数据
        if data.source == 'weibo':
            original = WeiboDebunk.query.filter_by(weibo_mid_id=data.content_id).first()
            if original:
                db.session.delete(original)
        elif data.source == 'xinlang':
            original = XinlangDebunk.query.filter_by(news_id=data.content_id).first()
            if original:
                db.session.delete(original)
        
        db.session.delete(data)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@spider_bp.route('/stats', methods=['GET'])
@jwt_required_without_optional
def get_spider_stats():
    """获取爬虫数据统计信息"""
    try:
        # 获取各来源的数据统计
        weibo_stats = db.session.query(
            WeiboDebunk.status,
            db.func.count(WeiboDebunk.id)
        ).group_by(WeiboDebunk.status).all()
        
        xinlang_stats = db.session.query(
            XinlangDebunk.status,
            db.func.count(XinlangDebunk.id)
        ).group_by(XinlangDebunk.status).all()
        
        # 格式化统计结果
        stats = {
            'weibo': {status: count for status, count in weibo_stats},
            'xinlang': {status: count for status, count in xinlang_stats},
            'total': {
                'weibo': sum(count for _, count in weibo_stats),
                'xinlang': sum(count for _, count in xinlang_stats)
            }
        }
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@spider_bp.route('/batch/status', methods=['PUT'])
@jwt_required_without_optional
def batch_update_status():
    """批量更新数据状态
    
    请求体参数:
    - ids: 数据ID列表
    - status: 新状态 (pending/verified/false)
    """
    data = request.get_json()
    if not data or 'ids' not in data or 'status' not in data:
        return jsonify({
            'code': 1,
            'message': '缺少必要的参数'
        }), 400
    
    try:
        # 更新DebunkContent表
        DebunkContent.query.filter(
            DebunkContent.id.in_(data['ids'])
        ).update({
            'status': data['status']
        }, synchronize_session=False)
        
        # 获取受影响的content_ids
        affected_contents = DebunkContent.query.filter(
            DebunkContent.id.in_(data['ids'])
        ).with_entities(DebunkContent.source, DebunkContent.content_id).all()
        
        # 更新原始数据表
        for source, content_id in affected_contents:
            if source == 'weibo':
                WeiboDebunk.query.filter_by(
                    weibo_mid_id=content_id
                ).update({
                    'status': data['status']
                }, synchronize_session=False)
            elif source == 'xinlang':
                XinlangDebunk.query.filter_by(
                    news_id=content_id
                ).update({
                    'status': data['status']
                }, synchronize_session=False)
        
        db.session.commit()
        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@spider_bp.route('/data', methods=['POST'])
@jwt_required_without_optional
def create_spider_data():
    """新增爬虫数据
    
    请求体参数:
    - source: 数据来源 (weibo/xinlang)
    - data: 数据内容
    
    微博数据结构:
    {
        "source": "weibo",
        "data": {
            "content": "微博内容",
            "weibo_mid_id": "微博ID",
            "weibo_user_id": "用户ID",
            "weibo_user_name": "用户名",
            "user_verified": false,
            "user_verified_type": 0,
            "user_verified_reason": "认证原因",
            "region": "地区",
            "attitudes_count": 0,
            "comments_count": 0,
            "reposts_count": 0,
            "pics": "图片URL1,图片URL2",
            "created_at": "2024-01-01 12:00:00",
            "search_query": "搜索关键词",
            "status": "pending"
        }
    }
    
    新浪数据结构:
    {
        "source": "xinlang",
        "data": {
            "news_id": "新闻ID",
            "data_id": "数据ID",
            "title": "新闻标题",
            "source_name": "来源名称",
            "link": "文章链接",
            "image_url": "图片链接",
            "category": "分类",
            "comment_id": "评论ID",
            "publish_time": "发布时间",
            "search_query": "搜索关键词",
            "status": "pending"
        }
    }
    """
    data = request.get_json()
    if not data or 'source' not in data or 'data' not in data:
        return jsonify({
            'code': 1,
            'message': '缺少必要的参数'
        }), 400
        
    source = data['source']
    content_data = data['data']
    
    try:
        if source == 'weibo':
            # 处理created_at字段
            if 'created_at' in content_data:
                try:
                    content_data['created_at'] = datetime.strptime(
                        content_data['created_at'],
                        '%Y-%m-%d %H:%M:%S'
                    )
                except:
                    content_data['created_at'] = datetime.now()
            
            # 检查是否已存在
            existing = WeiboDebunk.query.filter_by(
                weibo_mid_id=content_data.get('weibo_mid_id')
            ).first()
            if existing:
                return jsonify({
                    'code': 1,
                    'message': '该微博已存在'
                }), 400
            
            # 创建新的微博记录
            weibo = WeiboDebunk(**content_data)
            db.session.add(weibo)
            db.session.flush()  # 获取ID
            
            # 转换并保存到DebunkContent
            debunk_content = weibo.to_debunk_content()
            db.session.add(debunk_content)
            
            db.session.commit()
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': weibo.to_dict()
            })
            
        elif source == 'xinlang':
            # 检查是否已存在
            existing = XinlangDebunk.query.filter_by(
                news_id=content_data.get('news_id')
            ).first()
            if existing:
                return jsonify({
                    'code': 1,
                    'message': '该新闻已存在'
                }), 400
            
            # 创建新的新浪新闻记录
            news = XinlangDebunk(**content_data)
            db.session.add(news)
            db.session.flush()  # 获取ID
            
            # 转换并保存到DebunkContent
            debunk_content = news.to_debunk_content()
            db.session.add(debunk_content)
            
            db.session.commit()
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': news.to_dict()
            })
            
        else:
            # 处理其他来源的数据（如辟谣网站）
            title = data.get('data', {}).get('title')
            
            if not title:
                return jsonify({
                    'code': 1,
                    'message': '标题不能为空'
                }), 400
            
            # 检查是否已存在
            existing_content = DebunkContent.query.filter_by(
                source=source,
                title=title
            ).first()
            
            data = data.get('data', {})
            if not data:
                return jsonify({
                    'code': 1,
                    'message': '数据不能为空'
                }), 400
                
            title = data.get('title')
            content = data.get('content')
            if not content:
                return jsonify({
                    'code': 1,
                    'message': '内容不能为空'
                }), 400
                
            if existing_content:
                # 更新已存在的记录
                existing_content.content = content
                existing_content.updated_at = datetime.now()
                existing_content.status = 'published'
                db.session.commit()
                
                return jsonify({
                    'code': 0,
                    'message': '更新成功',
                    'data': {
                        'id': existing_content.id
                    }
                })
            else:
                # 创建新的辟谣内容
                debunk_content = DebunkContent(
                    source=source,
                    title=title,
                    content=content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    status='published'
                )
                
                db.session.add(debunk_content)
                db.session.commit()
                
                return jsonify({
                    'code': 0,
                    'message': '保存成功',
                    'data': {
                        'id': debunk_content.id
                    }
                })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500 