from datetime import datetime
from app import db

class ReadingHistory(db.Model):
    """用户阅读历史记录模型"""
    __tablename__ = 'reading_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('wx_users.id'), nullable=False)
    article_id = db.Column(db.Integer, nullable=False)
    article_type = db.Column(db.String(20), nullable=False)  # 'debunk'辟谣文章, 'news'新闻等
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_duration = db.Column(db.Integer, default=0)  # 阅读时长(秒)
    is_completed = db.Column(db.Boolean, default=False)  # 是否阅读完成
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'article_id': self.article_id, 
            'article_type': self.article_type,
            'read_at': self.read_at.isoformat(),
            'read_duration': self.read_duration,
            'is_completed': self.is_completed
        } 