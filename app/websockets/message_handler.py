"""WebSocket 消息处理器

处理实时消息的 WebSocket 事件
"""

from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from . import socketio
import logging
import json

logger = logging.getLogger('app.websocket')

@socketio.on('connect')
@jwt_required()
def handle_connect():
    """处理客户端连接"""
    try:
        # 获取用户ID
        identity = get_jwt_identity()
        logger.info(f'WebSocket连接 - 原始身份信息: {identity}')
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
                    logger.error('无效的用户身份信息')
                    return False
        
        if user_id is None:
            logger.error('无法获取用户ID')
            return False
            
        # 将用户加入以用户ID命名的房间
        room = str(user_id)
        join_room(room)
        logger.info(f'用户 {user_id} 已连接并加入房间 {room}')
        
        # 发送连接成功消息
        emit('connect_response', {
            'success': True,
            'message': '连接成功',
            'user_id': user_id
        })
        return True
        
    except Exception as e:
        logger.error(f'处理连接时出错: {str(e)}')
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    try:
        # 尝试验证 JWT，如果失败则直接返回
        try:
            verify_jwt_in_request()
        except Exception as e:
            logger.info('用户断开连接 (无token或token已过期)')
            return
            
        identity = get_jwt_identity()
        logger.info(f'WebSocket断开 - 原始身份信息: {identity}')
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
                    logger.error('无效的用户身份信息')
                    return
        
        if user_id:
            room = str(user_id)
            leave_room(room)
            logger.info(f'用户 {user_id} 已断开连接并离开房间 {room}')
            
    except Exception as e:
        logger.error(f'处理断开连接时出错: {str(e)}')

def push_message(user_id, message):
    """推送消息到指定用户
    
    Args:
        user_id: 目标用户ID
        message: 消息内容字典
    """
    try:
        room = str(user_id)
        logger.info(f'尝试向房间 {room} 推送消息: {message}')
        socketio.emit('new_message', message, room=room, namespace='/')
        logger.info(f'消息已成功推送到用户 {user_id} (房间 {room})')
        return True
    except Exception as e:
        logger.error(f'推送消息时出错: {str(e)}')
        return False 