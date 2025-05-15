"""IM消息推送路由

处理IM消息的推送、查询等功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.message import Message
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.websockets.message_handler import push_message
import logging
import json

logger = logging.getLogger('app.im')

# 创建蓝图
im_bp = Blueprint('im', __name__)

@im_bp.route('/push', methods=['POST'])
@jwt_required()
def push_im_message():
    """推送IM消息
    
    请求体格式:
    {
        "receiver_id": "用户ID",
        "title": "消息标题",
        "msg_type": "消息类型", // text/image/file
        "content": "消息内容",
        "priority": 0,  // 优先级 0-普通 1-重要 2-紧急
        "expire_time": "2024-03-20 12:00:00" // 可选,消息过期时间
    }
    
    返回:
    {
        "success": true,
        "message": "消息推送成功",
        "data": {
            "msg_id": "消息ID",
            "send_time": "发送时间"
        }
    }
    """
    try:
        data = request.get_json()
        # 添加请求数据的调试日志
        logger.info(f"收到的请求数据: {data}")
        
        # 获取并解析用户身份
        identity = get_jwt_identity()
        user_id = None
        
        # 处理不同格式的身份信息
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
        
        # 验证必填字段
        required_fields = ['receiver_id', 'title', 'msg_type', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 验证标题长度
        if len(data['title']) > 100:
            return jsonify({
                'success': False,
                'message': '标题长度不能超过100个字符'
            }), 400
            
        # 验证消息类型
        valid_types = ['text', 'image', 'file']
        if data['msg_type'] not in valid_types:
            return jsonify({
                'success': False,
                'message': f'无效的消息类型,支持的类型: {",".join(valid_types)}'
            }), 400
            
        # 验证优先级
        priority = data.get('priority', 0)
        if priority not in [0, 1, 2]:
            return jsonify({
                'success': False,
                'message': '无效的优先级,支持的值: 0(普通),1(重要),2(紧急)'
            }), 400
            
        # 处理过期时间
        expire_time = None
        if 'expire_time' in data:
            try:
                # 记录原始过期时间字符串
                logger.info(f"原始过期时间字符串: {data['expire_time']}")
                # 解析过期时间
                expire_time = datetime.strptime(data['expire_time'], '%Y-%m-%d %H:%M:%S')
                current_time = datetime.now()
                
                # 添加调试日志
                logger.info(f"当前时间: {current_time}")
                logger.info(f"解析后的过期时间: {expire_time}")
                
                # 比较时间
                if expire_time <= current_time:
                    logger.warning(f"过期时间验证失败: {expire_time} <= {current_time}")
                    return jsonify({
                        'success': False,
                        'message': '过期时间不能早于当前时间'
                    }), 400
                    
            except ValueError as e:
                logger.error(f"时间解析错误: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': '无效的过期时间格式,正确格式: YYYY-MM-DD HH:MM:SS'
                }), 400
        
        # 创建消息记录
        message = Message(
            sender_id=user_id,
            receiver_id=data['receiver_id'],
            title=data['title'],
            msg_type=data['msg_type'],
            content=data['content'],
            priority=priority,
            expire_time=expire_time,
            send_time=datetime.now()
        )
        
        # 保存到数据库
        db.session.add(message)
        db.session.commit()
        
        # 通过 WebSocket 推送消息
        message_data = message.to_dict()
        push_message(data['receiver_id'], message_data)
        
        logger.info(f"消息推送成功: {message.id}")
        
        return jsonify({
            'success': True,
            'message': '消息推送成功',
            'data': {
                'msg_id': message.id,
                'send_time': message.send_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"消息推送失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'消息推送失败: {str(e)}'
        }), 500

@im_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """获取消息列表
    
    查询参数:
    - direction: 消息方向 (received-收到的消息[默认], sent-发送的消息, all-全部消息)
    - unread_only: 是否只获取未读消息 (1/0)
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    - priority: 优先级过滤 (可选, 0/1/2)
    - msg_type: 消息类型过滤 (可选, text/image/file)
    
    返回:
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "messages": [
                {
                    "id": 消息ID,
                    "sender_id": 发送者ID,
                    "msg_type": "消息类型",
                    "content": "消息内容",
                    "priority": 优先级,
                    "send_time": "发送时间",
                    "expire_time": "过期时间",
                    "is_read": 是否已读
                }
            ],
            "total": 总消息数,
            "page": 当前页码,
            "per_page": 每页数量,
            "total_pages": 总页数
        }
    }
    """
    try:
        # 获取并解析用户身份
        identity = get_jwt_identity()
        user_id = None
        
        # 处理不同格式的身份信息
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        # 获取查询参数
        direction = request.args.get('direction', 'received')  # 默认获取收到的消息
        unread_only = request.args.get('unread_only', '0') == '1'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # 限制最大每页数量
        priority = request.args.get('priority', type=int)
        msg_type = request.args.get('msg_type')
        
        # 构建基础查询
        query = Message.query
        
        # 根据消息方向过滤
        if direction == 'received':
            query = query.filter_by(receiver_id=user_id)
        elif direction == 'sent':
            query = query.filter_by(sender_id=user_id)
        else:  # all
            query = query.filter((Message.receiver_id == user_id) | (Message.sender_id == user_id))
        
        # 应用其他过滤条件
        if unread_only:
            query = query.filter_by(is_read=False)
        if priority is not None:
            query = query.filter_by(priority=priority)
        if msg_type:
            query = query.filter_by(msg_type=msg_type)
            
        # 过滤掉已过期的消息
        query = query.filter(
            (Message.expire_time.is_(None)) | 
            (Message.expire_time > datetime.now())
        )
        
        # 添加调试日志
        logger.info(f"查询参数: direction={direction}, unread_only={unread_only}, user_id={user_id}")
        
        # 按优先级和时间排序
        query = query.order_by(Message.priority.desc(), Message.send_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'messages': [msg.to_dict() for msg in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取消息列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取消息列表失败: {str(e)}'
        }), 500

@im_bp.route('/messages/read', methods=['POST'])
@jwt_required()
def mark_messages_read():
    """标记消息为已读
    
    请求体格式:
    {
        "message_ids": [消息ID列表]  // 如果为空，则标记所有未读消息
    }
    
    返回:
    {
        "success": true,
        "message": "标记成功",
        "data": {
            "updated_count": 更新的消息数量
        }
    }
    """
    try:
        # 获取并解析用户身份
        identity = get_jwt_identity()
        user_id = None
        
        # 处理不同格式的身份信息
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        data = request.get_json()
        message_ids = data.get('message_ids', [])
        
        # 添加调试日志
        logger.info(f"标记消息已读: user_id={user_id}, message_ids={message_ids}")
        
        # 构建查询
        query = Message.query.filter_by(
            receiver_id=user_id,
            is_read=False
        )
        
        # 如果指定了消息ID，则只更新这些消息
        if message_ids:
            query = query.filter(Message.id.in_(message_ids))
            
        # 更新消息状态
        current_time = datetime.now()
        updated_count = query.update({
            'is_read': True,
            'read_time': current_time
        }, synchronize_session=False)
        
        db.session.commit()
        
        logger.info(f"已标记 {updated_count} 条消息为已读")
        
        return jsonify({
            'success': True,
            'message': '标记成功',
            'data': {
                'updated_count': updated_count
            }
        })
        
    except Exception as e:
        logger.error(f"标记消息已读失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'标记消息已读失败: {str(e)}'
        }), 500

@im_bp.route('/messages/history', methods=['GET'])
@jwt_required()
def get_history_messages():
    """获取历史消息
    
    查询参数:
    - start_time: 开始时间 (YYYY-MM-DD HH:MM:SS)
    - end_time: 结束时间 (YYYY-MM-DD HH:MM:SS)
    - direction: 消息方向 (received/sent/all)
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    - msg_type: 消息类型过滤 (可选)
    - priority: 优先级过滤 (可选)
    
    返回:
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "messages": [消息列表],
            "total": 总数,
            "page": 当前页,
            "per_page": 每页数量,
            "total_pages": 总页数
        }
    }
    """
    try:
        # 获取用户ID
        identity = get_jwt_identity()
        user_id = None
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        direction = request.args.get('direction', 'all')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        msg_type = request.args.get('msg_type')
        priority = request.args.get('priority', type=int)
        
        # 构建查询
        query = Message.query
        
        # 时间过滤
        if start_time:
            try:
                start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Message.send_time >= start_datetime)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '无效的开始时间格式'
                }), 400
                
        if end_time:
            try:
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Message.send_time <= end_datetime)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '无效的结束时间格式'
                }), 400
        
        # 方向过滤
        if direction == 'received':
            query = query.filter_by(receiver_id=user_id)
        elif direction == 'sent':
            query = query.filter_by(sender_id=user_id)
        else:  # all
            query = query.filter((Message.receiver_id == user_id) | (Message.sender_id == user_id))
            
        # 类型和优先级过滤
        if msg_type:
            query = query.filter_by(msg_type=msg_type)
        if priority is not None:
            query = query.filter_by(priority=priority)
            
        # 排序
        query = query.order_by(Message.send_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'messages': [msg.to_dict() for msg in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史消息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取历史消息失败: {str(e)}'
        }), 500

@im_bp.route('/messages/<int:message_id>', methods=['GET'])
@jwt_required()
def get_message_detail(message_id):
    """获取消息详情
    
    参数:
    - message_id: 消息ID
    
    返回:
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "message": 消息详情
        }
    }
    """
    try:
        # 获取用户ID
        identity = get_jwt_identity()
        user_id = None
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        # 获取消息
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({
                'success': False,
                'message': '消息不存在'
            }), 404
            
        # 验证权限
        if message.sender_id != user_id and message.receiver_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权访问此消息'
            }), 403
            
        # 如果是接收者查看，自动标记为已读
        if message.receiver_id == user_id and not message.is_read:
            message.is_read = True
            message.read_time = datetime.now()
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'message': message.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"获取消息详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取消息详情失败: {str(e)}'
        }), 500

@im_bp.route('/messages/sync-read-status', methods=['POST'])
@jwt_required()
def sync_read_status():
    """同步消息已读状态
    
    请求体格式:
    {
        "message_ids": [消息ID列表],
        "is_read": true/false
    }
    
    返回:
    {
        "success": true,
        "message": "同步成功",
        "data": {
            "updated_count": 更新数量
        }
    }
    """
    try:
        # 获取用户ID
        identity = get_jwt_identity()
        user_id = None
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        data = request.get_json()
        if not data or 'message_ids' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要的参数'
            }), 400
            
        message_ids = data['message_ids']
        is_read = data.get('is_read', True)
        
        # 更新消息状态
        query = Message.query.filter(
            Message.id.in_(message_ids),
            Message.receiver_id == user_id
        )
        
        current_time = datetime.now() if is_read else None
        updated_count = query.update({
            'is_read': is_read,
            'read_time': current_time
        }, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '同步成功',
            'data': {
                'updated_count': updated_count
            }
        })
        
    except Exception as e:
        logger.error(f"同步已读状态失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'同步已读状态失败: {str(e)}'
        }), 500

@im_bp.route('/messages/search', methods=['GET'])
@jwt_required()
def search_messages():
    """搜索消息
    
    查询参数:
    - keyword: 搜索关键词（匹配标题和内容）
    - msg_type: 消息类型过滤 (可选, text/image/file)
    - priority: 优先级过滤 (可选, 0/1/2)
    - direction: 消息方向 (received-收到的消息[默认], sent-发送的消息, all-全部消息)
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    
    返回:
    {
        "success": true,
        "message": "搜索成功",
        "data": {
            "messages": [
                {
                    "id": 消息ID,
                    "sender_id": 发送者ID,
                    "title": "消息标题",
                    "content": "消息内容",
                    "msg_type": "消息类型",
                    "priority": 优先级,
                    "send_time": "发送时间",
                    "expire_time": "过期时间",
                    "is_read": 是否已读
                }
            ],
            "total": 总消息数,
            "page": 当前页码,
            "per_page": 每页数量,
            "total_pages": 总页数
        }
    }
    """
    try:
        # 获取并解析用户身份
        identity = get_jwt_identity()
        user_id = None
        
        # 处理不同格式的身份信息
        if isinstance(identity, dict):
            user_id = identity.get('id')
        elif isinstance(identity, str):
            try:
                user_info = json.loads(identity)
                user_id = user_info.get('id')
            except json.JSONDecodeError:
                try:
                    user_id = int(identity)
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'message': '无效的用户身份信息'
                    }), 401
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 401
            
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        msg_type = request.args.get('msg_type')
        priority = request.args.get('priority', type=int)
        direction = request.args.get('direction', 'received')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # 限制最大每页数量
        
        # 构建基础查询
        query = Message.query
        
        # 关键词搜索
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                (Message.title.ilike(search_term)) | 
                (Message.content.ilike(search_term))
            )
        
        # 根据消息方向过滤
        if direction == 'received':
            query = query.filter_by(receiver_id=user_id)
        elif direction == 'sent':
            query = query.filter_by(sender_id=user_id)
        else:  # all
            query = query.filter((Message.receiver_id == user_id) | (Message.sender_id == user_id))
        
        # 应用其他过滤条件
        if msg_type:
            query = query.filter_by(msg_type=msg_type)
        if priority is not None:
            query = query.filter_by(priority=priority)
            
        # 过滤掉已过期的消息
        query = query.filter(
            (Message.expire_time.is_(None)) | 
            (Message.expire_time > datetime.now())
        )
        
        # 按优先级和时间排序
        query = query.order_by(Message.priority.desc(), Message.send_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'message': '搜索成功',
            'data': {
                'messages': [msg.to_dict() for msg in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"搜索消息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索消息失败: {str(e)}'
        }), 500 