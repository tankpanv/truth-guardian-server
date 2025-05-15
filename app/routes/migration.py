"""数据迁移路由模块

提供数据迁移相关的API接口
"""

from flask import Blueprint, jsonify
from app.models.debunk import DebunkContent, DebunkArticle
from app import db
from flask_jwt_extended import jwt_required
import json
from datetime import datetime
from sqlalchemy import func

migration_bp = Blueprint('migration', __name__, url_prefix='/api/migration')

# 创建一个不带参数的jwt_required实例
jwt_required_without_optional = jwt_required()

def convert_content_to_article(content):
    """将DebunkContent转换为DebunkArticle格式"""
    article_data = {
        'title': content.title or f"来自{content.source}的内容",
        'content': content.content,
        'summary': content.content[:500] if content.content else '',  # 使用内容前500字作为摘要
        'source': content.source,
        'author_id': 1,  # 设置默认作者ID为1
        'status': content.status or 'published',
        'tags': '',  # 初始化为空标签
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'published_at': datetime.now()
    }
    return DebunkArticle(**article_data)

@migration_bp.route('/content-to-article', methods=['POST'])
@jwt_required_without_optional
def migrate_content_to_article():
    """将DebunkContent数据迁移到DebunkArticle"""
    try:
        # 获取所有DebunkContent数据
        contents = DebunkContent.query.all()
        
        stats = {
            'total': len(contents),
            'success': 0,
            'skipped': 0,
            'error': 0
        }
        
        error_details = []
        
        for content in contents:
            try:
                # 检查是否已存在
                existing = DebunkArticle.query.filter_by(
                    source=content.source,
                    title=content.title
                ).first()
                
                if existing:
                    stats['skipped'] += 1
                    continue
                
                # 转换并保存数据
                article = convert_content_to_article(content)
                db.session.add(article)
                stats['success'] += 1
                
                # 每100条提交一次
                if stats['success'] % 100 == 0:
                    db.session.commit()
                    
            except Exception as e:
                stats['error'] += 1
                error_details.append({
                    'content_id': content.id,
                    'error': str(e)
                })
                continue
        
        # 提交剩余的更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'stats': stats,
                'error_details': error_details
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@migration_bp.route('/stats', methods=['GET'])
@jwt_required_without_optional
def get_migration_stats():
    """获取数据迁移统计信息"""
    try:
        content_count = DebunkContent.query.count()
        article_count = DebunkArticle.query.count()
        
        # 按来源统计
        content_by_source = db.session.query(
            DebunkContent.source,
            func.count(DebunkContent.id)
        ).group_by(DebunkContent.source).all()
        
        article_by_source = db.session.query(
            DebunkArticle.source,
            func.count(DebunkArticle.id)
        ).group_by(DebunkArticle.source).all()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'total': {
                    'content': content_count,
                    'article': article_count
                },
                'by_source': {
                    'content': dict(content_by_source),
                    'article': dict(article_by_source)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500 