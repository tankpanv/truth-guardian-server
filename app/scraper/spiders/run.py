import os
import sys

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.scraper.spiders.weibo_search import WeiboSearchSpider
from app.scraper.spiders.xinlang_search import XinlangSearchSpider

def create_app():
    app = Flask(__name__)
    
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'mysql://root:root@localhost/truth_guardian')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def init_db(app):
    db = SQLAlchemy()
    db.init_app(app)
    return db

def main():
    app = create_app()
    db = init_db(app)
    
    with app.app_context():
        # 确保所有表都已创建
        db.create_all()
        
        # 运行微博爬虫
        weibo_spider = WeiboSearchSpider()
        keywords = ['辟谣', '谣言']
        for keyword in keywords:
            weibo_spider.run(keyword, max_pages=5)
            
        # 运行新浪爬虫
        xinlang_spider = XinlangSearchSpider()
        for keyword in keywords:
            xinlang_spider.run(keyword, max_pages=5)

if __name__ == '__main__':
    main()