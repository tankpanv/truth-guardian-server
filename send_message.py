#!/usr/bin/env python
"""
辟谣消息推送脚本
定时从数据库获取最新辟谣内容，推送给订阅用户
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import schedule
import time
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API配置
API_CONFIG = {
    'base_url': 'http://localhost:5005',
    'username': 'user1',
    'password': 'user1123456'
}

def get_token():
    """获取JWT令牌"""
    try:
        url = f"{API_CONFIG['base_url']}/api/auth/login"
        data = {
            'username': API_CONFIG['username'],
            'password': API_CONFIG['password']
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('access_token')
    except Exception as e:
        logger.error(f"获取令牌失败: {str(e)}")
        return None

def get_latest_debunk_articles(token, hours=2400):
    """获取最近n小时的辟谣文章"""
    try:
        url = f"{API_CONFIG['base_url']}/api/debunk/articles"
        headers = {'Authorization': f'Bearer {token}'}
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        params = {
            'status': 'published',
            'page': 1,
            'per_page': 10
        }
        
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"API响应状态码: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"API响应错误: {response.text}")
            return []
            
        result = response.json()
        
        # 适配API返回的实际数据结构
        if 'data' in result and 'items' in result['data']:
            articles = result['data']['items']
            
            # 筛选最近n小时内的文章
            recent_articles = []
            for article in articles:
                recent_articles.append(article)
                try:
                    published_at = datetime.strptime(article['published_at'], '%Y-%m-%d %H:%M:%S')
                    if published_at >= start_time:
                        recent_articles.append(article)
                except (ValueError, KeyError) as e:
                    logger.warning(f"处理文章日期时出错: {str(e)}")
                    continue
                    
            logger.info(f"找到{len(recent_articles)}篇最近{hours}小时内的辟谣文章")
            return recent_articles
        else:
            logger.warning(f"API返回的数据结构不符合预期: {result}")
            return []
    except Exception as e:
        logger.error(f"获取辟谣文章失败: {str(e)}")
        return []

def get_user_by_username(token, username):
    """通过用户名获取用户信息
    
    Args:
        token: API访问令牌
        username: 用户名
    """
    try:
        # 使用新的用户搜索API
        url = f"{API_CONFIG['base_url']}/api/users/search"
        headers = {'Authorization': f'Bearer {token}'}
        params = {'username': username}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        if 'data' in result and 'users' in result['data'] and result['data']['users']:
            logger.info(f"找到用户: {username}")
            return result['data']['users']
        else:
            logger.warning(f"未找到用户名为 {username} 的用户")
            return []
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return []

def get_subscribers(token, all_users=False, username=None):
    """获取用户列表
    
    Args:
        token: API访问令牌
        all_users: 是否获取所有用户，True表示获取所有用户，False表示只获取订阅用户
        username: 指定的用户名，如果提供则只返回该用户
    """
    try:
        # 如果指定了用户名，优先通过用户名获取
        if username:
            return get_user_by_username(token, username)
            
        # 使用新的用户管理API
        url = f"{API_CONFIG['base_url']}/api/users"
        headers = {'Authorization': f'Bearer {token}'}
        params = {}
        
        if all_users:
            params['all'] = 'true'
            
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        if 'data' in result and 'users' in result['data']:
            users = result['data']['users']
            logger.info(f"成功获取到 {len(users)} 个用户")
            return users
        else:
            logger.warning("API返回数据格式不符合预期")
            return []
            
    except Exception as e:
        logger.error(f"获取{'所有' if all_users else '订阅'}用户失败: {str(e)}")
        # 返回默认测试用户
        return [{'id': 1, 'user_name': 'user1'}, {'id': 2, 'user_name': 'user2'}]

def push_debunk_message(token, user_id, article):
    """推送辟谣消息给用户"""
    try:
        url = f"{API_CONFIG['base_url']}/api/im/push"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 提取摘要文本
        summary = article['summary']
        # 移除HTML标签获取纯文本摘要
        import re
        summary_text = re.sub(r'<.*?>', '', summary)
        summary_text = summary_text.strip()
        if len(summary_text) > 100:
            summary_text = summary_text[:100] + "..."
        
        data = {
            'receiver_id': int(user_id),  # 确保receiver_id是整数类型
            'title': f"辟谣提醒: {article['title']}",
            'msg_type': 'text',
            'content': f"{summary_text}\n\n点击查看详情: {API_CONFIG['base_url']}/debunk/articles/{article['id']}",
            'priority': 1
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'success' in result and result['success']:
            logger.info(f"成功向用户{user_id}推送辟谣文章《{article['title']}》")
            return True
        else:
            logger.warning(f"推送消息失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        logger.error(f"推送消息失败: {str(e)}")
        return False

def push_debunk_messages(all_users=False, username=None, limit=20):
    """执行推送辟谣消息的主函数
    Args:
        all_users: 是否向所有用户推送，True表示向所有用户推送，False表示只向订阅用户推送
        username: 指定的用户名，如果提供则只向该用户推送
        limit: 本次最多推送多少条辟谣文章
    """
    target = "指定用户" if username else "所有用户" if all_users else "订阅用户"
    logger.info(f"开始执行辟谣消息推送 (目标: {target})")
    
    # 获取token
    token = get_token()
    if not token:
        logger.error("获取认证失败，无法推送辟谣消息")
        return
    
    # 获取最新辟谣文章
    articles = get_latest_debunk_articles(token, hours=24)
    if not articles:
        logger.info("没有最新辟谣文章，跳过推送")
        return
    
    # 限制推送数量
    articles = articles[:limit]
    logger.info(f"本次计划推送 {len(articles)} 条辟谣文章")
    
    # 获取用户列表
    users = get_subscribers(token, all_users, username)
    if not users:
        if username:
            logger.info(f"未找到用户名为 {username} 的用户，跳过推送")
        else:
            logger.info(f"没有{target}，跳过推送")
        return
    
    # 推送消息
    success_count = 0
    for article in articles:
        for user in users:
            user_id = user['id']
            if push_debunk_message(token, user_id, article):
                success_count += 1
    
    logger.info(f"辟谣消息推送完成，成功推送 {success_count} 条消息")

def run_scheduler(all_users=False, username=None, limit=20):
    """运行调度器
    Args:
        all_users: 是否向所有用户推送
        username: 指定的用户名，如果提供则只向该用户推送
        limit: 本次最多推送多少条辟谣文章
    """
    # 设置每2分钟执行一次推送
    import functools
    schedule.every(2).minutes.do(functools.partial(push_debunk_messages, all_users=all_users, username=username, limit=limit))
    
    target = "指定用户" if username else "所有用户" if all_users else "订阅用户"
    logger.info(f"辟谣消息推送调度器已启动（每2分钟执行一次，推送给{target}，每次最多推送{limit}条）")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='辟谣消息推送脚本')
    parser.add_argument('--now', action='store_true', help='立即执行一次推送')
    parser.add_argument('--all-users', action='store_true', help='向所有用户推送（默认只向订阅用户推送）')
    parser.add_argument('--username', type=str, help='指定要推送的用户名')
    parser.add_argument('--limit', type=int, default=20, help='本次最多推送多少条辟谣文章')
    args = parser.parse_args()
    
    if args.now:
        push_debunk_messages(all_users=args.all_users, username=args.username, limit=args.limit)
    else:
        run_scheduler(all_users=args.all_users, username=args.username, limit=args.limit)