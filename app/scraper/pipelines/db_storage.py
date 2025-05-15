"""数据库存储管道

将爬取的数据存储到数据库中
"""

import json
import logging
from datetime import datetime
from scrapy.exceptions import DropItem
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logger = logging.getLogger('db_storage_pipeline')
logger.setLevel(logging.INFO)

class DatabaseStoragePipeline:
    """数据库存储管道，将爬取的数据保存到数据库"""
    
    def __init__(self):
        """初始化存储管道"""
        self.app = None
        self.db = None
        self.NewsData = None
        self.RumorData = None
        self.SocialMediaData = None
        self.items_count = {
            'news': 0,
            'rumor': 0,
            'social': 0
        }
        logger.info("数据库存储管道初始化完成")
    
    def open_spider(self, spider):
        """爬虫启动时调用
        
        Args:
            spider: 爬虫实例
        """
        # 获取Flask应用实例和数据库模型
        self.app = spider.settings.get('FLASK_APP')
        
        if not self.app:
            logger.warning("未找到Flask应用实例，将无法存储数据到数据库")
            return
            
        # 导入数据库和模型
        from app import db
        from app.models.news_data import NewsData, RumorData, SocialMediaData
        
        self.db = db
        self.NewsData = NewsData
        self.RumorData = RumorData
        self.SocialMediaData = SocialMediaData
        
        logger.info(f"数据库存储管道已启动: {spider.name}")
    
    def process_item(self, item, spider):
        """处理爬取的项目
        
        Args:
            item: 爬取的项目
            spider: 爬虫实例
            
        Returns:
            item: 处理后的项目
        """
        if not self.app or not self.db:
            logger.warning("未初始化数据库连接，跳过数据存储")
            return item
            
        try:
            # 创建应用上下文
            with self.app.app_context():
                # 根据项目类型选择保存方式
                if 'news_id' in item:
                    self._save_news_item(item)
                elif 'rumor_id' in item:
                    self._save_rumor_item(item)
                elif 'post_id' in item:
                    self._save_social_item(item)
                else:
                    logger.warning(f"未知项目类型: {item}")
                    return item
        except Exception as e:
            logger.error(f"保存数据时出错: {str(e)}")
            raise DropItem(f"保存数据失败: {str(e)}")
            
        return item
    
    def _save_news_item(self, item):
        """保存新闻项目
        
        Args:
            item: 新闻项目
        """
        try:
            # 检查是否已存在
            existing = self.NewsData.query.filter_by(news_id=item['news_id']).first()
            
            if existing:
                # 更新已有记录
                for key, value in item.items():
                    if key != 'news_id' and hasattr(existing, key):
                        if key in ['media', 'tags']:
                            value = json.dumps(value) if value else None
                        setattr(existing, key, value)
                
                existing.crawl_time = datetime.now()
                self.db.session.commit()
                logger.info(f"更新新闻: {item['title']}")
                
            else:
                # 创建新记录
                news_data = self.NewsData(
                    news_id=item['news_id'],
                    title=item['title'],
                    content=item['content'],
                    summary=item.get('summary'),
                    source=item.get('source'),
                    url=item.get('url'),
                    pub_date=item.get('pub_date'),
                    crawl_time=datetime.now(),
                    author=item.get('author'),
                    category=item.get('category'),
                    tags=json.dumps(item['tags']) if 'tags' in item and item['tags'] else None,
                    media=json.dumps(item['media']) if 'media' in item and item['media'] else None,
                    source_type=item.get('source_type'),
                    recommendation_level=item.get('recommendation_level', 0),
                    keyword_match=item.get('keyword_match', 0.0),
                    processed=False
                )
                
                self.db.session.add(news_data)
                self.db.session.commit()
                self.items_count['news'] += 1
                logger.info(f"保存新闻: {item['title']}")
                
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"保存新闻出错: {str(e)}")
            raise
    
    def _save_rumor_item(self, item):
        """保存谣言项目
        
        Args:
            item: 谣言项目
        """
        try:
            # 检查是否已存在
            existing = self.RumorData.query.filter_by(rumor_id=item['rumor_id']).first()
            
            if existing:
                # 更新已有记录
                for key, value in item.items():
                    if key != 'rumor_id' and hasattr(existing, key):
                        if key in ['media', 'tags']:
                            value = json.dumps(value) if value else None
                        setattr(existing, key, value)
                
                existing.crawl_time = datetime.now()
                self.db.session.commit()
                logger.info(f"更新谣言: {item['title']}")
                
            else:
                # 创建新记录
                rumor_data = self.RumorData(
                    rumor_id=item['rumor_id'],
                    title=item['title'],
                    content=item['content'],
                    source=item.get('source'),
                    refutation=item.get('refutation'),
                    refutation_source=item.get('refutation_source'),
                    url=item.get('url'),
                    pub_date=item.get('pub_date'),
                    crawl_time=datetime.now(),
                    category=item.get('category'),
                    spread_level=item.get('spread_level', 1),
                    harm_level=item.get('harm_level', 1),
                    tags=json.dumps(item['tags']) if 'tags' in item and item['tags'] else None,
                    media=json.dumps(item['media']) if 'media' in item and item['media'] else None,
                    source_type=item.get('source_type'),
                    processed=False
                )
                
                self.db.session.add(rumor_data)
                self.db.session.commit()
                self.items_count['rumor'] += 1
                logger.info(f"保存谣言: {item['title']}")
                
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"保存谣言出错: {str(e)}")
            raise
    
    def _save_social_item(self, item):
        """保存社交媒体项目
        
        Args:
            item: 社交媒体项目
        """
        try:
            # 检查是否已存在
            existing = self.SocialMediaData.query.filter_by(post_id=item['post_id']).first()
            
            if existing:
                # 更新已有记录
                for key, value in item.items():
                    if key != 'post_id' and hasattr(existing, key):
                        if key in ['media', 'tags', 'topics']:
                            value = json.dumps(value) if value else None
                        setattr(existing, key, value)
                
                existing.crawl_time = datetime.now()
                self.db.session.commit()
                logger.info(f"更新社交媒体帖子: {item['platform']}:{item['post_id']}")
                
            else:
                # 创建新记录
                social_data = self.SocialMediaData(
                    post_id=item['post_id'],
                    platform=item['platform'],
                    content=item['content'],
                    user_id=item.get('user_id'),
                    username=item.get('username'),
                    verified_type=item.get('verified_type'),
                    pub_date=item.get('pub_date'),
                    crawl_time=datetime.now(),
                    url=item.get('url'),
                    shares=item.get('shares', 0),
                    comments=item.get('comments', 0),
                    likes=item.get('likes', 0),
                    media=json.dumps(item['media']) if 'media' in item and item['media'] else None,
                    tags=json.dumps(item['tags']) if 'tags' in item and item['tags'] else None,
                    topics=json.dumps(item['topics']) if 'topics' in item and item['topics'] else None,
                    location=item.get('location'),
                    content_type=item.get('content_type', 'original'),
                    recommendation_level=item.get('recommendation_level', 0),
                    keyword_match=item.get('keyword_match', 0.0),
                    processed=False
                )
                
                self.db.session.add(social_data)
                self.db.session.commit()
                self.items_count['social'] += 1
                logger.info(f"保存社交媒体帖子: {item['platform']}:{item['post_id']}")
                
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"保存社交媒体帖子出错: {str(e)}")
            raise
    
    def close_spider(self, spider):
        """爬虫关闭时调用
        
        Args:
            spider: 爬虫实例
        """
        logger.info(f"数据库存储管道已关闭: {spider.name}")
        logger.info(f"已保存 {sum(self.items_count.values())} 条数据:")
        logger.info(f"- 新闻: {self.items_count['news']} 条")
        logger.info(f"- 谣言: {self.items_count['rumor']} 条")
        logger.info(f"- 社交媒体: {self.items_count['social']} 条") 