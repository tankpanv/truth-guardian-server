"""WebSocket 模块初始化

处理实时消息推送的 WebSocket 连接
"""

from flask_socketio import SocketIO

# 创建 SocketIO 实例
socketio = SocketIO(cors_allowed_origins="*")

def init_websocket(app):
    """初始化 WebSocket
    
    Args:
        app: Flask 应用实例
    """
    socketio.init_app(app) 