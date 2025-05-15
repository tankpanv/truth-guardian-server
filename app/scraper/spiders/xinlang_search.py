import json
import time
from datetime import datetime, timedelta
import requests
import sys
import os
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API配置
API_CONFIG = {
    'base_url': 'http://localhost:5005',
    'username': 'user1',
    'password': 'user1123456'
}

class XinlangSearchSpider:
    def __init__(self):
        """初始化爬虫"""
        self.api_base_url = API_CONFIG['base_url']
        self.token = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
    def login(self):
        """登录获取token"""
        url = f"{self.api_base_url}/api/auth/login"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'username': API_CONFIG['username'],
            'password': API_CONFIG['password']
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
            
    def search(self, keyword, page=1):
        """搜索新浪新闻"""
        url = 'https://search.sina.com.cn/api/search'
        params = {
            'q': keyword,
            'page': page,
            'type': 'news',
            'size': 20,
            'sort': 'time'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f'搜索请求失败: {str(e)}')
            return None
            
    def parse_time(self, time_str):
        """解析时间字符串"""
        now = datetime.now()
        
        # 处理"x小时前"/"x分钟前"的格式
        if '小时前' in time_str:
            hours = int(re.search(r'\d+', time_str).group())
            dt = now - timedelta(hours=hours)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif '分钟前' in time_str:
            minutes = int(re.search(r'\d+', time_str).group())
            dt = now - timedelta(minutes=minutes)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif '昨天' in time_str:
            time_part = re.search(r'(\d{2}:\d{2})', time_str)
            if time_part:
                dt = now - timedelta(days=1)
                return f"{dt.strftime('%Y-%m-%d')} {time_part.group(1)}:00"
        
        # 尝试直接解析完整的时间格式
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # 如果无法解析，返回当前时间
            return now.strftime('%Y-%m-%d %H:%M:%S')

    def parse_response(self, response_data, search_query):
        """解析响应数据"""
        if not response_data or 'data' not in response_data or 'results' not in response_data['data']:
            return []
            
        results = []
        for item in response_data['data']['results']:
            # 构建新闻数据
            news_data = {
                'news_id': str(item.get('id', '')),
                'data_id': str(item.get('docid', '')),
                'title': item.get('title', ''),
                'source_name': item.get('media', '新浪新闻'),
                'link': item.get('url', ''),
                'image_url': item.get('img_url', ''),
                'category': item.get('category', 'cms'),
                'comment_id': str(item.get('comment_id', '')),
                'publish_time': self.parse_time(item.get('datetime', '')),
                'search_query': search_query,
                'status': 'pending'
            }
            results.append(news_data)
            
        return results

    def save_to_api(self, news_data):
        """通过API保存新闻数据"""
        if not self.token:
            logger.error("未提供API认证token")
            return False
            
        url = f"{self.api_base_url}/api/spider/data"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    'source': 'xinlang',
                    'data': news_data
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"成功保存新闻，id: {news_data['news_id']}")
                    return True
                else:
                    logger.warning(f"保存新闻失败，id: {news_data['news_id']}, 错误: {result.get('message')}")
                    return False
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"保存新闻时发生错误: {str(e)}")
            return False

    def run(self, keyword, max_pages=5):
        """运行爬虫"""
        # 先进行登录
        if not self.login():
            logger.error("登录失败，无法继续运行爬虫")
            return
            
        logger.info(f'开始搜索关键词: {keyword}')
        total_saved = 0
        
        for page in range(1, max_pages + 1):
            logger.info(f'正在爬取第 {page} 页')
            response_data = self.search(keyword, page)
            
            if not response_data:
                logger.error(f'第 {page} 页请求失败，停止爬取')
                break
                
            results = self.parse_response(response_data, keyword)
            
            for news_data in results:
                if self.save_to_api(news_data):
                    total_saved += 1
                    
            logger.info(f'第 {page} 页处理完成')
            time.sleep(2)  # 避免请求过于频繁
            
        logger.info(f'爬取完成，共保存 {total_saved} 条新闻')

if __name__ == '__main__':
    spider = XinlangSearchSpider()
    spider.run('谣言', max_pages=5)
