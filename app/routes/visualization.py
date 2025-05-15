"""数据可视化路由模块

提供谣言分析和传播数据的可视化接口
"""

import random
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

# 创建蓝图时不指定 url_prefix，在注册时指定
visualization_bp = Blueprint('visualization', __name__)

# 修改路由路径，因为前缀 /api 已经在注册时指定
@visualization_bp.route('/visualization/rumor-analysis', methods=['GET'])
def get_rumor_analysis():
    """获取谣言分析可视化数据
    
    Returns:
        dict: 包含文本分析、情感分析、传播路径和用户行为的数据
    """
    try:
        # 生成过去30天的日期列表
        dates = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30)]
        
        # 构造演示数据
        data = {
            # 文本分析数据
            'text_analysis': {
                'keyword_cloud': [
                    {'word': '疫情', 'weight': 100},
                    {'word': '病毒', 'weight': 85},
                    {'word': '感染', 'weight': 75},
                    {'word': '疫苗', 'weight': 70},
                    {'word': '确诊', 'weight': 65},
                    {'word': '防控', 'weight': 60},
                    {'word': '隔离', 'weight': 55},
                    {'word': '核酸', 'weight': 50}
                ],
                'topic_distribution': [
                    {'topic': '医疗卫生', 'percentage': 35},
                    {'topic': '社会民生', 'percentage': 25},
                    {'topic': '科技', 'percentage': 20},
                    {'topic': '教育', 'percentage': 15},
                    {'topic': '其他', 'percentage': 5}
                ],
                'credibility_scores': [
                    {'category': '可信度高', 'count': 150},
                    {'category': '可信度中等', 'count': 230},
                    {'category': '可信度低', 'count': 120},
                    {'category': '确定为谣言', 'count': 80}
                ]
            },
            
            # 情感分析数据
            'sentiment_analysis': {
                'timeline': {
                    'dates': dates,
                    'positive': [random.randint(20, 100) for _ in range(30)],
                    'neutral': [random.randint(30, 120) for _ in range(30)],
                    'negative': [random.randint(10, 80) for _ in range(30)]
                },
                'platform_sentiment': {
                    'weibo': {'positive': 45, 'neutral': 30, 'negative': 25},
                    'wechat': {'positive': 40, 'neutral': 35, 'negative': 25},
                    'news': {'positive': 50, 'neutral': 30, 'negative': 20}
                }
            },
            
            # 传播路径数据
            'spread_path': {
                'nodes': [
                    {'id': 'source', 'name': '源头', 'type': 'origin'},
                    {'id': 'platform1', 'name': '微博', 'type': 'platform'},
                    {'id': 'platform2', 'name': '微信', 'type': 'platform'},
                    {'id': 'platform3', 'name': '新闻网站', 'type': 'platform'},
                    {'id': 'group1', 'name': '用户群体1', 'type': 'group'},
                    {'id': 'group2', 'name': '用户群体2', 'type': 'group'}
                ],
                'links': [
                    {'source': 'source', 'target': 'platform1', 'value': 100},
                    {'source': 'platform1', 'target': 'group1', 'value': 80},
                    {'source': 'platform1', 'target': 'platform2', 'value': 60},
                    {'source': 'platform2', 'target': 'group2', 'value': 40},
                    {'source': 'platform2', 'target': 'platform3', 'value': 30}
                ]
            },
            
            # 用户行为数据
            'user_behavior': {
                'interaction_stats': {
                    'dates': dates,
                    'shares': [random.randint(50, 200) for _ in range(30)],
                    'comments': [random.randint(100, 300) for _ in range(30)],
                    'reports': [random.randint(10, 50) for _ in range(30)]
                },
                'user_distribution': {
                    'age_groups': {
                        '18-24': 20,
                        '25-34': 35,
                        '35-44': 25,
                        '45-54': 15,
                        '55+': 5
                    },
                    'regions': [
                        {'name': '北京', 'value': 250},
                        {'name': '上海', 'value': 220},
                        {'name': '广东', 'value': 180},
                        {'name': '浙江', 'value': 150},
                        {'name': '江苏', 'value': 140}
                    ]
                }
            },
            
            # 地理分布数据
            'geo_distribution': {
                'regions': [
                    {
                        'name': '北京',
                        'coordinates': [116.407526, 39.904030],
                        'rumor_count': 150,
                        'spread_intensity': 0.8
                    },
                    {
                        'name': '上海',
                        'coordinates': [121.473701, 31.230416],
                        'rumor_count': 130,
                        'spread_intensity': 0.7
                    },
                    {
                        'name': '广州',
                        'coordinates': [113.264434, 23.129162],
                        'rumor_count': 120,
                        'spread_intensity': 0.6
                    }
                ],
                'heatmap_data': [
                    {'lat': 39.904030, 'lng': 116.407526, 'intensity': 0.8},
                    {'lat': 31.230416, 'lng': 121.473701, 'intensity': 0.7},
                    {'lat': 23.129162, 'lng': 113.264434, 'intensity': 0.6}
                ]
            }
        }
        
        return jsonify({
            'code': 200,
            'message': '获取可视化数据成功',
            'data': data
        })
    except Exception as e:
        # 添加错误处理
        return jsonify({
            'code': 500,
            'message': f'获取数据失败: {str(e)}'
        }), 500 