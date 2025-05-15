"""数据清洗管道

负责对爬取的数据进行清洗，去除HTML标签、广告内容等
"""

import re
import logging
from scrapy.exceptions import DropItem

# 配置日志
logger = logging.getLogger('data_clean_pipeline')
logger.setLevel(logging.INFO)

class DataCleanPipeline:
    """数据清洗管道，处理爬取的原始数据"""
    
    def __init__(self):
        """初始化清洗管道"""
        # 广告关键词列表
        self.ad_keywords = [
            '广告', '推广', '赞助', '点击购买', '限时优惠',
            '联系电话', '推荐使用', '购买链接', '折扣', '促销',
            '联系我们', '微信号', 'QQ群', '加入我们', '转发有奖'
        ]
        
        # 广告模式正则表达式
        self.ad_patterns = [
            r'([购领][买取][链方地][接式址][：:].+)',
            r'([加关]入?[我官]们?的?[微群].{1,10}[：:].{5,30})',
            r'([联微][系信][方电][式话][：:].{5,15})',
            r'((?:http|https|www).+?(?:\.com|\.cn|\.net))',
            r'([送优][礼惠][：:].+)',
        ]
        
        logger.info("数据清洗管道初始化完成")
    
    def process_item(self, item, spider):
        """处理爬取的项目
        
        Args:
            item: 爬取的项目
            spider: 爬虫实例
            
        Returns:
            item: 处理后的项目
        """
        # 清洗标题
        if 'title' in item and item['title']:
            item['title'] = self.clean_text(item['title'])
            
            # 检查标题是否为空
            if not item['title']:
                raise DropItem(f"标题为空，丢弃项目: {item}")
        else:
            raise DropItem(f"缺少标题，丢弃项目: {item}")
        
        # 清洗内容
        if 'content' in item and item['content']:
            item['content'] = self.clean_text(item['content'])
            item['content'] = self.filter_ads(item['content'])
            
            # 检查内容是否为空
            if not item['content']:
                raise DropItem(f"内容为空，丢弃项目: {item}")
        else:
            raise DropItem(f"缺少内容，丢弃项目: {item}")
            
        # 如果是谣言项目，清洗辟谣内容
        if 'refutation' in item and item['refutation']:
            item['refutation'] = self.clean_text(item['refutation'])
            item['refutation'] = self.filter_ads(item['refutation'])
        
        logger.debug(f"数据清洗完成: {item['title']}")
        return item
    
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
    
    def filter_ads(self, text):
        """过滤广告内容
        
        Args:
            text: 原文内容
            
        Returns:
            str: 过滤后的内容
        """
        # 根据广告关键词拆分文本，然后过滤包含关键词的段落
        paragraphs = re.split(r'\n+', text)
        filtered_paragraphs = []
        
        for para in paragraphs:
            is_ad = False
            
            # 检查是否包含广告关键词
            for keyword in self.ad_keywords:
                if keyword in para:
                    is_ad = True
                    break
            
            # 检查是否匹配广告模式
            if not is_ad:
                for pattern in self.ad_patterns:
                    if re.search(pattern, para):
                        is_ad = True
                        break
            
            # 如果不是广告，保留这个段落
            if not is_ad:
                filtered_paragraphs.append(para)
        
        # 重新连接过滤后的段落
        filtered_text = '\n'.join(filtered_paragraphs)
        return filtered_text 