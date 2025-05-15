"""政府网站爬虫

负责爬取政府官方网站的信息
"""

import re
import json
import hashlib
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

import scrapy
from app.scraper.items import NewsItem
from app.scraper import settings

logger = logging.getLogger('scraper.gov')

class GovSpider(scrapy.Spider):
    """政府网站爬虫"""
    
    name = 'gov_spider'
    allowed_domains = [
        'gov.cn',
        'nhc.gov.cn'
    ]
    
    # 从配置中获取起始URL
    start_urls = settings.TRUTH_GUARDIAN_SETTINGS['SOURCES']['government']
    
    # 关键词列表，用于过滤内容
    keywords = settings.TRUTH_GUARDIAN_SETTINGS['KEYWORDS']
    
    def __init__(self, *args, **kwargs):
        super(GovSpider, self).__init__(*args, **kwargs)
        self.source_mapping = {
            'gov.cn': '中国政府网',
            'nhc.gov.cn': '国家卫健委'
        }
    
    def parse(self, response):
        """解析政府网站首页，提取信息链接"""
        # 提取消息链接
        gov_links = response.css('a[href*="content"]::attr(href), a[href*="zwgk"]::attr(href), a[href*="info"]::attr(href)').getall()
        
        # 去重
        gov_links = list(set(gov_links))
        
        # 构造完整URL
        for link in gov_links:
            # 处理相对URL
            if not link.startswith(('http://', 'https://')):
                link = urljoin(response.url, link)
            
            # 确保链接属于允许的域名
            parsed_url = urlparse(link)
            domain = parsed_url.netloc
            if any(allowed_domain in domain for allowed_domain in self.allowed_domains):
                # 传递源网站信息
                source = next((self.source_mapping[domain] for domain in self.source_mapping if domain in parsed_url.netloc), '政府网站')
                
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_article,
                    meta={'source': source}
                )
    
    def parse_article(self, response):
        """解析政府网站文章页面"""
        # 获取源网站
        source = response.meta.get('source', '政府网站')
        
        # 提取标题
        title = self.extract_title(response)
        if not title:
            logger.warning(f"无法提取标题: {response.url}")
            return
        
        # 提取内容
        content = self.extract_content(response)
        if not content:
            logger.warning(f"无法提取内容: {response.url}")
            return
        
        # 内容关键词过滤，必须包含至少一个关键词
        if not any(keyword in content for keyword in self.keywords):
            logger.info(f"内容不包含关键词，跳过: {response.url}")
            return
        
        # 生成唯一ID
        news_id = self.generate_news_id(response.url, title)
        
        # 提取发布时间
        pub_date = self.extract_pub_date(response)
        
        # 提取发布机构
        author = self.extract_department(response)
        
        # 提取分类
        category = self.extract_category(response)
        
        # 创建NewsItem
        news_item = NewsItem()
        news_item['news_id'] = news_id
        news_item['title'] = title
        news_item['content'] = content
        news_item['source'] = source
        news_item['url'] = response.url
        news_item['pub_date'] = pub_date
        news_item['crawl_time'] = datetime.now()
        news_item['author'] = author
        news_item['category'] = category
        news_item['source_type'] = 'government'
        
        # 提取相关媒体
        media = self.extract_media(response)
        if media:
            news_item['media'] = json.dumps(media)
        
        yield news_item
    
    def extract_title(self, response):
        """提取标题"""
        # 尝试多种选择器
        title = response.css('.article_title::text, .title::text, h1::text, .content-title::text').get()
        if not title:
            title = response.xpath('//title/text()').get()
            if title:
                # 清理标题，去除网站名称等
                title = re.sub(r'[-_|（\(].*$', '', title).strip()
        return title
    
    def extract_content(self, response):
        """提取正文内容"""
        # 尝试多种选择器
        content_selectors = [
            'div#content, div.content, div.article',
            'div.TRS_Editor, div.wrap, div.news-content',
            'div.zwxl-article, div.zw_new, div.pages_content'
        ]
        
        for selector in content_selectors:
            content_element = response.css(selector)
            if content_element:
                # 提取段落文本
                paragraphs = content_element.css('p::text').getall()
                if paragraphs:
                    return '\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        # 如果以上方法都失败，尝试直接提取所有段落
        paragraphs = response.css('p::text').getall()
        if paragraphs:
            return '\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        return None
    
    def extract_pub_date(self, response):
        """提取发布时间"""
        # 尝试多种选择器
        date_selectors = [
            '.date::text, .time::text, .pubDate::text, .sub::text',
            '//span[contains(@class, "date")]/text()',
            '//span[contains(@class, "time")]/text()',
            '//div[contains(@class, "info")]/text()'
        ]
        
        for selector in date_selectors:
            date_text = response.css(selector).get() if selector.startswith('.') else response.xpath(selector).get()
            if date_text:
                # 提取日期部分
                date_match = re.search(r'(\d{4}[-年/]\d{1,2}[-月/]\d{1,2}日?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', date_text)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        # 尝试不同格式
                        if '年' in date_str:
                            if ':' in date_str:
                                return datetime.strptime(date_str, '%Y年%m月%d日 %H:%M')
                            else:
                                return datetime.strptime(date_str, '%Y年%m月%d日')
                        elif '-' in date_str:
                            if ':' in date_str:
                                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            else:
                                return datetime.strptime(date_str, '%Y-%m-%d')
                        elif '/' in date_str:
                            if ':' in date_str:
                                return datetime.strptime(date_str, '%Y/%m/%d %H:%M')
                            else:
                                return datetime.strptime(date_str, '%Y/%m/%d')
                    except Exception as e:
                        logger.warning(f"解析日期出错: {date_str}, {str(e)}")
        
        # 如果无法提取，返回当前时间
        return datetime.now()
    
    def extract_department(self, response):
        """提取发布部门/机构"""
        # 尝试多种选择器
        dept_selectors = [
            '.source::text, .department::text, .publisher::text',
            '//span[contains(@class, "source")]/text()',
            '//span[contains(text(), "来源")]/text()',
            '//span[contains(text(), "发布机构")]/text()'
        ]
        
        for selector in dept_selectors:
            dept_text = response.css(selector).get() if selector.startswith('.') else response.xpath(selector).get()
            if dept_text:
                # 清理文本
                dept_text = dept_text.strip()
                # 提取部门名称
                match = re.search(r'[：:]\s*([^：:]+)$', dept_text)
                if match:
                    return match.group(1).strip()
                return dept_text.replace('来源：', '').replace('发布机构：', '').strip()
        
        return None
    
    def extract_category(self, response):
        """提取政府信息分类"""
        # 从URL路径提取分类
        url_path = urlparse(response.url).path
        path_parts = url_path.strip('/').split('/')
        
        # 常见政府信息分类
        gov_categories = {
            'zhengce': '政策',
            'zhengwu': '政务',
            'zwgk': '政务公开',
            'xinwen': '新闻',
            'tpxw': '图片新闻',
            'tzgg': '通知公告',
            'zcwj': '政策文件',
            'zxft': '在线访谈',
            'hygq': '回应关切'
        }
        
        for part in path_parts:
            if part in gov_categories:
                return gov_categories[part]
        
        # 尝试从页面元素提取
        category_selectors = [
            '.crumbs a::text, .location a::text, .path a::text',
            '//div[contains(@class, "bread")]//a/text()'
        ]
        
        for selector in category_selectors:
            categories = response.css(selector).getall() if selector.startswith('.') else response.xpath(selector).getall()
            if categories and len(categories) > 1:
                # 通常面包屑导航的第二项是分类
                return categories[1].strip()
        
        return '政府信息'
    
    def extract_media(self, response):
        """提取相关媒体（图片/文件）"""
        media = {
            'images': [],
            'files': []
        }
        
        # 提取图片URL
        image_urls = response.css('#content img::attr(src), .content img::attr(src), .article img::attr(src)').getall()
        for url in image_urls:
            if url and not url.startswith(('http://', 'https://')):
                url = urljoin(response.url, url)
            if url:
                media['images'].append(url)
        
        # 提取附件URL
        file_urls = response.css('a[href$=".pdf"]::attr(href), a[href$=".doc"]::attr(href), a[href$=".xls"]::attr(href), a[href$=".xlsx"]::attr(href), a[href$=".docx"]::attr(href)').getall()
        for url in file_urls:
            if url and not url.startswith(('http://', 'https://')):
                url = urljoin(response.url, url)
            if url:
                media['files'].append(url)
        
        return media if media['images'] or media['files'] else None
    
    def generate_news_id(self, url, title):
        """生成唯一ID"""
        # 使用URL和标题的组合生成哈希值作为ID
        id_string = f"{url}_{title}"
        return hashlib.md5(id_string.encode('utf-8')).hexdigest() 