"""
辟谣管理系统数据采集模块

该模块负责从各大社交媒体平台、新闻网站等官方权威渠道实时抓取信息
"""
import logging

# 配置日志
logger = logging.getLogger('scraper')
logger.setLevel(logging.INFO)

# 日志处理器
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(handler) 