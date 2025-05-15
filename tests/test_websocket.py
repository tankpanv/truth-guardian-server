"""WebSocket 测试脚本

测试 WebSocket 消息推送功能
"""

import os
import sys
import json
import pytest
from flask_socketio import SocketIO
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.message import Message
from datetime import datetime

@pytest.fixture
def app():
    """创建测试应用实例"""
    app = create_app('test')
    
    # 创建测试数据库表
    with app.app_context():
        db.create_all()
        
        # 创建测试用户
        user1 = User(
            username='testuser1',
            name='Test User 1',
            phone='13800138001'
        )
        user1.set_password('password123')
        
        user2 = User(
            username='testuser2',
            name='Test User 2',
            phone='13800138002'
        )
        user2.set_password('password123')
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
    yield app
    
    # 清理测试数据库
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def socket_client(app, client):
    """创建 WebSocket 测试客户端"""
    flask_test_client = app.test_client()
    
    # 登录获取token
    response = flask_test_client.post('/api/auth/login', json={
        'username': 'testuser1',
        'password': 'password123'
    })
    token = json.loads(response.data)['access_token']
    
    # 创建 SocketIO 客户端
    socket_client = SocketIO(app, logger=True, engineio_logger=True)
    
    return socket_client, token

def test_websocket_connection(socket_client):
    """测试 WebSocket 连接"""
    client, token = socket_client
    
    connected = [False]
    received = []
    
    @client.on('connect')
    def on_connect():
        connected[0] = True
        
    @client.on('new_message')
    def on_message(data):
        received.append(data)
        
    # 连接 WebSocket
    client.connect(
        'http://localhost:5005',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert connected[0] is True
    
    # 发送测试消息
    with app.app_context():
        message = Message(
            sender_id=1,
            receiver_id=2,
            title='Test Message',
            msg_type='text',
            content='Hello WebSocket!',
            priority=0,
            send_time=datetime.now()
        )
        db.session.add(message)
        db.session.commit()
        
        # 推送消息
        from app.websockets.message_handler import push_message
        push_message(2, message.to_dict())
        
    # 等待接收消息
    client.sleep(1)
    
    assert len(received) == 1
    assert received[0]['content'] == 'Hello WebSocket!'
    
    client.disconnect() 