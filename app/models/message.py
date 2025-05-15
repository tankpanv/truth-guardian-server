"""消息模型

定义IM消息的数据结构
"""

from app.extensions import db
from datetime import datetime

class Message(db.Model):
    """消息模型类"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False, comment='发送者ID')
    receiver_id = db.Column(db.Integer, nullable=False, comment='接收者ID')
    title = db.Column(db.String(100), nullable=False, comment='消息标题')
    msg_type = db.Column(db.String(10), nullable=False, comment='消息类型:text/image/file')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    priority = db.Column(db.Integer, default=0, comment='优先级:0-普通,1-重要,2-紧急')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    send_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='发送时间')
    read_time = db.Column(db.DateTime, comment='阅读时间')
    expire_time = db.Column(db.DateTime, comment='过期时间')
    
    def __repr__(self):
        return f'<Message {self.id}>'
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'title': self.title,
            'msg_type': self.msg_type,
            'content': self.content,
            'priority': self.priority,
            'is_read': self.is_read,
            'send_time': self.send_time.strftime('%Y-%m-%d %H:%M:%S'),
            'read_time': self.read_time.strftime('%Y-%m-%d %H:%M:%S') if self.read_time else None,
            'expire_time': self.expire_time.strftime('%Y-%m-%d %H:%M:%S') if self.expire_time else None
        } 