"""数据迁移脚本

将DebunkContent数据转换为DebunkArticle格式，通过API接口创建
"""

import sys
import os
import json
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)

from app import create_app, db
from app.models.debunk import DebunkContent

def has_chinese(text):
    """检查文本是否包含中文字符"""
    if not text:
        return False
    # \u4e00-\u9fff 是中文字符的unicode范围
    return bool(re.search('[\u4e00-\u9fff]', text))

def normalize_title(title):
    """标准化标题，用于重复检查"""
    if not title:
        return ""
    # 去除前后空格，转换为小写，去除多余空白字符
    normalized = re.sub(r'\s+', ' ', title.strip().lower())
    return normalized

def clean_text(text):
    """清洗文本内容，去除HTML标签和URL"""
    if not text:
        return ""
        
    # 去除HTML标签
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    # 去除URL
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, '', text)
    
    # 去除多余空白字符
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def is_valid_content(title, content):
    """检查内容是否有效"""
    clean_title = clean_text(title)
    clean_content = clean_text(content)
    
    # 标题为空则无效
    if not clean_title:
        return False, None, None
        
    # 内容为空则无效
    if not clean_content:
        return False, None, None
        
    # 标题必须包含中文字符
    if not has_chinese(clean_title):
        print(f"标题不包含中文字符: {clean_title}")
        return False, None, None
        
    return True, clean_title, clean_content

def login():
    """登录获取token"""
    url = "http://localhost:5005/api/auth/login"
    data = {
        "username": "user1",
        "password": "user1123456"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求出错: {str(e)}")
        return None

def get_existing_titles(token):
    """获取已存在的文章标题"""
    url = "http://localhost:5005/api/debunk/articles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    existing_titles = set()
    page = 1
    
    try:
        while True:
            params = {
                'page': page,
                'per_page': 100,  # 每页最多100条
                'status': 'all'   # 获取所有状态的文章
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"获取文章列表失败: {response.text}")
                break
                
            data = response.json()
            
            # 检查数据结构
            if 'data' in data and 'items' in data['data']:
                articles = data['data']['items']
                if not articles:  # 没有更多数据
                    break
                    
                for article in articles:
                    title = article.get('title', '').strip()
                    if title:
                        normalized_title = normalize_title(title)
                        if normalized_title:
                            existing_titles.add(normalized_title)
                        
                print(f"已获取第{page}页文章标题，共{len(articles)}条")
                page += 1
                
                # 检查是否还有更多页
                if page > data['data'].get('pages', 1):
                    break
            else:
                print(f"API返回数据结构不符合预期: {data}")
                break
                
    except Exception as e:
        print(f"获取已存在文章标题时出错: {str(e)}")
        
    print(f"总共获取到{len(existing_titles)}个已存在的文章标题")
    return existing_titles

def convert_content_to_article_data(content):
    """将DebunkContent转换为文章数据格式"""
    try:
        # 如果content是字典，直接使用字典访问
        if isinstance(content, dict):
            content_dict = content
        else:
            # 如果是SQLAlchemy模型实例，转换为字典
            content_dict = content.__dict__
            content_dict.pop('_sa_instance_state', None)  # 移除SQLAlchemy的内部属性

        # 获取原始标题和内容
        title = content_dict.get('title') or f"来自{content_dict.get('source', '未知来源')}的内容"
        content_text = str(content_dict.get('content', ''))
        
        # 检查内容是否有效
        is_valid, clean_title, clean_content = is_valid_content(title, content_text)
        if not is_valid:
            print(f"内容无效 - 原始标题: {title}")
            return None

        # 处理images字段
        image_urls = []
        images = content_dict.get('images')
        if images:
            if isinstance(images, str):
                image_urls = [url.strip() for url in images.split(',') if url.strip()]
            elif isinstance(images, (list, tuple)):
                image_urls = images

        # 构建API请求数据
        article_data = {
            'title': clean_title,
            'content': clean_content,
            'source': str(content_dict.get('source', '')),
            'summary': '',  # API要求的字段
            'tags': [],  # API要求的字段
            'rumor_reports': [],  # API要求的字段
            'clarification_reports': [],  # API要求的字段
            'meta_info': {  # 额外信息存储在元数据中
                'author': str(content_dict.get('author_name', '')),
                'region': str(content_dict.get('region', '')),
                'image_urls': image_urls,
                'url': str(content_dict.get('link', '')),
                'interaction_info': {
                    'attitudes_count': int(content_dict.get('attitudes_count', 0) or 0),
                    'comments_count': int(content_dict.get('comments_count', 0) or 0),
                    'reposts_count': int(content_dict.get('reposts_count', 0) or 0)
                },
                'origin_info': {
                    'content_id': str(content_dict.get('content_id', '') or ''),
                    'author_id': str(content_dict.get('author_id', '') or ''),
                    'author_verified': bool(content_dict.get('author_verified', False)),
                    'search_query': str(content_dict.get('search_query', '') or ''),
                    'origin_content': str(content_dict.get('origin_content', '') or '')
                }
            }
        }

        return article_data
    except Exception as e:
        print(f"转换数据时出错: {str(e)}")
        print(f"原始数据: {content_dict}")
        raise

def create_article_via_api(token, article_data):
    """通过API创建文章"""
    url = "http://localhost:5005/api/debunk/articles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=article_data, headers=headers)
        if response.status_code == 201:
            return response.json().get('article_id')
        else:
            print(f"创建文章失败: {response.text}")
            return None
    except Exception as e:
        print(f"API请求出错: {str(e)}")
        return None

def migrate_data():
    """迁移数据"""
    app = create_app()
    with app.app_context():
        try:
            # 登录获取token
            token = login()
            if not token:
                print("登录失败，无法继续迁移")
                return

            # 获取已存在的文章标题
            print("正在获取已存在的文章标题...")
            existing_titles = get_existing_titles(token)
            print(f"已获取到 {len(existing_titles)} 个已存在的文章标题")

            # 获取所有DebunkContent数据
            contents = DebunkContent.query.all()
            print(f"找到 {len(contents)} 条数据需要迁移")
            
            success_count = 0
            error_count = 0
            skip_count = 0
            duplicate_count = 0
            
            for content in contents:
                try:
                    # 转换数据格式
                    article_data = convert_content_to_article_data(content)
                    
                    # 如果数据无效，跳过
                    if not article_data:
                        skip_count += 1
                        continue
                    
                    # 检查标题是否已存在
                    title = article_data.get('title', '').strip()
                    normalized_title = normalize_title(title)
                    if normalized_title in existing_titles:
                        duplicate_count += 1
                        print(f"标题重复，跳过: {title}")
                        continue
                    
                    # 通过API创建文章
                    article_id = create_article_via_api(token, article_data)
                    
                    if article_id:
                        success_count += 1
                        # 将新创建的标题添加到已存在列表，避免后续重复
                        existing_titles.add(normalized_title)
                        print(f"成功创建第 {success_count} 条数据，ID: {article_id}, 标题: {title}")
                    else:
                        error_count += 1
                        print(f"创建失败: {content.id}")
                    
                    # 添加延时避免请求过快
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_count += 1
                    print(f"处理数据时出错 {content.id}: {str(e)}")
                    continue
            
            print("\n迁移完成:")
            print(f"- 成功: {success_count}")
            print(f"- 失败: {error_count}")
            print(f"- 跳过(无效): {skip_count}")
            print(f"- 跳过(重复): {duplicate_count}")
            print(f"- 总计: {len(contents)}")
            
        except Exception as e:
            print(f"迁移过程中出错: {str(e)}")

if __name__ == '__main__':
    migrate_data() 