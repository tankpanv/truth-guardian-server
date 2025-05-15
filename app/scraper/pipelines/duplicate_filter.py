"""重复数据过滤管道

检测并过滤重复的爬取数据，防止数据库中出现重复条目
"""

import logging
import hashlib
from scrapy.exceptions import DropItem
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logger = logging.getLogger('duplicate_filter_pipeline')
logger.setLevel(logging.INFO)

class DuplicateFilterPipeline:
    """重复数据过滤管道，确保不会插入重复数据"""
    
    def __init__(self):
        """初始化去重管道"""
        # 存储已处理项目的指纹
        self.fingerprints = set()
        logger.info("重复数据过滤管道初始化完成")
    
    def process_item(self, item, spider):
        """处理爬取的项目
        
        Args:
            item: 爬取的项目
            spider: 爬虫实例
            
        Returns:
            item: 处理后的项目
            
        Raises:
            DropItem: 如果项目重复，则丢弃
        """
        # 检查项目类型
        if 'news_id' in item:
            # 新闻项目检查
            fingerprint = self.get_fingerprint(item, 'news')
            item_id = item.get('news_id', '')
            item_type = 'news'
        elif 'rumor_id' in item:
            # 谣言项目检查
            fingerprint = self.get_fingerprint(item, 'rumor')
            item_id = item.get('rumor_id', '')
            item_type = 'rumor'
        elif 'post_id' in item:
            # 社交媒体项目检查
            fingerprint = self.get_fingerprint(item, 'social')
            item_id = item.get('post_id', '')
            item_type = 'social'
        else:
            # 未知项目类型
            raise DropItem(f"未知项目类型: {item}")
        
        # 检查内存中是否已存在
        if fingerprint in self.fingerprints:
            raise DropItem(f"重复项目: {item_id}")
        
        # 检查数据库中是否已存在
        try:
            if spider.settings.get('FLASK_APP') and hasattr(spider, 'check_duplicate'):
                if spider.check_duplicate(item_type, item):
                    raise DropItem(f"数据库中已存在: {item_id}")
        except (SQLAlchemyError, AttributeError) as e:
            logger.error(f"检查数据库重复时出错: {str(e)}")
            # 出错时不丢弃，让数据库约束处理重复情况
            pass
        
        # 添加到内存集合
        self.fingerprints.add(fingerprint)
        
        return item
    
    def get_fingerprint(self, item, item_type):
        """生成项目指纹
        
        Args:
            item: 爬取的项目
            item_type: 项目类型
            
        Returns:
            str: 项目指纹
        """
        if item_type == 'news':
            # 新闻指纹: URL + 标题
            url = item.get('url', '')
            title = item.get('title', '')
            data = f"{url}|{title}"
        elif item_type == 'rumor':
            # 谣言指纹: 标题 + 内容前100字符
            title = item.get('title', '')
            content = item.get('content', '')[:100]
            data = f"{title}|{content}"
        elif item_type == 'social':
            # 社交媒体指纹: 平台 + 用户ID + 内容前100字符
            platform = item.get('platform', '')
            user_id = item.get('user_id', '')
            content = item.get('content', '')[:100]
            data = f"{platform}|{user_id}|{content}"
        else:
            data = str(item)
        
        # 使用SHA256生成指纹
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def open_spider(self, spider):
        """爬虫启动时调用
        
        Args:
            spider: 爬虫实例
        """
        logger.info(f"重复数据过滤管道已启动: {spider.name}")
    
    def close_spider(self, spider):
        """爬虫关闭时调用
        
        Args:
            spider: 爬虫实例
        """
        logger.info(f"重复数据过滤管道已关闭: {spider.name}, 共处理 {len(self.fingerprints)} 条数据")
        # 清空指纹集合
        self.fingerprints.clear() 