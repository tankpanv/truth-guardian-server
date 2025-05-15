"""爬虫项目类

定义爬取数据的结构
"""

import scrapy
from datetime import datetime

class NewsItem(scrapy.Item):
    """新闻项目"""
    
    # 唯一ID，用于去重
    news_id = scrapy.Field()
    
    # 标题
    title = scrapy.Field()
    
    # 内容
    content = scrapy.Field()
    
    # 摘要
    summary = scrapy.Field()
    
    # 新闻来源（网站名称）
    source = scrapy.Field()
    
    # 原始URL
    url = scrapy.Field()
    
    # 发布时间
    pub_date = scrapy.Field()
    
    # 采集时间
    crawl_time = scrapy.Field(default=datetime.now)
    
    # 作者/发布者
    author = scrapy.Field()
    
    # 分类/栏目
    category = scrapy.Field()
    
    # 标签列表
    tags = scrapy.Field()
    
    # 相关媒体（图片/视频链接）
    media = scrapy.Field()
    
    # 数据来源类型（新闻网站/政府网站/社交媒体）
    source_type = scrapy.Field()
    
    # 推荐级别（根据内容重要性和相关性评分）
    recommendation_level = scrapy.Field()
    
    # 关键词匹配度
    keyword_match = scrapy.Field()

class RumorItem(scrapy.Item):
    """谣言项目"""
    
    # 唯一ID，用于去重
    rumor_id = scrapy.Field()
    
    # 谣言标题
    title = scrapy.Field()
    
    # 谣言内容
    content = scrapy.Field()
    
    # 谣言来源
    source = scrapy.Field()
    
    # 辟谣内容
    refutation = scrapy.Field()
    
    # 辟谣来源
    refutation_source = scrapy.Field()
    
    # 原始URL
    url = scrapy.Field()
    
    # 发布时间
    pub_date = scrapy.Field()
    
    # 采集时间
    crawl_time = scrapy.Field(default=datetime.now)
    
    # 谣言类型/分类
    category = scrapy.Field()
    
    # 传播范围评估 (1-10)
    spread_level = scrapy.Field()
    
    # 危害程度评估 (1-10)
    harm_level = scrapy.Field()
    
    # 标签列表
    tags = scrapy.Field()
    
    # 相关媒体（图片/视频链接）
    media = scrapy.Field()
    
    # 数据来源类型（辟谣平台/政府网站/社交媒体）
    source_type = scrapy.Field()

class SocialMediaPost(scrapy.Item):
    """社交媒体帖子"""
    
    # 唯一ID
    post_id = scrapy.Field()
    
    # 平台（微博/微信/抖音等）
    platform = scrapy.Field()
    
    # 内容
    content = scrapy.Field()
    
    # 发布者ID
    user_id = scrapy.Field()
    
    # 发布者名称
    username = scrapy.Field()
    
    # 发布者认证类型（官方/媒体/个人）
    verified_type = scrapy.Field()
    
    # 发布时间
    pub_date = scrapy.Field()
    
    # 采集时间
    crawl_time = scrapy.Field(default=datetime.now)
    
    # 原始URL
    url = scrapy.Field()
    
    # 转发/分享数
    shares = scrapy.Field()
    
    # 评论数
    comments = scrapy.Field()
    
    # 点赞数
    likes = scrapy.Field()
    
    # 相关媒体（图片/视频链接）
    media = scrapy.Field()
    
    # 标签列表
    tags = scrapy.Field()
    
    # 话题/话题标签
    topics = scrapy.Field()
    
    # 地理位置
    location = scrapy.Field()
    
    # 内容类型（原创/转发）
    content_type = scrapy.Field()
    
    # 推荐级别
    recommendation_level = scrapy.Field()
    
    # 关键词匹配度
    keyword_match = scrapy.Field()

# 为保持兼容性，创建SocialMediaItem作为SocialMediaPost的别名
SocialMediaItem = SocialMediaPost 