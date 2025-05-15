"""新闻网站爬虫

负责从新闻网站爬取新闻信息
"""

import re
import json
import logging
import hashlib
import time
import random
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

import scrapy
from scrapy.exceptions import CloseSpider
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from app.scraper.items import NewsItem
from app.scraper.spiders.base_spider import BaseSpider
from app.scraper.utils import ScraperUtils

# 配置日志
logger = logging.getLogger('news_spider')
logger.setLevel(logging.INFO)

class NewsSpider(BaseSpider):
    """新闻网站爬虫"""
    
    name = 'news_spider'
    
    # 新闻源配置
    NEWS_SOURCES = [
        {
            'name': '新华网',
            'domain': 'news.xinhuanet.com',
            'start_urls': [
                'http://www.xinhuanet.com/politics/',
                'http://www.xinhuanet.com/fortune/',
                'http://www.xinhuanet.com/tech/',
                'http://www.xinhuanet.com/world/'
            ],
            'list_selectors': [
                'ul.dataList li a',
                'div.dataList div.news a',
                'div.right-list ul li a'
            ]
        },
        {
            'name': '人民网',
            'domain': 'people.com.cn',
            'start_urls': [
                'http://politics.people.com.cn/',
                'http://finance.people.com.cn/',
                'http://tech.people.com.cn/',
                'http://world.people.com.cn/'
            ],
            'list_selectors': [
                'div.news_box .news a',
                'div.list_box ul li a',
                'div.fl ul li a'
            ]
        }
    ]
    
    # 标题选择器
    TITLE_SELECTORS = [
        'h1.article-title',
        'h1.post-title',
        'h1.entry-title',
        'div.article-title h1',
        'div.post-title h1',
        'div.title h1',
        'header h1',
        'article h1',
        'div.article h1'
    ]
    
    # 正文选择器
    CONTENT_SELECTORS = [
        'div.article-content',
        'div.post-content',
        'div.entry-content',
        'article.content',
        'div.article',
        'div.content',
        'article',
        'div.main-content',
        'div.article-body'
    ]
    
    # 日期选择器
    DATE_SELECTORS = [
        'time.entry-date',
        'span.date',
        'div.article-date',
        'div.post-date',
        'div.entry-date',
        'time.published',
        'time.post-date',
        'meta[property="article:published_time"]',
        'meta[name="publishdate"]'
    ]
    
    # 作者选择器
    AUTHOR_SELECTORS = [
        'span.author',
        'a.author',
        'div.author-name',
        'div.article-author',
        'div.post-author',
        'meta[name="author"]',
        'meta[property="article:author"]',
        'div.byline',
        'p.byline'
    ]
    
    # 分类选择器
    CATEGORY_SELECTORS = [
        'div.category',
        'span.category',
        'a.category',
        'div.article-category',
        'div.post-category',
        'meta[property="article:section"]',
        'meta[name="category"]'
    ]
    
    # 代理池
    PROXY_POOL = [
        # TODO: 添加代理服务器
    ]
    
    def __init__(self, *args, **kwargs):
        """初始化爬虫
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        super(NewsSpider, self).__init__(*args, **kwargs)
        
        # 获取配置中的新闻源
        sources = self.settings.get('TRUTH_GUARDIAN_SETTINGS', {}).get('SOURCES', {}).get('news', [])
        
        if not sources:
            logger.warning("未配置新闻源，爬虫将不会启动")
            raise CloseSpider("未配置新闻源")
            
        # 设置允许的域名
        self.allowed_domains = sources
        
        # 构造起始URL
        self.start_urls = [f"https://{domain}" for domain in self.allowed_domains]
        
        # 新闻来源映射
        self.source_mapping = {
            'news.sina.com.cn': '新浪新闻',
            'news.163.com': '网易新闻',
            'news.qq.com': '腾讯新闻',
            'news.ifeng.com': '凤凰新闻',
            'news.sohu.com': '搜狐新闻'
        }
        
        # 初始化User-Agent池
        self.user_agent = UserAgent()
        
        # 初始化代理池
        self.proxy_pool = self._init_proxy_pool()
        
        # 访问延迟设置
        self.min_delay = 2  # 最小延迟秒数
        self.max_delay = 5  # 最大延迟秒数
        
        # 重试设置
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 5  # 重试等待秒数
        
        # 初始化工具类
        self.utils = ScraperUtils()
        
        # 初始化请求头
        self.headers = self.DEFAULT_HEADERS.copy()
        self.headers['User-Agent'] = self.user_agent.random
        
        # 初始化统计信息
        self.stats = {
            'start_time': datetime.now(),
            'pages_crawled': 0,
            'news_saved': 0,
            'errors': 0
        }
        
        logger.info(f"新闻爬虫初始化完成，目标网站: {', '.join(self.allowed_domains)}")
    
    def start_requests(self):
        """生成初始请求"""
        try:
            for source in self.NEWS_SOURCES:
                logger.info(f"开始爬取新闻源: {source['name']}")
                
                for start_url in source['start_urls']:
                    # 创建请求
                    request = {
                        'url': start_url,
                        'headers': self.headers.copy(),
                        'callback': self.parse_list,
                        'meta': {'source': source}
                    }
                    
                    # 添加随机延迟
                    time.sleep(random.uniform(1, 3))
                    
                    # 处理请求
                    self._process_request(request)
                    
        except Exception as e:
            logger.error(f"生成初始请求出错: {str(e)}")
            logger.exception(e)
            
    def parse_list(self, response):
        """解析新闻列表页
        
        Args:
            response: 响应对象
        """
        try:
            source = response.meta['source']
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取新闻链接
            for selector in source['list_selectors']:
                links = soup.select(selector)
                
                for link in links:
                    url = link.get('href')
                    if not url:
                        continue
                        
                    # 处理相对URL
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(response.url, url)
                        
                    # 标准化URL
                    url = self.normalize_url(url)
                    
                    # 检查是否为新闻页面
                    if self.is_news_url(url) and not self.is_duplicate_url(url):
                        # 创建请求
                        request = {
                            'url': url,
                            'headers': self.headers.copy(),
                            'callback': self.parse,
                            'meta': {'source': source}
                        }
                        
                        # 添加随机延迟
                        time.sleep(random.uniform(1, 3))
                        
                        # 处理请求
                        self._process_request(request)
                        
            # 提取下一页链接
            next_page = self._get_next_page(soup, source)
            if next_page:
                # 创建下一页请求
                request = {
                    'url': next_page,
                    'headers': self.headers.copy(),
                    'callback': self.parse_list,
                    'meta': {'source': source}
                }
                
                # 添加随机延迟
                time.sleep(random.uniform(1, 3))
                
                # 处理请求
                self._process_request(request)
                
        except Exception as e:
            logger.error(f"解析列表页出错: {str(e)}")
            logger.exception(e)
            self.stats['errors'] += 1
            
    def parse_detail(self, response):
        """解析新闻详情页
        
        Args:
            response: 响应对象
        """
        try:
            source = response.meta['source']
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取新闻数据
            news_data = {
                'url': response.url,
                'title': self.extract_title(soup),
                'content': self.extract_content(soup),
                'publish_date': self.extract_date(soup),
                'author': self.extract_author(soup),
                'category': self.extract_category(soup),
                'source': source['name'],
                'crawl_time': datetime.now()
            }
            
            # 生成新闻ID
            news_data['id'] = self.utils.generate_id(
                f"{news_data['url']}|{news_data['title']}",
                'news'
            )
            
            # 保存新闻数据
            self.save_news(news_data)
            
            # 提取更多链接
            self.extract_links(soup, response.url)
            
        except Exception as e:
            logger.error(f"解析详情页出错: {str(e)}")
            logger.exception(e)
            
    def _make_request(self, url: str, callback, meta: Optional[Dict] = None):
        """构造请求
        
        Args:
            url: 请求URL
            callback: 回调函数
            meta: 元数据
        """
        headers = {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        # 随机选择代理
        proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
        
        return {
            'url': url,
            'callback': callback,
            'headers': headers,
            'meta': meta,
            'proxy': proxy,
            'dont_filter': True
        }
        
    def extract_title(self, soup: BeautifulSoup) -> str:
        """提取新闻标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 新闻标题
        """
        title = None
        
        # 尝试不同的选择器
        for selector in self.TITLE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                break
                
        if not title:
            # 尝试使用<title>标签
            title_tag = soup.title
            if title_tag:
                title = title_tag.get_text(strip=True)
                
        if not title:
            logger.warning("未找到新闻标题")
            return ""
            
        return self.utils.clean_text(title)
        
    def extract_content(self, soup: BeautifulSoup) -> str:
        """提取新闻正文
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 新闻正文
        """
        content = None
        
        # 尝试不同的选择器
        for selector in self.CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                # 移除无关元素
                for tag in element.select('script, style, iframe, form'):
                    tag.decompose()
                    
                content = element.get_text(strip=True)
                break
                
        if not content:
            logger.warning("未找到新闻正文")
            return ""
            
        return self.utils.clean_text(content)
        
    def extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """提取发布日期
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Optional[datetime]: 发布日期
        """
        date_str = None
        
        # 尝试不同的选择器
        for selector in self.DATE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                # 尝试获取datetime属性
                date_str = element.get('datetime') or element.get('content')
                if not date_str:
                    date_str = element.get_text(strip=True)
                break
                
        if not date_str:
            logger.warning("未找到发布日期")
            return None
            
        try:
            # 解析日期字符串
            return self.utils.parse_date(date_str)
        except Exception as e:
            logger.error(f"解析日期出错: {str(e)}")
            return None
        
    def extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 作者
        """
        author = None
        
        # 尝试不同的选择器
        for selector in self.AUTHOR_SELECTORS:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') or element.get_text(strip=True)
                break
                
        if not author:
            logger.warning("未找到作者")
            return ""
            
        return self.utils.clean_text(author)
        
    def extract_category(self, soup: BeautifulSoup) -> str:
        """提取分类
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 分类
        """
        category = None
        
        # 尝试不同的选择器
        for selector in self.CATEGORY_SELECTORS:
            element = soup.select_one(selector)
            if element:
                category = element.get('content') or element.get_text(strip=True)
                break
                
        if not category:
            logger.warning("未找到分类")
            return ""
            
        return self.utils.clean_text(category)
        
    def extract_links(self, soup: BeautifulSoup, base_url: str):
        """提取页面链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
        """
        try:
            # 获取所有链接
            links = soup.find_all('a', href=True)
            
            for link in links:
                url = link['href']
                
                # 处理相对URL
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(base_url, url)
                    
                # 标准化URL
                url = self.normalize_url(url)
                
                # 检查是否为新闻页面
                if self.is_news_url(url) and not self.is_duplicate_url(url):
                    # 创建新的请求
                    request = {
                        'url': url,
                        'headers': self.headers.copy(),
                        'callback': self.parse
                    }
                    
                    # 添加随机延迟
                    time.sleep(random.uniform(1, 3))
                    
                    # 处理请求
                    self._process_request(request)
                    
        except Exception as e:
            logger.error(f"提取链接出错: {str(e)}")
            logger.exception(e)
            
    def is_news_url(self, url: str) -> bool:
        """检查是否为新闻URL
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 是否为新闻URL
        """
        # 检查URL格式
        if not url or not url.startswith(('http://', 'https://')):
            return False
            
        # 检查域名
        domain = self.get_domain(url)
        if not domain:
            return False
            
        # 检查URL路径
        path = url.split(domain)[-1].lower()
        
        # 排除常见的非新闻页面
        exclude_patterns = [
            r'/search',
            r'/tag/',
            r'/author/',
            r'/about',
            r'/contact',
            r'/login',
            r'/register',
            r'/rss',
            r'/feed',
            r'\.(jpg|jpeg|png|gif|pdf|doc|docx)$'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, path):
                return False
                
        # 检查新闻特征
        news_patterns = [
            r'/news/',
            r'/article/',
            r'/story/',
            r'/\d{4}/',
            r'/\d{4}-\d{2}/',
            r'/\d{8}/',
            r'/p/\d+',
            r'/content/\d+'
        ]
        
        for pattern in news_patterns:
            if re.search(pattern, path):
                return True
                
        return False
        
    def _get_next_page(self, soup: BeautifulSoup, source: Dict) -> Optional[str]:
        """获取下一页链接
        
        Args:
            soup: BeautifulSoup对象
            source: 新闻源配置
            
        Returns:
            Optional[str]: 下一页链接
        """
        # 常见的下一页选择器
        next_page_selectors = [
            'a.next',
            'a.nextPage',
            'a:contains("下一页")',
            'a[rel="next"]',
            'a.pagination-next',
            'a.next-page'
        ]
        
        for selector in next_page_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                url = next_link['href']
                
                # 处理相对URL
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(source['start_urls'][0], url)
                    
                return self.normalize_url(url)
                
        return None
        
    def _init_proxy_pool(self) -> List[str]:
        """初始化代理池
        
        Returns:
            List[str]: 代理列表
        """
        # TODO: 实现代理池
        return []
    
    def parse(self, response):
        """解析网站首页，提取新闻链接"""
        # 提取新闻链接
        news_links = response.css('a[href*="news"]::attr(href), a[href*="article"]::attr(href), a[href*="politics"]::attr(href)').getall()
        
        # 去重
        news_links = list(set(news_links))
        
        # 构造完整URL
        for link in news_links:
            # 处理相对URL
            if not link.startswith(('http://', 'https://')):
                link = urljoin(response.url, link)
            
            # 确保链接属于允许的域名
            parsed_url = urlparse(link)
            if parsed_url.netloc in self.allowed_domains:
                # 传递源网站信息
                source = next((self.source_mapping[domain] for domain in self.allowed_domains if domain in parsed_url.netloc), '未知来源')
                
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_news,
                    meta={'source': source}
                )
    
    def parse_news(self, response):
        """解析新闻页面"""
        # 提取标题
        title = self.extract_title(response)
        if not title:
            return
            
        # 提取内容
        content = self.extract_content(response)
        if not content:
            return
            
        # 提取发布日期
        pub_date = self.extract_date(response)
        
        # 提取作者
        author = self.extract_author(response)
        
        # 提取分类
        category = self.extract_category(response)
        
        # 提取媒体
        media = self.extract_media(response)
        
        # 生成新闻ID
        news_id = self.generate_news_id(response.url, title)
        
        # 计算关键词匹配度
        keyword_match = self.calculate_keyword_match(title + ' ' + content)
        
        # 创建新闻项
        item = NewsItem()
        item['news_id'] = news_id
        item['title'] = title
        item['content'] = content
        item['summary'] = self.generate_summary(content)
        item['source'] = response.meta.get('source', '未知来源')
        item['url'] = response.url
        item['pub_date'] = pub_date
        item['author'] = author
        item['category'] = category
        item['tags'] = self.extract_tags(title + ' ' + content)
        item['media'] = media
        item['source_type'] = 'news'
        item['keyword_match'] = keyword_match
        item['recommendation_level'] = self.calculate_recommendation_level({'keyword_match': keyword_match, 'source_type': 'news'})
        
        self.item_count += 1
        logger.info(f"已爬取新闻: {title} [{response.url}]")
        
        yield item
    
    def extract_media(self, response):
        """提取媒体"""
        # 提取图片
        images = []
        
        # 内容图片
        content_images = response.css('.article-content img::attr(src), .content img::attr(src), .article img::attr(src)').getall()
        for img_url in content_images:
            if img_url:
                # 处理相对URL
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(response.url, img_url)
                images.append({'type': 'image', 'url': img_url})
        
        # 视频
        videos = response.css('video::attr(src), .video-player::attr(data-src)').getall()
        for video_url in videos:
            if video_url:
                # 处理相对URL
                if not video_url.startswith(('http://', 'https://')):
                    video_url = urljoin(response.url, video_url)
                images.append({'type': 'video', 'url': video_url})
                
        return images
    
    def extract_tags(self, text):
        """提取标签"""
        # 如果文本为空，返回空列表
        if not text:
            return []
            
        # 提取关键词作为标签
        tags = []
        for keyword in self.keywords:
            if keyword in text and keyword not in tags:
                tags.append(keyword)
                
        # 限制标签数量
        return tags[:5]
    
    def generate_summary(self, content, max_length=200):
        """生成摘要"""
        if not content:
            return ""
            
        # 简单摘要：取前200个字符
        summary = content[:max_length].strip()
        
        # 确保摘要不会截断句子
        if len(content) > max_length:
            last_period = summary.rfind('。')
            if last_period > 0:
                summary = summary[:last_period + 1]
                
        return summary

    def generate_news_id(self, url, title):
        """生成新闻唯一ID"""
        # 使用URL和标题的组合生成哈希值作为ID
        id_string = f"{url}_{title}"
        return hashlib.md5(id_string.encode('utf-8')).hexdigest() 