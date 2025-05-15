"""新闻数据模型

用于存储从各种渠道采集的新闻、谣言和社交媒体数据
"""

from datetime import datetime
from app import db
from sqlalchemy.dialects.mysql import JSON

class NewsData(db.Model):
    """新闻数据模型"""
    
    __tablename__ = 'news_data'
    
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.String(64), unique=True, index=True, comment='新闻唯一ID')
    title = db.Column(db.String(255), nullable=False, comment='新闻标题')
    content = db.Column(db.Text, nullable=False, comment='新闻内容')
    summary = db.Column(db.Text, comment='新闻摘要')
    source = db.Column(db.String(100), comment='新闻来源')
    url = db.Column(db.String(512), comment='原始URL')
    pub_date = db.Column(db.DateTime, comment='发布时间')
    crawl_time = db.Column(db.DateTime, default=datetime.now, comment='采集时间')
    author = db.Column(db.String(100), comment='作者/发布者')
    category = db.Column(db.String(50), comment='分类/栏目')
    tags = db.Column(JSON, comment='标签列表')
    media = db.Column(JSON, comment='相关媒体')
    source_type = db.Column(db.String(20), comment='数据来源类型')
    recommendation_level = db.Column(db.Integer, default=0, comment='推荐级别')
    keyword_match = db.Column(db.Float, default=0.0, comment='关键词匹配度')
    processed = db.Column(db.Boolean, default=False, comment='是否已处理')
    processed_time = db.Column(db.DateTime, comment='处理时间')
    
    def __repr__(self):
        return f'<NewsData {self.title}>'

class RumorData(db.Model):
    """谣言数据模型"""
    
    __tablename__ = 'rumor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    rumor_id = db.Column(db.String(64), unique=True, index=True, comment='谣言唯一ID')
    title = db.Column(db.String(255), nullable=False, comment='谣言标题')
    content = db.Column(db.Text, nullable=False, comment='谣言内容')
    source = db.Column(db.String(100), comment='谣言来源')
    refutation = db.Column(db.Text, comment='辟谣内容')
    refutation_source = db.Column(db.String(100), comment='辟谣来源')
    url = db.Column(db.String(512), comment='原始URL')
    pub_date = db.Column(db.DateTime, comment='发布时间')
    crawl_time = db.Column(db.DateTime, default=datetime.now, comment='采集时间')
    category = db.Column(db.String(50), comment='谣言类型/分类')
    spread_level = db.Column(db.Integer, default=1, comment='传播范围评估')
    harm_level = db.Column(db.Integer, default=1, comment='危害程度评估')
    tags = db.Column(JSON, comment='标签列表')
    media = db.Column(JSON, comment='相关媒体')
    source_type = db.Column(db.String(20), comment='数据来源类型')
    processed = db.Column(db.Boolean, default=False, comment='是否已处理')
    processed_time = db.Column(db.DateTime, comment='处理时间')
    
    def __repr__(self):
        return f'<RumorData {self.title}>'

class SocialMediaData(db.Model):
    """社交媒体数据模型"""
    
    __tablename__ = 'social_media_data'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(64), unique=True, index=True, comment='帖子唯一ID')
    platform = db.Column(db.String(20), nullable=False, comment='平台')
    content = db.Column(db.Text, nullable=False, comment='内容')
    user_id = db.Column(db.String(64), comment='发布者ID')
    username = db.Column(db.String(100), comment='发布者名称')
    verified_type = db.Column(db.String(20), comment='认证类型')
    pub_date = db.Column(db.DateTime, comment='发布时间')
    crawl_time = db.Column(db.DateTime, default=datetime.now, comment='采集时间')
    url = db.Column(db.String(512), comment='原始URL')
    shares = db.Column(db.Integer, default=0, comment='转发/分享数')
    comments = db.Column(db.Integer, default=0, comment='评论数')
    likes = db.Column(db.Integer, default=0, comment='点赞数')
    media = db.Column(JSON, comment='相关媒体')
    tags = db.Column(JSON, comment='标签列表')
    topics = db.Column(JSON, comment='话题/话题标签')
    location = db.Column(db.String(100), comment='地理位置')
    content_type = db.Column(db.String(20), default='original', comment='内容类型')
    recommendation_level = db.Column(db.Integer, default=0, comment='推荐级别')
    keyword_match = db.Column(db.Float, default=0.0, comment='关键词匹配度')
    processed = db.Column(db.Boolean, default=False, comment='是否已处理')
    processed_time = db.Column(db.DateTime, comment='处理时间')
    
    def __repr__(self):
        return f'<SocialMediaData {self.platform}:{self.post_id}>'

class DataProcessLog(db.Model):
    """数据处理日志"""
    
    __tablename__ = 'data_process_log'
    
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(20), nullable=False, comment='数据类型')
    data_id = db.Column(db.Integer, nullable=False, comment='数据ID')
    process_type = db.Column(db.String(50), nullable=False, comment='处理类型')
    status = db.Column(db.String(20), nullable=False, comment='处理状态')
    message = db.Column(db.Text, comment='处理消息')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<DataProcessLog {self.process_type}:{self.data_id}>' 