"""数据处理服务

负责对爬取的数据进行清洗、去重、分词等预处理
"""

import re
import json
import jieba
import jieba.analyse
import logging
from datetime import datetime
from sqlalchemy import func, and_, or_
from collections import Counter

from app import db
from app.models.news_data import NewsData, RumorData, SocialMediaData, DataProcessLog

# 配置日志
logger = logging.getLogger('data_processor')
logger.setLevel(logging.INFO)

# 加载停用词
STOPWORDS = set()
try:
    with open('app/services/data_processor/stopwords.txt', 'r', encoding='utf-8') as f:
        for line in f:
            STOPWORDS.add(line.strip())
except Exception as e:
    logger.warning(f"加载停用词失败: {str(e)}")

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, app=None):
        """初始化数据处理器
        
        Args:
            app: Flask应用实例，用于获取应用上下文
        """
        self.app = app
        self.stopwords = STOPWORDS
        logger.info("数据处理器初始化完成")
        
        # 加载用户词典
        try:
            jieba.load_userdict('app/services/data_processor/custom_dict.txt')
            logger.info("加载用户词典成功")
        except Exception as e:
            logger.warning(f"加载用户词典失败: {str(e)}")
    
    def clean_text(self, text):
        """清洗文本
        
        Args:
            text: 待清洗的文本
            
        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ""
            
        # 替换HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 替换多余空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 替换特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，、；：""（）《》？！]', '', text)
        
        # 移除空行
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def extract_keywords(self, text, topk=10):
        """提取关键词
        
        Args:
            text: 文本内容
            topk: 提取的关键词数量
            
        Returns:
            list: 关键词列表 [(word, weight), ...]
        """
        # 使用TextRank算法提取关键词
        keywords = jieba.analyse.textrank(text, topK=topk, withWeight=True)
        return keywords
    
    def extract_tags(self, text, topk=5):
        """提取标签
        
        Args:
            text: 文本内容
            topk: 提取的标签数量
            
        Returns:
            list: 标签列表
        """
        # 使用TF-IDF算法提取标签
        tags = jieba.analyse.extract_tags(text, topK=topk)
        return tags
    
    def segment_text(self, text):
        """对文本进行分词
        
        Args:
            text: 待分词的文本
            
        Returns:
            list: 分词结果
        """
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词
        filtered_words = [word for word in words if word not in self.stopwords and len(word.strip()) > 1]
        
        return filtered_words
    
    def generate_summary(self, text, max_length=200):
        """生成摘要
        
        Args:
            text: 原文内容
            max_length: 最大摘要长度
            
        Returns:
            str: 生成的摘要
        """
        # 如果文本长度小于最大长度，直接返回
        if len(text) <= max_length:
            return text
            
        # 按句子切分
        sentences = re.split(r'[。！？；.!?;]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 提取关键词
        keywords = jieba.analyse.textrank(text, topK=10, withWeight=True)
        keyword_dict = {word: weight for word, weight in keywords}
        
        # 计算每个句子的得分
        sentence_scores = []
        for sentence in sentences:
            score = 0
            words = self.segment_text(sentence)
            for word in words:
                if word in keyword_dict:
                    score += keyword_dict[word]
            # 长度归一化
            sentence_scores.append((sentence, score / (len(words) + 1)))
        
        # 排序并选择高分句子
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择前几个高分句子组成摘要
        selected_sentences = []
        current_length = 0
        
        for sentence, _ in sentence_scores:
            if current_length + len(sentence) <= max_length:
                selected_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        # 按原文顺序排列句子
        sentence_order = {sentence: i for i, sentence in enumerate(sentences)}
        selected_sentences.sort(key=lambda s: sentence_order.get(s, 999))
        
        # 连接成摘要
        summary = '。'.join(selected_sentences) + '。'
        
        return summary
    
    def check_duplicate(self, item_type, item_data):
        """检查数据是否重复
        
        Args:
            item_type: 数据类型 ('news', 'rumor', 'social')
            item_data: 数据字典
            
        Returns:
            bool: 是否重复
        """
        try:
            if item_type == 'news':
                # 检查新闻ID是否存在
                if 'news_id' in item_data and item_data['news_id']:
                    exists = NewsData.query.filter_by(news_id=item_data['news_id']).first()
                    if exists:
                        return True
                
                # 检查标题+来源是否存在
                if 'title' in item_data and 'source' in item_data:
                    exists = NewsData.query.filter(
                        NewsData.title == item_data['title'],
                        NewsData.source == item_data['source']
                    ).first()
                    if exists:
                        return True
            
            elif item_type == 'rumor':
                # 检查谣言ID是否存在
                if 'rumor_id' in item_data and item_data['rumor_id']:
                    exists = RumorData.query.filter_by(rumor_id=item_data['rumor_id']).first()
                    if exists:
                        return True
                
                # 检查标题+来源是否存在
                if 'title' in item_data and 'source' in item_data:
                    exists = RumorData.query.filter(
                        RumorData.title == item_data['title'],
                        RumorData.source == item_data['source']
                    ).first()
                    if exists:
                        return True
            
            elif item_type == 'social':
                # 检查帖子ID是否存在
                if 'post_id' in item_data and item_data['post_id']:
                    exists = SocialMediaData.query.filter_by(post_id=item_data['post_id']).first()
                    if exists:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查重复数据时出错: {str(e)}")
            return False
    
    def filter_ads(self, text):
        """过滤广告内容
        
        Args:
            text: 原文内容
            
        Returns:
            str: 过滤后的内容
        """
        # 广告关键词列表
        ad_keywords = [
            '广告', '推广', '赞助', '点击购买', '限时优惠',
            '联系电话', '推荐使用', '购买链接', '折扣', '促销',
            '联系我们', '微信号', 'QQ群', '加入我们', '转发有奖'
        ]
        
        # 广告模式正则表达式
        ad_patterns = [
            r'([购领][买取][链方地][接式址][：:].+)',
            r'([加关]入?[我官]们?的?[微群].{1,10}[：:].{5,30})',
            r'([联微][系信][方电][式话][：:].{5,15})',
            r'((?:http|https|www).+?(?:\.com|\.cn|\.net))',
            r'([送优][礼惠][：:].+)',
        ]
        
        # 根据广告关键词拆分文本，然后过滤包含关键词的段落
        paragraphs = re.split(r'\n+', text)
        filtered_paragraphs = []
        
        for para in paragraphs:
            is_ad = False
            
            # 检查是否包含广告关键词
            for keyword in ad_keywords:
                if keyword in para:
                    is_ad = True
                    break
            
            # 检查是否匹配广告模式
            if not is_ad:
                for pattern in ad_patterns:
                    if re.search(pattern, para):
                        is_ad = True
                        break
            
            # 如果不是广告，保留这个段落
            if not is_ad:
                filtered_paragraphs.append(para)
        
        # 重新连接过滤后的段落
        filtered_text = '\n'.join(filtered_paragraphs)
        return filtered_text
    
    def process_news_data(self, news_id=None, limit=100):
        """处理新闻数据
        
        Args:
            news_id: 指定的新闻ID，为None时处理所有未处理的数据
            limit: 每次处理的最大数量
            
        Returns:
            int: 成功处理的数据数量
        """
        processed_count = 0
        
        try:
            # 创建Flask应用上下文
            if self.app:
                ctx = self.app.app_context()
                ctx.push()
            
            # 查询未处理的数据
            query = NewsData.query.filter_by(processed=False)
            if news_id:
                query = query.filter_by(id=news_id)
            
            news_list = query.limit(limit).all()
            
            for news in news_list:
                try:
                    # 清洗内容
                    if news.content:
                        news.content = self.clean_text(news.content)
                        news.content = self.filter_ads(news.content)
                    
                    # 生成摘要
                    if not news.summary and news.content:
                        news.summary = self.generate_summary(news.content)
                    
                    # 提取标签
                    if news.content and not news.tags:
                        tags = self.extract_tags(news.content)
                        news.tags = json.dumps(tags)
                    
                    # 计算关键词匹配度
                    if news.content:
                        keywords = [kw for kw in settings.TRUTH_GUARDIAN_SETTINGS.get('KEYWORDS', [])]
                        if keywords:
                            matches = sum(1 for kw in keywords if kw in news.content)
                            news.keyword_match = matches / len(keywords)
                    
                    # 标记为已处理
                    news.processed = True
                    news.processed_time = datetime.now()
                    
                    # 记录处理日志
                    log = DataProcessLog(
                        data_type='news',
                        data_id=news.id,
                        process_type='clean_and_extract',
                        status='success',
                        message='数据处理成功'
                    )
                    db.session.add(log)
                    
                    processed_count += 1
                
                except Exception as e:
                    logger.error(f"处理新闻ID {news.id} 时出错: {str(e)}")
                    # 记录错误日志
                    log = DataProcessLog(
                        data_type='news',
                        data_id=news.id,
                        process_type='clean_and_extract',
                        status='error',
                        message=f'处理出错: {str(e)}'
                    )
                    db.session.add(log)
            
            # 提交更改
            db.session.commit()
            logger.info(f"成功处理 {processed_count} 条新闻数据")
            
            # 释放Flask应用上下文
            if self.app:
                ctx.pop()
        
        except Exception as e:
            logger.error(f"批量处理新闻数据时出错: {str(e)}")
            if 'ctx' in locals() and self.app:
                ctx.pop()
        
        return processed_count
    
    def process_rumor_data(self, rumor_id=None, limit=100):
        """处理谣言数据
        
        Args:
            rumor_id: 指定的谣言ID，为None时处理所有未处理的数据
            limit: 每次处理的最大数量
            
        Returns:
            int: 成功处理的数据数量
        """
        processed_count = 0
        
        try:
            # 创建Flask应用上下文
            if self.app:
                ctx = self.app.app_context()
                ctx.push()
            
            # 查询未处理的数据
            query = RumorData.query.filter_by(processed=False)
            if rumor_id:
                query = query.filter_by(id=rumor_id)
            
            rumor_list = query.limit(limit).all()
            
            for rumor in rumor_list:
                try:
                    # 清洗内容
                    if rumor.content:
                        rumor.content = self.clean_text(rumor.content)
                        rumor.content = self.filter_ads(rumor.content)
                    
                    if rumor.refutation:
                        rumor.refutation = self.clean_text(rumor.refutation)
                        rumor.refutation = self.filter_ads(rumor.refutation)
                    
                    # 提取标签
                    if (rumor.content or rumor.refutation) and not rumor.tags:
                        text = (rumor.content or '') + ' ' + (rumor.refutation or '')
                        tags = self.extract_tags(text)
                        rumor.tags = json.dumps(tags)
                    
                    # 标记为已处理
                    rumor.processed = True
                    rumor.processed_time = datetime.now()
                    
                    # 记录处理日志
                    log = DataProcessLog(
                        data_type='rumor',
                        data_id=rumor.id,
                        process_type='clean_and_extract',
                        status='success',
                        message='数据处理成功'
                    )
                    db.session.add(log)
                    
                    processed_count += 1
                
                except Exception as e:
                    logger.error(f"处理谣言ID {rumor.id} 时出错: {str(e)}")
                    # 记录错误日志
                    log = DataProcessLog(
                        data_type='rumor',
                        data_id=rumor.id,
                        process_type='clean_and_extract',
                        status='error',
                        message=f'处理出错: {str(e)}'
                    )
                    db.session.add(log)
            
            # 提交更改
            db.session.commit()
            logger.info(f"成功处理 {processed_count} 条谣言数据")
            
            # 释放Flask应用上下文
            if self.app:
                ctx.pop()
        
        except Exception as e:
            logger.error(f"批量处理谣言数据时出错: {str(e)}")
            if 'ctx' in locals() and self.app:
                ctx.pop()
        
        return processed_count
    
    def process_social_media_data(self, post_id=None, limit=100):
        """处理社交媒体数据
        
        Args:
            post_id: 指定的帖子ID，为None时处理所有未处理的数据
            limit: 每次处理的最大数量
            
        Returns:
            int: 成功处理的数据数量
        """
        processed_count = 0
        
        try:
            # 创建Flask应用上下文
            if self.app:
                ctx = self.app.app_context()
                ctx.push()
            
            # 查询未处理的数据
            query = SocialMediaData.query.filter_by(processed=False)
            if post_id:
                query = query.filter_by(id=post_id)
            
            post_list = query.limit(limit).all()
            
            for post in post_list:
                try:
                    # 清洗内容
                    if post.content:
                        post.content = self.clean_text(post.content)
                        post.content = self.filter_ads(post.content)
                    
                    # 提取标签
                    if post.content and not post.tags:
                        tags = self.extract_tags(post.content)
                        post.tags = json.dumps(tags)
                    
                    # 计算关键词匹配度
                    if post.content:
                        keywords = [kw for kw in settings.TRUTH_GUARDIAN_SETTINGS.get('KEYWORDS', [])]
                        if keywords:
                            matches = sum(1 for kw in keywords if kw in post.content)
                            post.keyword_match = matches / len(keywords)
                    
                    # 计算推荐级别
                    recommendation_level = 0
                    # 认证用户的内容更可信
                    if post.verified_type in ['official', 'media']:
                        recommendation_level += 2
                    # 热度高的内容更值得关注
                    engagement = (post.shares or 0) + (post.comments or 0) + (post.likes or 0)
                    if engagement > 1000:
                        recommendation_level += 1
                    # 关键词匹配度高的内容更相关
                    if post.keyword_match and post.keyword_match > 0.2:
                        recommendation_level += 1
                        
                    post.recommendation_level = min(5, recommendation_level)
                    
                    # 标记为已处理
                    post.processed = True
                    post.processed_time = datetime.now()
                    
                    # 记录处理日志
                    log = DataProcessLog(
                        data_type='social',
                        data_id=post.id,
                        process_type='clean_and_extract',
                        status='success',
                        message='数据处理成功'
                    )
                    db.session.add(log)
                    
                    processed_count += 1
                
                except Exception as e:
                    logger.error(f"处理社交媒体ID {post.id} 时出错: {str(e)}")
                    # 记录错误日志
                    log = DataProcessLog(
                        data_type='social',
                        data_id=post.id,
                        process_type='clean_and_extract',
                        status='error',
                        message=f'处理出错: {str(e)}'
                    )
                    db.session.add(log)
            
            # 提交更改
            db.session.commit()
            logger.info(f"成功处理 {processed_count} 条社交媒体数据")
            
            # 释放Flask应用上下文
            if self.app:
                ctx.pop()
        
        except Exception as e:
            logger.error(f"批量处理社交媒体数据时出错: {str(e)}")
            if 'ctx' in locals() and self.app:
                ctx.pop()
        
        return processed_count
    
    def process_all_data(self, batch_size=100):
        """处理所有未处理的数据
        
        Args:
            batch_size: 每批处理的数据量
            
        Returns:
            dict: 各类型处理的数据数量
        """
        result = {
            'news': 0,
            'rumor': 0,
            'social': 0
        }
        
        # 处理新闻数据
        news_count = self.process_news_data(limit=batch_size)
        result['news'] = news_count
        
        # 处理谣言数据
        rumor_count = self.process_rumor_data(limit=batch_size)
        result['rumor'] = rumor_count
        
        # 处理社交媒体数据
        social_count = self.process_social_media_data(limit=batch_size)
        result['social'] = social_count
        
        return result

# 创建一个全局的数据处理器实例
data_processor = None

def init_data_processor(app=None):
    """初始化数据处理器
    
    Args:
        app: Flask应用实例
        
    Returns:
        DataProcessor: 数据处理器实例
    """
    global data_processor
    if data_processor is None:
        data_processor = DataProcessor(app)
    return data_processor

def get_data_processor():
    """获取数据处理器实例
    
    Returns:
        DataProcessor: 数据处理器实例
    """
    global data_processor
    if data_processor is None:
        data_processor = DataProcessor()
    return data_processor 