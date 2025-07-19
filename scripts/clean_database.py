#!/usr/bin/env python3
"""
数据库清理脚本
清空爬虫相关的脏数据，为重新爬取做准备
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.debunk import DebunkArticle, RumorReport, ClarificationReport, WeiboDebunk, XinlangDebunk, DebunkContent
from app.models.message import Message
from app.models.news import News
import click
from sqlalchemy import text

# 尝试导入可能不存在的模型
try:
    from app.models.news_data import NewsData, RumorData, SocialMediaData
    HAS_NEWS_DATA_MODELS = True
except ImportError:
    HAS_NEWS_DATA_MODELS = False
    print("警告: news_data 模块不存在，将跳过相关表的清理")

def table_exists(table_name):
    """检查表是否存在"""
    try:
        result = db.session.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
        return result.fetchone() is not None
    except Exception:
        return False

def safe_delete_table(model_class, table_name):
    """安全删除表数据"""
    try:
        if not table_exists(table_name):
            print(f"  - 跳过 {table_name}: 表不存在")
            return 0
        
        count = model_class.query.count()
        model_class.query.delete()
        print(f"  - 清理 {table_name}: {count} 条")
        return count
    except Exception as e:
        print(f"  - 清理 {table_name} 失败: {str(e)}")
        return 0

def clean_debunk_data():
    """清理辟谣相关数据"""
    print("清理辟谣相关数据...")
    
    # 清理关联表（需要先清理，避免外键约束）
    try:
        if table_exists('article_rumor_association'):
            db.session.execute(text("DELETE FROM article_rumor_association"))
            print("  - 清理 article_rumor_association")
    except Exception as e:
        print(f"  - 清理 article_rumor_association 失败: {str(e)}")
    
    try:
        if table_exists('article_clarification_association'):
            db.session.execute(text("DELETE FROM article_clarification_association"))
            print("  - 清理 article_clarification_association")
    except Exception as e:
        print(f"  - 清理 article_clarification_association 失败: {str(e)}")
    
    # 清理各个表
    safe_delete_table(DebunkContent, 'debunk_content')
    safe_delete_table(WeiboDebunk, 'weibo_debunk')
    safe_delete_table(XinlangDebunk, 'xinlang_debunk')
    safe_delete_table(DebunkArticle, 'debunk_article')
    safe_delete_table(RumorReport, 'rumor_report')
    safe_delete_table(ClarificationReport, 'clarification_report')

def clean_message_data():
    """清理消息数据"""
    print("清理消息数据...")
    safe_delete_table(Message, 'message')

def clean_news_data():
    """清理新闻数据"""
    print("清理新闻数据...")
    
    if not HAS_NEWS_DATA_MODELS:
        print("  - 跳过新闻数据清理: 相关模型不存在")
        return
    
    # 清理爬虫新闻数据
    safe_delete_table(NewsData, 'news_data')
    safe_delete_table(RumorData, 'rumor_data')
    safe_delete_table(SocialMediaData, 'social_media_data')
    safe_delete_table(News, 'news')

@click.command()
@click.option('--tables', default='all', help='指定要清理的表: debunk,message,news,all')
@click.option('--confirm', is_flag=True, help='确认执行清理操作')
def main(tables, confirm):
    """数据库清理主函数"""
    
    if not confirm:
        print("警告：此操作将删除数据库中的数据！")
        print("请使用 --confirm 参数确认执行")
        print("可选参数 --tables: debunk,message,news,all")
        return
    
    app = create_app()
    
    with app.app_context():
        try:
            print("开始清理数据库...")
            
            if tables in ['all', 'debunk']:
                clean_debunk_data()
            
            if tables in ['all', 'message']:
                clean_message_data()
            
            if tables in ['all', 'news']:
                clean_news_data()
            
            # 提交事务
            db.session.commit()
            print("数据清理完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"清理失败: {str(e)}")
            print("已回滚所有更改")
            sys.exit(1)

if __name__ == '__main__':
    main()
