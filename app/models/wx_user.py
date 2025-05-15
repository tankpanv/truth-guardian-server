from datetime import datetime
from app import db
from sqlalchemy.types import JSON

class WxUser(db.Model):
    """微信小程序用户模型"""
    __tablename__ = 'wx_users'
    
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    unionid = db.Column(db.String(64), unique=True, nullable=True)
    session_key = db.Column(db.String(128), nullable=True)
    
    # 用户基本信息
    nickname = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    gender = db.Column(db.SmallInteger, default=0)  # 0:未知, 1:男, 2:女
    country = db.Column(db.String(64), nullable=True)
    province = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    
    # 额外信息
    phone = db.Column(db.String(32), nullable=True)
    extra_data = db.Column(JSON, nullable=True)
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联的阅读历史记录
    reading_histories = db.relationship('ReadingHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'openid': self.openid,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'gender': self.gender,
            'country': self.country,
            'province': self.province,
            'city': self.city,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat()
        }
    
    def update_login_time(self):
        """更新登录时间"""
        self.last_login = datetime.utcnow()
        db.session.commit() 