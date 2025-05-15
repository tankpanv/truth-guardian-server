"""基础爬虫类

为所有爬虫提供基础功能
"""

import re
import time
import logging
import hashlib
import os
import requests
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from app.models import News
from app.extensions import db
from app.scraper.utils import ScraperUtils

# 配置日志
logger = logging.getLogger('base_spider')
logger.setLevel(logging.INFO)

class BaseSpider:
    """基础爬虫类"""
    
    name = 'base_spider'
    
    # 默认设置
    DEFAULT_SETTINGS = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],
        'ROBOTSTXT_OBEY': True
    }
    
    # 请求头模板
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    }
    
    def __init__(self, api_base_url="http://localhost:5005", username=None, password=None):
        """初始化基础爬虫
        
        Args:
            api_base_url: API基础URL
            username: 用户名
            password: 密码
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.username = username or os.getenv('API_USERNAME', 'testuser')
        self.password = password or os.getenv('API_PASSWORD', 'password123')
        self.token = None
        
        # 初始化已访问的URL集合
        self.visited_urls: Set[str] = set()
        
        # 初始化User-Agent池
        self.user_agent = UserAgent()
        
        # 初始化统计信息
        self.stats = {
            'start_time': None,
            'end_time': None,
            'pages_crawled': 0,
            'items_scraped': 0,
            'errors': 0
        }
        
        # 初始化重试信息
        self.retry_counts: Dict[str, int] = {}
        
        logger.info(f"基础爬虫 {self.name} 初始化完成")
        
    def start_crawl(self):
        """开始爬取"""
        try:
            self.stats['start_time'] = datetime.now()
            self.pre_crawl()
            
            for request in self.start_requests():
                self._process_request(request)
                
            self.post_crawl()
            self.stats['end_time'] = datetime.now()
            
            self._log_stats()
            
        except Exception as e:
            logger.error(f"爬虫运行出错: {str(e)}")
            logger.exception(e)
            self.stats['errors'] += 1
            
    def pre_crawl(self):
        """爬取前的准备工作"""
        pass
        
    def post_crawl(self):
        """爬取后的清理工作"""
        pass
        
    def start_requests(self):
        """生成初始请求
        
        Returns:
            Iterator: 请求迭代器
        """
        raise NotImplementedError
        
    def parse(self, response):
        """解析响应
        
        Args:
            response: 响应对象
        """
        raise NotImplementedError
        
    def _process_request(self, request: Dict):
        """处理请求
        
        Args:
            request: 请求配置
        """
        try:
            url = request['url']
            
            # 检查URL是否已访问
            if self.is_duplicate_url(url):
                return
                
            # 发送请求
            response = self._send_request(request)
            
            # 处理响应
            if response:
                self.stats['pages_crawled'] += 1
                self.visited_urls.add(url)
                
                # 调用回调函数
                callback = request.get('callback', self.parse)
                callback(response)
                
        except Exception as e:
            logger.error(f"处理请求出错: {str(e)}")
            logger.exception(e)
            self.stats['errors'] += 1
            
            # 重试请求
            self._retry_request(request)
            
    def _send_request(self, request: Dict):
        """发送HTTP请求
        
        Args:
            request: 请求配置
            
        Returns:
            Response: 响应对象
        """
        url = request['url']
        headers = request.get('headers', self.DEFAULT_HEADERS)
        proxy = request.get('proxy')
        
        try:
            # TODO: 实现HTTP请求
            pass
            
        except Exception as e:
            logger.error(f"发送请求出错: {str(e)}")
            logger.exception(e)
            return None
            
    def _retry_request(self, request: Dict):
        """重试请求
        
        Args:
            request: 请求配置
        """
        url = request['url']
        retry_count = self.retry_counts.get(url, 0)
        
        if retry_count < self.DEFAULT_SETTINGS['RETRY_TIMES']:
            # 增加重试次数
            self.retry_counts[url] = retry_count + 1
            
            # 添加随机延迟
            time.sleep(self.DEFAULT_SETTINGS['DOWNLOAD_DELAY'] * (retry_count + 1))
            
            # 重新处理请求
            self._process_request(request)
            
    def is_duplicate_url(self, url: str) -> bool:
        """检查URL是否已访问
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 是否已访问
        """
        return url in self.visited_urls
        
    def save_news(self, news_data: Dict):
        """保存新闻数据
        
        Args:
            news_data: 新闻数据
        """
        try:
            # 创建新闻对象
            news = News(
                id=news_data['id'],
                url=news_data['url'],
                title=news_data['title'],
                content=news_data['content'],
                publish_date=news_data['publish_date'],
                author=news_data['author'],
                category=news_data['category'],
                source=news_data['source'],
                crawl_time=news_data['crawl_time']
            )
            
            # 保存到数据库
            db.session.add(news)
            db.session.commit()
            
            self.stats['items_scraped'] += 1
            
        except Exception as e:
            logger.error(f"保存新闻出错: {str(e)}")
            logger.exception(e)
            db.session.rollback()
            
    def _log_stats(self):
        """记录爬虫统计信息"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("爬虫统计信息:")
        logger.info(f"- 运行时间: {duration}")
        logger.info(f"- 爬取页面: {self.stats['pages_crawled']}")
        logger.info(f"- 采集数据: {self.stats['items_scraped']}")
        logger.info(f"- 错误数量: {self.stats['errors']}")
        
    @staticmethod
    def get_domain(url: str) -> str:
        """获取URL域名
        
        Args:
            url: 目标URL
            
        Returns:
            str: 域名
        """
        parsed = urlparse(url)
        return parsed.netloc
        
    @staticmethod
    def normalize_url(url: str) -> str:
        """标准化URL
        
        Args:
            url: 目标URL
            
        Returns:
            str: 标准化后的URL
        """
        # 移除URL参数
        url = re.sub(r'\?.*$', '', url)
        
        # 移除锚点
        url = re.sub(r'#.*$', '', url)
        
        # 移除多余的斜杠
        url = re.sub(r'([^:])//+', r'\1/', url)
        
        return url.rstrip('/')

    def login(self):
        """登录获取token
        
        Returns:
            bool: 登录是否成功
        """
        url = f"{self.api_base_url}/api/auth/login"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    self.token = result['access_token']
                    logger.info("登录成功")
                    return True
                else:
                    logger.error("登录响应中没有token")
                    return False
            else:
                logger.error(f"登录失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"登录请求出错: {str(e)}")
            return False 