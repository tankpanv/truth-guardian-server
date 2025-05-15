#!/usr/bin/env python3
"""爬虫运行脚本

用于手动启动爬虫和查询爬虫数据
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import json

# 设置环境变量
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import create_app
from app.scraper.crawler import init_crawler, get_crawler_manager
from app.services.data_processor.processor import init_data_processor
from app.models.news_data import NewsData, RumorData, SocialMediaData, DataProcessLog

# 创建应用实例
app = create_app()

def start_crawler(spider_name=None):
    """启动爬虫
    
    Args:
        spider_name: 爬虫名称，为None时启动所有爬虫
    """
    with app.app_context():
        # 初始化爬虫管理器
        crawler_manager = init_crawler(app)
        
        if spider_name:
            # 启动指定爬虫
            if spider_name not in crawler_manager.spiders:
                available_spiders = list(crawler_manager.spiders.keys())
                print(f"错误: 未找到爬虫 '{spider_name}'")
                print(f"可用爬虫: {', '.join(available_spiders)}")
                return
            
            print(f"正在启动爬虫: {spider_name}")
            crawler_manager.start_crawler(spider_name)
        else:
            # 启动所有爬虫
            print("正在启动所有爬虫...")
            crawler_manager.crawl_all()

def process_data():
    """处理爬虫数据"""
    with app.app_context():
        # 初始化数据处理器
        data_processor = init_data_processor(app)
        
        print("开始处理爬虫数据...")
        result = data_processor.process_all_data(batch_size=50)
        
        print(f"处理完成! 新闻: {result['news']}条, 谣言: {result['rumor']}条, 社交媒体: {result['social']}条")

def query_data(data_type, limit=10, days=None, keywords=None):
    """查询爬虫数据
    
    Args:
        data_type: 数据类型 (news/rumor/social)
        limit: 返回的数据条数
        days: 查询最近几天的数据
        keywords: 关键词过滤
    """
    with app.app_context():
        if data_type == 'news':
            query = NewsData.query
        elif data_type == 'rumor':
            query = RumorData.query
        elif data_type == 'social':
            query = SocialMediaData.query
        else:
            print(f"错误: 未知数据类型 '{data_type}'")
            print("可用类型: news, rumor, social")
            return
        
        # 按最近几天过滤
        if days:
            start_date = datetime.now() - timedelta(days=days)
            query = query.filter(NewsData.crawl_time >= start_date if data_type == 'news' else 
                                RumorData.crawl_time >= start_date if data_type == 'rumor' else
                                SocialMediaData.crawl_time >= start_date)
        
        # 按关键词过滤
        if keywords:
            if data_type == 'news':
                query = query.filter(NewsData.title.contains(keywords) | NewsData.content.contains(keywords))
            elif data_type == 'rumor':
                query = query.filter(RumorData.title.contains(keywords) | RumorData.content.contains(keywords))
            else:
                query = query.filter(SocialMediaData.content.contains(keywords))
        
        # 按爬取时间倒序排列
        if data_type == 'news':
            query = query.order_by(NewsData.crawl_time.desc())
        elif data_type == 'rumor':
            query = query.order_by(RumorData.crawl_time.desc())
        else:
            query = query.order_by(SocialMediaData.crawl_time.desc())
        
        # 限制返回条数
        results = query.limit(limit).all()
        
        # 输出结果
        print(f"\n查询到 {len(results)} 条{data_type}数据:")
        for i, item in enumerate(results):
            if data_type == 'news':
                print(f"\n{i+1}. {item.title} ({item.source})")
                print(f"   发布时间: {item.pub_date}")
                print(f"   链接: {item.url}")
                print(f"   摘要: {item.summary[:100]}..." if item.summary and len(item.summary) > 100 else f"   摘要: {item.summary}")
            elif data_type == 'rumor':
                print(f"\n{i+1}. {item.title} ({item.source})")
                print(f"   发布时间: {item.pub_date}")
                print(f"   辟谣来源: {item.refutation_source}")
                print(f"   辟谣内容: {item.refutation[:100]}..." if item.refutation and len(item.refutation) > 100 else f"   辟谣内容: {item.refutation}")
            else:
                print(f"\n{i+1}. {item.platform} - {item.username}")
                print(f"   发布时间: {item.pub_date}")
                print(f"   链接: {item.url}")
                print(f"   内容: {item.content[:100]}..." if len(item.content) > 100 else f"   内容: {item.content}")
                print(f"   互动: 转发 {item.shares}, 评论 {item.comments}, 点赞 {item.likes}")

def show_stats():
    """显示爬虫数据统计"""
    with app.app_context():
        news_count = NewsData.query.count()
        rumor_count = RumorData.query.count()
        social_count = SocialMediaData.query.count()
        
        last_news = NewsData.query.order_by(NewsData.crawl_time.desc()).first()
        last_rumor = RumorData.query.order_by(RumorData.crawl_time.desc()).first()
        last_social = SocialMediaData.query.order_by(SocialMediaData.crawl_time.desc()).first()
        
        print("\n爬虫数据统计:")
        print(f"新闻数据: {news_count} 条")
        print(f"谣言数据: {rumor_count} 条")
        print(f"社交媒体数据: {social_count} 条")
        print(f"总计: {news_count + rumor_count + social_count} 条")
        
        print("\n最近爬取时间:")
        print(f"新闻数据: {last_news.crawl_time if last_news else '无数据'}")
        print(f"谣言数据: {last_rumor.crawl_time if last_rumor else '无数据'}")
        print(f"社交媒体数据: {last_social.crawl_time if last_social else '无数据'}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='爬虫运行和数据查询工具')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 启动爬虫
    run_parser = subparsers.add_parser('run', help='启动爬虫')
    run_parser.add_argument('spider', nargs='?', help='爬虫名称 (news/government/weibo)，不指定则启动所有爬虫')
    
    # 处理数据
    process_parser = subparsers.add_parser('process', help='处理爬虫数据')
    
    # 查询数据
    query_parser = subparsers.add_parser('query', help='查询爬虫数据')
    query_parser.add_argument('type', choices=['news', 'rumor', 'social'], help='数据类型')
    query_parser.add_argument('-l', '--limit', type=int, default=10, help='返回条数 (默认: 10)')
    query_parser.add_argument('-d', '--days', type=int, help='最近几天的数据')
    query_parser.add_argument('-k', '--keywords', help='关键词过滤')
    
    # 显示统计
    stats_parser = subparsers.add_parser('stats', help='显示数据统计')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        start_crawler(args.spider)
    elif args.command == 'process':
        process_data()
    elif args.command == 'query':
        query_data(args.type, args.limit, args.days, args.keywords)
    elif args.command == 'stats':
        show_stats()
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 