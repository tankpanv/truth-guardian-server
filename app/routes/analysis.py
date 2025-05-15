"""数据分析路由模块

分析爬虫数据并生成可视化所需的数据格式
"""

from flask import Blueprint, jsonify
from app.models.debunk import DebunkContent, WeiboDebunk, XinlangDebunk
from app import db
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from collections import Counter
import jieba
import jieba.analyse
from flask_jwt_extended import jwt_required

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

# 创建一个不带参数的jwt_required实例


def extract_keywords(texts, top_n=100):
    """提取文本关键词"""
    combined_text = ' '.join(texts)
    keywords = jieba.analyse.extract_tags(combined_text, topK=top_n, withWeight=True)
    return [{'word': word, 'weight': int(weight * 100)} for word, weight in keywords]

def analyze_sentiment(status):
    """简单的情感分析"""
    if status == 'verified':
        return 'positive'
    elif status == 'false':
        return 'negative'
    return 'neutral'

@analysis_bp.route('/visualization-data', methods=['GET'])

def get_visualization_data():
    """生成可视化数据"""
    try:
        # 获取过去30天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = [(end_date - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30)]

        # 获取所有内容
        contents = DebunkContent.query.filter(
            DebunkContent.created_at >= start_date
        ).all()

        # 文本分析
        all_contents = [c.content for c in contents if c.content]
        keyword_cloud = extract_keywords(all_contents)

        # 话题分布（基于source统计）
        source_counts = Counter(c.source for c in contents)
        topic_distribution = [
            {'topic': source, 'percentage': (count / len(contents)) * 100}
            for source, count in source_counts.items()
        ]

        # 可信度分析
        status_counts = Counter(c.status for c in contents)
        credibility_scores = [
            {'category': '可信度高', 'count': status_counts.get('verified', 0)},
            {'category': '待核实', 'count': status_counts.get('pending', 0)},
            {'category': '确定为谣言', 'count': status_counts.get('false', 0)}
        ]

        # 情感分析时间线数据
        daily_sentiments = {date: {'positive': 0, 'neutral': 0, 'negative': 0} for date in dates}
        for content in contents:
            date = content.created_at.strftime('%Y-%m-%d')
            if date in daily_sentiments:
                sentiment = analyze_sentiment(content.status)
                daily_sentiments[date][sentiment] += 1

        # 平台情感分布
        platform_sentiment = {
            'weibo': {'positive': 0, 'neutral': 0, 'negative': 0},
            'xinlang': {'positive': 0, 'neutral': 0, 'negative': 0}
        }
        for content in contents:
            sentiment = analyze_sentiment(content.status)
            if content.source in platform_sentiment:
                platform_sentiment[content.source][sentiment] += 1

        # 用户行为数据
        daily_interactions = {date: {'shares': 0, 'comments': 0, 'reports': 0} for date in dates}
        for content in contents:
            date = content.created_at.strftime('%Y-%m-%d')
            if date in daily_interactions:
                daily_interactions[date]['shares'] += content.reposts_count or 0
                daily_interactions[date]['comments'] += content.comments_count or 0
                daily_interactions[date]['reports'] += content.attitudes_count or 0

        # 地理分布
        region_counts = Counter(c.region for c in contents if c.region)
        top_regions = region_counts.most_common(10)
        
        # 构建返回数据
        data = {
            'text_analysis': {
                'keyword_cloud': keyword_cloud[:50],  # 限制关键词数量
                'topic_distribution': topic_distribution,
                'credibility_scores': credibility_scores
            },
            'sentiment_analysis': {
                'timeline': {
                    'dates': dates,
                    'positive': [daily_sentiments[date]['positive'] for date in dates],
                    'neutral': [daily_sentiments[date]['neutral'] for date in dates],
                    'negative': [daily_sentiments[date]['negative'] for date in dates]
                },
                'platform_sentiment': platform_sentiment
            },
            'user_behavior': {
                'interaction_stats': {
                    'dates': dates,
                    'shares': [daily_interactions[date]['shares'] for date in dates],
                    'comments': [daily_interactions[date]['comments'] for date in dates],
                    'reports': [daily_interactions[date]['reports'] for date in dates]
                }
            },
            'geo_distribution': {
                'regions': [
                    {
                        'name': region,
                        'value': count
                    } for region, count in top_regions
                ]
            }
        }

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': data
        })

    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@analysis_bp.route('/stats/daily', methods=['GET'])

def get_daily_stats():
    """获取每日统计数据"""
    try:
        # 获取过去30天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 按日期和来源统计数据
        daily_stats = db.session.query(
            func.date(DebunkContent.created_at).label('date'),
            DebunkContent.source,
            func.count(DebunkContent.id).label('count')
        ).filter(
            DebunkContent.created_at >= start_date
        ).group_by(
            func.date(DebunkContent.created_at),
            DebunkContent.source
        ).all()
        
        # 格式化数据
        stats = {}
        for date, source, count in daily_stats:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in stats:
                stats[date_str] = {'weibo': 0, 'xinlang': 0}
            stats[date_str][source] = count
            
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500

@analysis_bp.route('/stats/platform', methods=['GET'])

def get_platform_stats():
    """获取平台统计数据"""
    try:
        # 统计各平台的数据量和状态分布
        platform_stats = db.session.query(
            DebunkContent.source,
            DebunkContent.status,
            func.count(DebunkContent.id).label('count')
        ).group_by(
            DebunkContent.source,
            DebunkContent.status
        ).all()
        
        # 格式化数据
        stats = {}
        for source, status, count in platform_stats:
            if source not in stats:
                stats[source] = {'total': 0, 'status': {}}
            stats[source]['total'] += count
            stats[source]['status'][status] = count
            
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': str(e)
        }), 500 