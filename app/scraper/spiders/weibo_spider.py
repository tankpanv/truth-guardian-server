# """微博爬虫

# 负责从微博平台获取数据
# """

# import json
# import re
# import hashlib
# import logging
# from datetime import datetime
# import time
# from urllib.parse import urlencode

# from app.scraper.spiders.base_spider import BaseSpider
# from app.scraper.items import SocialMediaItem
# from app.scraper import settings

# logger = logging.getLogger('scraper.weibo')

# class WeiboSpider(BaseSpider):
#     """微博爬虫"""
    
#     name = 'weibo_spider'
    
#     # 从配置获取API密钥等信息
#     api_config = settings.TRUTH_GUARDIAN_SETTINGS['API_KEYS']['weibo']
    
#     # 关键词列表，用于搜索
#     keywords = settings.TRUTH_GUARDIAN_SETTINGS['KEYWORDS']
    
#     # 热搜榜API
#     hot_search_url = 'https://weibo.com/ajax/side/hotSearch'
    
#     # 搜索API
#     search_api = 'https://m.weibo.cn/api/container/getIndex?'
    
#     # 详情API
#     detail_api = 'https://m.weibo.cn/statuses/show?id='
    
#     # 评论API
#     comments_api = 'https://m.weibo.cn/comments/hotflow?'
    
#     def __init__(self, *args, **kwargs):
#         super(WeiboSpider, self).__init__(*args, **kwargs)
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
#             'Accept': 'application/json, text/plain, */*',
#             'Accept-Language': 'zh-CN,zh;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#         }
        
#         # 如果API配置中有Cookie，添加到请求头
#         if 'cookie' in self.api_config:
#             self.headers['Cookie'] = self.api_config['cookie']
#             logger.info("已配置Cookie")
#         else:
#             logger.error("未找到Cookie配置，爬虫可能无法正常工作")
        
#         self.max_pages = 5  # 每个关键词最多爬取的页数
#         logger.info(f"微博爬虫初始化完成，关键词列表: {self.keywords}")
    
#     def start_requests(self):
#         """开始请求微博热搜榜"""
#         logger.info(f"开始请求微博热搜榜: {self.hot_search_url}")
#         logger.debug(f"请求头: {self.headers}")
        
#         # 检查必需的Cookie字段
#         required_cookies = ['SUB', 'SUBP', '_T_WM', 'XSRF-TOKEN']
#         cookie_dict = dict(item.split("=") for item in self.headers.get('Cookie', '').split("; "))
#         missing_cookies = [cookie for cookie in required_cookies if cookie not in cookie_dict]
        
#         if missing_cookies:
#             error_msg = f"缺少必需的Cookie字段: {', '.join(missing_cookies)}"
#             logger.error(error_msg)
#             return []
        
#         requests = []
#         try:
#             # 请求热搜榜
#             requests.append({
#                 'url': self.hot_search_url,
#                 'headers': self.headers,
#                 'callback': self.parse_hot_search,
#                 'meta': {
#                     'dont_redirect': True,
#                     'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                     'download_timeout': 30
#                 }
#             })
        
#         # 同时搜索预定义的关键词
#         for keyword in self.keywords:
#             params = {
#                 'containerid': '100103type=1&q=' + keyword,
#                 'page_type': 'searchall'
#             }
#             url = self.search_api + urlencode(params)
#             logger.info(f"开始搜索关键词: {keyword}, URL: {url}")
            
#             requests.append({
#                 'url': url,
#                 'headers': self.headers,
#                 'callback': self.parse_search_results,
#                 'meta': {
#                     'keyword': keyword, 
#                     'page': 1,
#                     'dont_redirect': True,
#                     'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                     'download_timeout': 30
#                 }
#             })
#         except Exception as e:
#             logger.error(f"生成请求时出错: {str(e)}")
#             logger.exception(e)
            
#         return requests
    
#     def handle_error(self, failure):
#         """处理请求错误"""
#         request = failure.request
#         logger.error(f"请求失败: {request.url}")
#         logger.error(f"请求头: {request.headers}")
#         logger.error(f"失败原因: {failure.value}")
        
#         if isinstance(failure, dict):
#             response = failure.get('response')
#             if response:
#                 logger.error(f"HTTP错误状态码: {response.get('status')}")
#                 logger.error(f"响应头: {response.get('headers')}")
#                 logger.error(f"响应内容: {response.get('text', '')[:500]}")  # 记录前500个字符
#         else:
#             logger.error(f"未知错误: {str(failure)}")
#             logger.exception(failure)
    
#     def parse_hot_search(self, response):
#         """解析微博热搜榜"""
#         logger.info("开始解析微博热搜榜响应")
#         logger.debug(f"响应状态码: {response.get('status')}")
#         logger.debug(f"响应头: {response.get('headers')}")
        
#         if response.get('status') != 200:
#             logger.error(f"响应状态码异常: {response.get('status')}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return
        
#         try:
#             data = json.loads(response.get('text', '{}'))
#             logger.debug(f"响应数据: {data}")
            
#             if data.get('ok') != 1:
#                 error_msg = f"微博热搜请求失败: {data}"
#                 logger.error(error_msg)
#                 if 'login' in str(data).lower():
#                     logger.error("Cookie可能已过期或无效")
#                 return
            
#             hot_list = data.get('data', {}).get('realtime', [])
#             if not hot_list:
#                 logger.warning("未获取到热搜数据")
#                 return
                
#             logger.info(f"获取到 {len(hot_list)} 条热搜")
            
#             requests = []
#             for item in hot_list:
#                 keyword = item.get('word', '')
#                 if not keyword:
#                     continue
                    
#                 logger.info(f"处理热搜关键词: {keyword}")
                
#                 params = {
#                     'containerid': '100103type=1&q=' + keyword,
#                     'page_type': 'searchall'
#                 }
#                 url = self.search_api + urlencode(params)
                
#                 requests.append({
#                     'url': url,
#                     'headers': self.headers,
#                     'callback': self.parse_search_results,
#                     'meta': {
#                         'keyword': keyword, 
#                         'page': 1,
#                         'dont_redirect': True,
#                         'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                         'download_timeout': 30
#                     }
#                 })
            
#             return requests
            
#         except json.JSONDecodeError as e:
#             logger.error(f"解析JSON响应失败: {str(e)}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return []
    
#     def parse_search_results(self, response):
#         """解析搜索结果"""
#         logger.info("开始解析搜索结果")
#         logger.debug(f"响应状态码: {response.get('status')}")
        
#         if response.get('status') != 200:
#             logger.error(f"响应状态码异常: {response.get('status')}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return
        
#         try:
#             data = json.loads(response.get('text', '{}'))
#             logger.debug(f"响应数据: {data}")
            
#             if data.get('ok') != 1:
#                 error_msg = f"微博搜索请求失败: {data}"
#                 logger.error(error_msg)
#                 if 'login' in str(data).lower():
#                     logger.error("Cookie可能已过期或无效")
#                 return
            
#             cards = data.get('data', {}).get('cards', [])
#             if not cards:
#                 logger.warning("未获取到搜索结果")
#                 return
            
#             requests = []
#             for card in cards:
#                 mblog = card.get('mblog')
#                 if not mblog:
#                     continue
                
#                 weibo_id = mblog.get('id')
#                 if not weibo_id:
#                     continue
                
#                 logger.info(f"处理微博ID: {weibo_id}")
                
#                 # 请求微博详情
#                 detail_url = self.detail_api + weibo_id
#                 requests.append({
#                     'url': detail_url,
#                     'headers': self.headers,
#                     'callback': self.parse_weibo_detail,
#                     'meta': {
#                         'weibo_id': weibo_id,
#                         'dont_redirect': True,
#                         'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                         'download_timeout': 30
#                     }
#                 })
                
#                 # 请求评论
#                 params = {
#                     'id': weibo_id,
#                     'mid': weibo_id,
#                     'max_id_type': 0
#                 }
#                 comments_url = self.comments_api + urlencode(params)
#                 requests.append({
#                     'url': comments_url,
#                     'headers': self.headers,
#                     'callback': self.parse_comments,
#                     'meta': {
#                         'weibo_id': weibo_id,
#                         'dont_redirect': True,
#                         'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                         'download_timeout': 30
#                     }
#                 })
            
#             # 处理下一页
#             page = response.meta.get('page', 1)
#             keyword = response.meta.get('keyword', '')
            
#             if page < self.max_pages:
#                 params = {
#                     'containerid': '100103type=1&q=' + keyword,
#                     'page_type': 'searchall',
#                     'page': page + 1
#                 }
#                 next_url = self.search_api + urlencode(params)
#                 logger.info(f"请求下一页: {next_url}")
                
#                 requests.append({
#                     'url': next_url,
#                     'headers': self.headers,
#                     'callback': self.parse_search_results,
#                     'meta': {
#                         'keyword': keyword,
#                         'page': page + 1,
#                         'dont_redirect': True,
#                         'handle_httpstatus_list': [301, 302, 403, 404, 500],
#                         'download_timeout': 30
#                     }
#                 })
            
#             return requests
            
#         except json.JSONDecodeError as e:
#             logger.error(f"解析JSON响应失败: {str(e)}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return []
#         except Exception as e:
#             logger.error(f"解析搜索结果出错: {str(e)}")
#             logger.exception(e)
#             return []
    
#     def parse_weibo_detail(self, response):
#         """解析微博详情"""
#         logger.info("开始解析微博详情")
#         logger.debug(f"响应状态码: {response.get('status')}")
        
#         if response.get('status') != 200:
#             logger.error(f"响应状态码异常: {response.get('status')}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return
        
#         try:
#             data = json.loads(response.get('text', '{}'))
#             logger.debug(f"响应数据: {data}")
            
#             if data.get('ok') != 1:
#                 error_msg = f"获取微博详情失败: {data}"
#                 logger.error(error_msg)
#                 if 'login' in str(data).lower():
#                     logger.error("Cookie可能已过期或无效")
#                 return
            
#             weibo_data = {}
#             weibo_info = data.get('data', {})
            
#             # 提取基本信息
#             weibo_data['id'] = weibo_info.get('id')
#             weibo_data['mid'] = weibo_info.get('mid')
#             weibo_data['text'] = weibo_info.get('text', '')
#             weibo_data['source'] = weibo_info.get('source', '')
#             weibo_data['created_at'] = weibo_info.get('created_at', '')
            
#             # 提取用户信息
#             user = weibo_info.get('user', {})
#             weibo_data['user'] = {
#                 'id': user.get('id'),
#                 'screen_name': user.get('screen_name', ''),
#                 'description': user.get('description', ''),
#                 'followers_count': user.get('followers_count', 0),
#                 'friends_count': user.get('friends_count', 0),
#                 'statuses_count': user.get('statuses_count', 0)
#             }
            
#             # 提取统计信息
#             weibo_data['reposts_count'] = weibo_info.get('reposts_count', 0)
#             weibo_data['comments_count'] = weibo_info.get('comments_count', 0)
#             weibo_data['attitudes_count'] = weibo_info.get('attitudes_count', 0)
            
#             # 提取图片信息
#             pics = weibo_info.get('pics', [])
#             weibo_data['pics'] = [pic.get('url') for pic in pics if pic.get('url')]
            
#             # 提取视频信息
#             page_info = weibo_info.get('page_info', {})
#             if page_info.get('type') == 'video':
#                 weibo_data['video'] = {
#                     'url': page_info.get('media_info', {}).get('stream_url', ''),
#                     'duration': page_info.get('media_info', {}).get('duration', 0),
#                     'title': page_info.get('title', '')
#                 }
            
#             # 提取地理位置
#             if weibo_info.get('geo'):
#                 weibo_data['geo'] = {
#                     'type': weibo_info['geo'].get('type'),
#                     'coordinates': weibo_info['geo'].get('coordinates', [])
#                 }
            
#             # 提取转发信息
#             retweeted = weibo_info.get('retweeted_status')
#             if retweeted:
#                 weibo_data['retweeted'] = {
#                     'id': retweeted.get('id'),
#                     'text': retweeted.get('text', ''),
#                     'user': {
#                         'id': retweeted.get('user', {}).get('id'),
#                         'screen_name': retweeted.get('user', {}).get('screen_name', '')
#                     }
#                 }
            
#             # 保存数据
#             self.save_weibo(weibo_data)
#             logger.info(f"成功保存微博: {weibo_data['id']}")
            
#             return []
            
#         except json.JSONDecodeError as e:
#             logger.error(f"解析JSON响应失败: {str(e)}")
#             logger.error(f"响应内容: {response.get('text', '')[:500]}")
#             return []
#         except Exception as e:
#             logger.error(f"解析微博详情出错: {str(e)}")
#             logger.exception(e)
#             return []
    
#     def parse_comments(self, response):
#         """解析评论"""
#         weibo_id = response.meta['weibo_id']
        
#         try:
#             data = json.loads(response.text)
#             if 'ok' not in data or data['ok'] != 1:
#                 logger.error("微博评论请求失败: %s", data)
#                 return
            
#             # 获取评论列表
#             comments = data.get('data', {}).get('data', [])
#             for comment in comments:
#                 comment_id = comment.get('id')
#                 if not comment_id:
#                     continue
                
#                 # 生成唯一ID
#                 unique_id = self.generate_id(f"{weibo_id}_{comment_id}")
                
#                 # 创建评论Item
#                 item = SocialMediaItem()
#                 item['post_id'] = unique_id
#                 item['platform'] = '微博'
#                 item['content'] = self.clean_content(comment.get('text', ''))
#                 item['author'] = comment.get('user', {}).get('screen_name', '')
#                 item['author_id'] = comment.get('user', {}).get('id', '')
#                 item['verified'] = comment.get('user', {}).get('verified', False)
#                 item['followers_count'] = comment.get('user', {}).get('followers_count', 0)
#                 item['parent_id'] = self.generate_id(weibo_id)  # 父微博ID
#                 item['is_comment'] = 1  # 标记为评论
                
#                 # 点赞数
#                 item['likes_count'] = comment.get('like_count', 0)
                
#                 # 提取发布时间
#                 created_at = comment.get('created_at', '')
#                 if created_at:
#                     try:
#                         # 评论时间格式：Sun Jun 07 22:54:26 +0800 2020
#                         item['pub_date'] = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
#                     except Exception:
#                         item['pub_date'] = datetime.now()
#                 else:
#                     item['pub_date'] = datetime.now()
                
#                 item['crawl_time'] = datetime.now()
                
#                 yield item
            
#             # 翻页
#             max_id = data.get('data', {}).get('max_id', 0)
#             if max_id and max_id != response.meta['max_id']:
#                 params = {
#                     'id': weibo_id,
#                     'mid': weibo_id,
#                     'max_id': max_id,
#                     'max_id_type': '0'
#                 }
#                 next_url = self.comments_api + urlencode(params)
#                 yield scrapy.Request(
#                     url=next_url,
#                     headers=self.headers,
#                     callback=self.parse_comments,
#                     meta={'weibo_id': weibo_id, 'max_id': max_id}
#                 )
#         except Exception as e:
#             logger.error("解析微博评论出错: %s", str(e))
    
#     def clean_content(self, content):
#         """清理微博内容"""
#         if not content:
#             return ''
        
#         # 去除HTML标签
#         content = re.sub(r'<[^>]+>', '', content)
        
#         # 去除表情图片链接
#         content = re.sub(r'\[.*?\]', '', content)
        
#         # 去除多余空格和换行
#         content = re.sub(r'\s+', ' ', content).strip()
        
#         return content
    
#     def extract_title(self, content):
#         """从内容提取标题（取前30个字符）"""
#         if not content:
#             return ''
        
#         # 取前30个字符作为标题
#         title = content[:30]
        
#         # 如果有完整句号，截取到第一个句号
#         period_pos = title.find('。')
#         if period_pos > 0:
#             title = title[:period_pos + 1]
        
#         return title
    
#     def generate_id(self, id_str):
#         """生成唯一ID"""
#         return hashlib.md5(f"weibo_{id_str}".encode('utf-8')).hexdigest() 