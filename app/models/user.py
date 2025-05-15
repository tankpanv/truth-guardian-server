import os
import binascii
from hashlib import pbkdf2_hmac
from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    user_name = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # 新增字段
    bio = db.Column(db.String(200))  # 个人签名
    tags = db.Column(db.String(500))  # 用户标签，以逗号分隔存储
    interests = db.Column(db.String(500))  # 用户兴趣，以逗号分隔存储
    avatar_url = db.Column(db.String(255))  # 头像URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 注册时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    # 添加与角色的关联
    roles = db.relationship('UserRole', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        salt = os.urandom(16)
        key = pbkdf2_hmac(
            hash_name='sha256',
            password=password.encode('utf-8'),
            salt=salt,
            iterations=100000,
            dklen=32
        )
        self.password_hash = f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(key).decode()}"

    def check_password(self, password):
        salt, stored_key = self.password_hash.split(':')
        salt = binascii.unhexlify(salt.encode())
        stored_key = binascii.unhexlify(stored_key.encode())
        new_key = pbkdf2_hmac(
            hash_name='sha256',
            password=password.encode('utf-8'),
            salt=salt,
            iterations=100000,
            dklen=32
        )
        return new_key == stored_key
        
    def has_role(self, role_name):
        """检查用户是否拥有指定角色"""
        for user_role in self.roles:
            if user_role.role.name == role_name:
                return True
        return False
    
    # 辅助方法，将字符串转换为列表
    def tags_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def interests_list(self):
        if not self.interests:
            return []
        return [interest.strip() for interest in self.interests.split(',') if interest.strip()]

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与用户角色关联的关系
    user_roles = db.relationship('UserRole', back_populates='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class UserRole(db.Model):
    """用户角色关联模型"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系定义
    user = db.relationship('User', back_populates='roles')
    role = db.relationship('Role', back_populates='user_roles')
    
    def __repr__(self):
        return f'<UserRole {self.user_id}:{self.role_id}>' 