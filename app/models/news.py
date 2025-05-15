"""新闻模型

定义新闻数据的数据库模型
"""

from datetime import datetime
from app.extensions import db

class News(db.Model):
    """新闻模型类"""
    
    __tablename__ = 'news'
    
    # 主键
    id = db.Column(db.String(32), primary_key=True)
    
    # 新闻URL
    url = db.Column(db.String(512), unique=True, nullable=False, index=True)
    
    # 新闻标题
    title = db.Column(db.String(256), nullable=False, index=True)
    
    # 新闻内容
    content = db.Column(db.Text, nullable=False)
    
    # 新闻摘要
    summary = db.Column(db.String(512))
    
    # 发布日期
    publish_date = db.Column(db.DateTime, index=True)
    
    # 作者
    author = db.Column(db.String(64), index=True)
    
    # 分类
    category = db.Column(db.String(64), index=True)
    
    # 标签，JSON格式存储
    tags = db.Column(db.JSON)
    
    # 来源网站
    source = db.Column(db.String(64), index=True)
    
    # 来源类型(news/weibo/gov等)
    source_type = db.Column(db.String(32), nullable=False, index=True)
    
    # 媒体文件，JSON格式存储
    media = db.Column(db.JSON)
    
    # 关键词匹配度
    keyword_match = db.Column(db.Float, default=0)
    
    # 推荐级别
    recommendation_level = db.Column(db.Integer, default=0)
    
    # 爬取时间
    crawl_time = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 更新时间
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        """返回模型的字符串表示"""
        return f'<News {self.title}>' 