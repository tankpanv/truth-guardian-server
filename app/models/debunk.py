from app import db
from datetime import datetime
from app.models.user import User
import json

# 辟谣文章和谣言报道的关联表
article_rumor_association = db.Table('article_rumor_association',
    db.Column('article_id', db.Integer, db.ForeignKey('debunk_article.id'), primary_key=True),
    db.Column('rumor_report_id', db.Integer, db.ForeignKey('rumor_report.id'), primary_key=True)
)

# 辟谣文章和澄清报道的关联表
article_clarification_association = db.Table('article_clarification_association',
    db.Column('article_id', db.Integer, db.ForeignKey('debunk_article.id'), primary_key=True),
    db.Column('clarification_report_id', db.Integer, db.ForeignKey('clarification_report.id'), primary_key=True)
)

class DebunkArticle(db.Model):
    """辟谣文章模型"""
    __tablename__ = 'debunk_article'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    source = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    published_at = db.Column(db.DateTime)
    tags = db.Column(db.String(255))  # 以逗号分隔的标签
    
    # 关联
    author = db.relationship('User', backref='debunk_articles')
    rumor_reports = db.relationship('RumorReport', secondary=article_rumor_association, 
                                  backref=db.backref('debunk_articles', lazy='dynamic'))
    clarification_reports = db.relationship('ClarificationReport', secondary=article_clarification_association, 
                                          backref=db.backref('debunk_articles', lazy='dynamic'))

class RumorReport(db.Model):
    """谣言报道模型"""
    __tablename__ = 'rumor_report'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255))
    url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # rumor_type可以是social_media, news, website等
    rumor_type = db.Column(db.String(50)) 
    rumor_probability = db.Column(db.Float)  # 谣言概率，0-1

class ClarificationReport(db.Model):
    """澄清报道模型"""
    __tablename__ = 'clarification_report'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255))
    url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 澄清评分，表示澄清的权威性，1-10
    authority_score = db.Column(db.Integer)

class WeiboDebunk(db.Model):
    """微博辟谣数据模型"""
    __tablename__ = 'weibo_debunk'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), default='weibo')
    content = db.Column(db.Text, nullable=False)
    weibo_mid_id = db.Column(db.String(50), unique=True)
    weibo_user_id = db.Column(db.String(50))
    weibo_user_name = db.Column(db.String(100))
    user_verified = db.Column(db.Boolean, default=False)
    user_verified_type = db.Column(db.Integer)
    user_verified_reason = db.Column(db.String(255))
    region = db.Column(db.String(100))
    attitudes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    reposts_count = db.Column(db.Integer, default=0)
    pics = db.Column(db.Text)  # 存储图片URL，以逗号分隔
    created_at = db.Column(db.DateTime)
    search_query = db.Column(db.String(255))  # 存储搜索关键词
    status = db.Column(db.String(20), default='pending')  # pending, verified, false
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'source': self.source,
            'content': self.content,
            'weibo_mid_id': self.weibo_mid_id,
            'weibo_user_id': self.weibo_user_id,
            'weibo_user_name': self.weibo_user_name,
            'user_verified': self.user_verified,
            'user_verified_type': self.user_verified_type,
            'user_verified_reason': self.user_verified_reason,
            'region': self.region,
            'attitudes_count': self.attitudes_count,
            'comments_count': self.comments_count,
            'reposts_count': self.reposts_count,
            'pics': self.pics.split(',') if self.pics else [],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'search_query': self.search_query,
            'status': self.status
        }

    def to_debunk_content(self):
        """转换为DebunkContent格式"""
        content = DebunkContent(
            source='weibo',
            content_id=self.weibo_mid_id,
            title=self.content[:100] if self.content else '',  # 取内容前100字作为标题
            content=self.content,
            author_id=self.weibo_user_id,
            author_name=self.weibo_user_name,
            author_verified=self.user_verified,
            author_verified_type=self.user_verified_type,
            author_verified_reason=self.user_verified_reason,
            region=self.region,
            attitudes_count=self.attitudes_count,
            comments_count=self.comments_count,
            reposts_count=self.reposts_count,
            images=self.pics,
            link=f'https://m.weibo.cn/detail/{self.weibo_mid_id}',
            publish_time=self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            created_at=self.created_at,
            search_query=self.search_query,
            status=self.status,
            origin_content=json.dumps(self.to_dict(), ensure_ascii=False)
        )
        return content

class XinlangDebunk(db.Model):
    """新浪辟谣数据模型"""
    __tablename__ = 'xinlang_debunk'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), default='xinlang')
    news_id = db.Column(db.String(100), unique=True)
    data_id = db.Column(db.String(100))
    title = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(100))  # 来源名称（如：北国网）
    link = db.Column(db.String(500))  # 文章链接
    image_url = db.Column(db.String(500))  # 图片链接
    category = db.Column(db.String(50))  # 分类（cms/mp等）
    comment_id = db.Column(db.String(100))  # 评论ID
    publish_time = db.Column(db.String(50))  # 发布时间描述
    search_query = db.Column(db.String(255))  # 搜索关键词
    created_at = db.Column(db.DateTime, default=datetime.now)  # 爬取时间
    status = db.Column(db.String(20), default='pending')  # pending, verified, false
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'source': self.source,
            'news_id': self.news_id,
            'data_id': self.data_id,
            'title': self.title,
            'source_name': self.source_name,
            'link': self.link,
            'image_url': self.image_url,
            'category': self.category,
            'comment_id': self.comment_id,
            'publish_time': self.publish_time,
            'search_query': self.search_query,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'status': self.status
        }

    def to_debunk_content(self):
        """转换为DebunkContent格式"""
        content = DebunkContent(
            source='xinlang',
            content_id=self.news_id,
            title=self.title,
            content=self.title,  # 新浪只有标题，用标题作为内容
            author_id=self.source_name,
            author_name=self.source_name,
            author_verified=True,  # 新浪新闻源默认为认证
            author_verified_type=3,  # 媒体认证
            author_verified_reason=f'新浪新闻源: {self.source_name}',
            region='',
            attitudes_count=0,
            comments_count=0,
            reposts_count=0,
            images=self.image_url,
            link=self.link,
            publish_time=self.publish_time,
            created_at=self.created_at,
            search_query=self.search_query,
            status=self.status,
            origin_content=json.dumps(self.to_dict(), ensure_ascii=False)
        )
        return content

class DebunkContent(db.Model):
    """辟谣内容聚合模型"""
    __tablename__ = 'debunk_content'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)  # xinlang/weibo
    content_id = db.Column(db.String(100), unique=True)  # news_id/mid
    title = db.Column(db.String(500))  # 标题(新浪有,微博用content前100字)
    content = db.Column(db.Text)  # 内容
    author_id = db.Column(db.String(100))  # 作者ID(weibo_user_id/source_name)
    author_name = db.Column(db.String(100))  # 作者名称(weibo_user_name/source_name)
    author_verified = db.Column(db.Boolean, default=False)  # 作者是否认证
    author_verified_type = db.Column(db.Integer)  # 认证类型
    author_verified_reason = db.Column(db.String(255))  # 认证原因
    region = db.Column(db.String(100))  # 地区
    attitudes_count = db.Column(db.Integer, default=0)  # 点赞/态度数
    comments_count = db.Column(db.Integer, default=0)  # 评论数
    reposts_count = db.Column(db.Integer, default=0)  # 转发数
    images = db.Column(db.Text)  # 图片URL列表，逗号分隔
    link = db.Column(db.String(500))  # 原文链接
    publish_time = db.Column(db.String(50))  # 发布时间描述
    created_at = db.Column(db.DateTime, default=datetime.now)  # 爬取时间
    search_query = db.Column(db.String(255))  # 搜索关键词
    status = db.Column(db.String(20), default='pending')  # pending, verified, false
    origin_content = db.Column(db.Text)  # 原始JSON内容
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'source': self.source,
            'content_id': self.content_id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'author_verified': self.author_verified,
            'author_verified_type': self.author_verified_type,
            'author_verified_reason': self.author_verified_reason,
            'region': self.region,
            'attitudes_count': self.attitudes_count,
            'comments_count': self.comments_count,
            'reposts_count': self.reposts_count,
            'images': self.images.split(',') if self.images else [],
            'link': self.link,
            'publish_time': self.publish_time,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'search_query': self.search_query,
            'status': self.status
        } 