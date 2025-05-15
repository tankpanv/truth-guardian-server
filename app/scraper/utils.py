"""爬虫工具类

提供爬虫相关的辅助函数
"""

import re
import json
import hashlib
import logging
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# 配置日志
logger = logging.getLogger('scraper_utils')
logger.setLevel(logging.INFO)

class ScraperUtils:
    """爬虫辅助工具类"""
    
    @staticmethod
    def clean_url(url, base_url=None):
        """清理URL
        
        Args:
            url: 需要清理的URL
            base_url: 基础URL，用于转换相对URL
            
        Returns:
            str: 清理后的URL
        """
        if not url:
            return None
            
        # 处理相对URL
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
            
        # 去除URL中的查询参数和片段
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        return clean_url
    
    @staticmethod
    def extract_text(html, selector=None):
        """从HTML中提取文本
        
        Args:
            html: HTML字符串
            selector: CSS选择器，为None时提取所有文本
            
        Returns:
            str: 提取的文本
        """
        if not html:
            return ""
            
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.extract()
            
        if selector:
            elements = soup.select(selector)
            if elements:
                text = " ".join([elem.get_text() for elem in elements])
            else:
                text = ""
        else:
            # 获取所有文本
            text = soup.get_text()
            
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    @staticmethod
    def generate_id(content, prefix=''):
        """生成唯一ID
        
        Args:
            content: 用于生成ID的内容
            prefix: ID前缀
            
        Returns:
            str: 生成的唯一ID
        """
        # 确保内容是字符串
        if not isinstance(content, str):
            content = str(content)
            
        # 使用SHA256生成哈希值
        hash_object = hashlib.sha256(content.encode('utf-8'))
        hex_dig = hash_object.hexdigest()
        
        # 添加前缀
        if prefix:
            return f"{prefix}_{hex_dig[:16]}"
        else:
            return hex_dig[:16]
            
    @staticmethod
    def parse_date(date_str, formats=None):
        """解析日期字符串
        
        Args:
            date_str: 日期字符串
            formats: 日期格式列表
            
        Returns:
            datetime: 解析后的日期时间对象
        """
        if not date_str:
            return None
            
        # 清理日期字符串
        date_str = re.sub(r'发布时间[：:]|\s+来源[：:].*$', '', date_str).strip()
        
        # 默认日期格式
        if formats is None:
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y年%m月%d日 %H:%M:%S',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d'
            ]
            
        # 尝试解析日期
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # 尝试匹配常见模式
        patterns = [
            # 2023年10月1日
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # 2023-10-01
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # 10月1日
            (r'(\d{1,2})月(\d{1,2})日', lambda m: datetime(datetime.now().year, int(m.group(1)), int(m.group(2)))),
            # 昨天 12:30
            (r'昨天\s*(\d{1,2}):(\d{1,2})', lambda m: datetime.now().replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)),
            # 今天 12:30
            (r'今天\s*(\d{1,2}):(\d{1,2})', lambda m: datetime.now().replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)),
        ]
        
        for pattern, date_func in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    return date_func(match)
                except ValueError:
                    continue
                    
        logger.warning(f"无法解析日期: {date_str}")
        return datetime.now()
    
    @staticmethod
    def extract_images(html, base_url=None):
        """提取HTML中的图片
        
        Args:
            html: HTML字符串
            base_url: 基础URL，用于转换相对URL
            
        Returns:
            list: 图片URL列表
        """
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'lxml')
        images = []
        
        # 提取所有img标签
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # 处理相对URL
                if base_url and not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                images.append(src)
                
        return images
    
    @staticmethod
    def check_api_connection(api_url, timeout=5):
        """检查API连接
        
        Args:
            api_url: API的URL
            timeout: 超时时间(秒)
            
        Returns:
            bool: 连接是否成功
        """
        try:
            response = requests.get(api_url, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False 