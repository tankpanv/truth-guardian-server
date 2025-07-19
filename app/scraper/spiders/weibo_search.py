import json
import time
from datetime import datetime
import requests
import sys
import os
import logging
from urllib.parse import quote
import re
import html

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_html_text(text):
    """
    清理HTML文本，提取纯文本内容
    保留标点符号，去除HTML标签和特殊字符
    
    Args:
        text (str): 包含HTML标签的文本
        
    Returns:
        str: 清理后的纯文本
    """
    if not text:
        return ""
    
    # 解码HTML实体（如 &lt; &gt; &amp; &quot; &#x等）
    text = html.unescape(text)
    
    # 移除HTML标签，但保留标签内的文本内容
    # 匹配 <标签名 属性> 和 </标签名> 格式
    text = re.sub(r'<[^>]+>', '', text)
    
    # 处理常见的微博特殊标记
    # 移除 @用户名 的链接格式，但保留用户名
    text = re.sub(r'<a[^>]*>@([^<]+)</a>', r'@\1', text)
    
    # 移除话题链接格式，但保留话题内容  
    text = re.sub(r'<a[^>]*>#([^<]+)#</a>', r'#\1#', text)
    
    # 移除链接，但保留链接文本
    text = re.sub(r'<a[^>]*>([^<]+)</a>', r'\1', text)
    
    # 移除图片标签
    text = re.sub(r'<img[^>]*/?>', '', text)
    
    # 移除视频标签
    text = re.sub(r'<video[^>]*>.*?</video>', '', text, flags=re.DOTALL)
    
    # 移除换行符周围的多余空格
    text = re.sub(r'\s*\n\s*', '\n', text)
    
    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)
    
    # 移除行首行尾空格
    text = text.strip()
    
    # 移除多余的换行符（超过2个连续换行符替换为2个）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text
# https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%E8%BE%9F%E8%B0%A3
# https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D%E8%BE%9F%E8%B0%A3&page_type=searchall
# API配置
API_CONFIG = {
    'base_url': 'http://localhost:5005',
    'username': 'user1',
    'password': 'user1123456'
}

# 微博配置
WEIBO_CONFIG = {
    'headers': {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'mweibo-pwa': '1',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%E8%BE%9F%E8%B0%A3',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': 'cf62e9'
    },
    'cookies': {
        'WEIBOCN_FROM': '1110006030',
        '_T_WM': '56436634362',
        'SCF': 'AsJDcLcsDdZbMVo5q1U6Z_kiEavOU7GO_8SnwKhXI6Gqsfi5I6uIlzot2pBzX56SgVKg_ON5xbNI6_7HuVhLqrE.',
        'SUB': '_2A25FCtGEDeRhGeVP41IY9CnEyDmIHXVmZmtMrDV6PUJbktAYLXHYkW1NTRTbknjH7o3Tj4vod6rky8uudNR76Rmi',
        'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9W5cQQlcQ.iBYv6NSS0JZnjU5NHD95Q0eKn71KBN1hefWs4Dqcjji--fiKnEi-iFi--Xi-zRiKy2i--fiK.fi-2ci--fiKysi-i2Us8VIfY0ehet',
        'SSOLoginState': '1745789396',
        'ALF': '1748381396',
        'MLOGIN': '1',
        'XSRF-TOKEN': 'cf62e9',
        'mweibo_short_token': '48563daa66',
        'M_WEIBOCN_PARAMS': 'luicode%3D10000011%26lfid%3D231583%26fid%3D231583%26uicode%3D10000011'
    }
}

class WeiboSearchSpider:
    def __init__(self):
        """初始化爬虫"""
        self.api_base_url = API_CONFIG['base_url']
        self.token = None
        self.headers = WEIBO_CONFIG['headers']
        self.cookies = WEIBO_CONFIG['cookies']
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total': 0,
            'new': 0,
            'existing': 0,
            'error': 0
        }
        
    def login(self):
        """登录获取token"""
        url = f"{self.api_base_url}/api/auth/login"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'username': API_CONFIG['username'],
            'password': API_CONFIG['password']
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    self.token = result['access_token']
                    self.logger.info("登录成功")
                    return True
                else:
                    self.logger.error("登录响应中没有token")
                    return False
            else:
                self.logger.error(f"登录失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"登录请求出错: {str(e)}")
            return False
        
    def search(self, keyword, page=1):
        """搜索微博内容"""
        # URL编码关键词
        encoded_keyword = quote(keyword)
        
        # 直接构造完整URL，不使用params参数
        url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{encoded_keyword}&page_type=searchall'
        
        # 严格按照curl请求的headers
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'mweibo-pwa': '1',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{encoded_keyword}',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'x-xsrf-token': 'cf62e9'
        }
        
        # 严格按照curl请求的cookies
        cookies = {
            'WEIBOCN_FROM': '1110006030',
            '_T_WM': '56436634362',
            'SCF': 'AsJDcLcsDdZbMVo5q1U6Z_kiEavOU7GO_8SnwKhXI6Gqsfi5I6uIlzot2pBzX56SgVKg_ON5xbNI6_7HuVhLqrE.',
            'SUB': '_2A25FCtGEDeRhGeVP41IY9CnEyDmIHXVmZmtMrDV6PUJbktAYLXHYkW1NTRTbknjH7o3Tj4vod6rky8uudNR76Rmi',
            'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9W5cQQlcQ.iBYv6NSS0JZnjU5NHD95Q0eKn71KBN1hefWs4Dqcjji--fiKnEi-iFi--Xi-zRiKy2i--fiK.fi-2ci--fiKysi-i2Us8VIfY0ehet',
            'SSOLoginState': '1745789396',
            'ALF': '1748381396',
            'MLOGIN': '1',
            'XSRF-TOKEN': 'cf62e9',
            'mweibo_short_token': '48563daa66',
            'M_WEIBOCN_PARAMS': 'luicode%3D10000011%26lfid%3D231583%26fid%3D231583%26uicode%3D10000011'
        }
        
        try:
            # 打印完整请求信息用于调试
            self.logger.info(f'请求URL: {url}')
            self.logger.info(f'请求Headers: {headers}')
            
            # 直接发送GET请求，不使用params参数
            response = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                verify=False  # 添加此参数避免SSL验证问题
            )
            
            # 打印响应信息用于调试
            self.logger.info(f'响应状态码: {response.status_code}')
            self.logger.info(f'响应内容: {response.text[:200]}...')  # 只打印前200个字符
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f'搜索请求失败: {str(e)}')
            if hasattr(e, 'response'):
                self.logger.error(f'错误响应内容: {e.response.text}')
            return None

    def parse_response(self, response_data, search_query):
        """解析响应数据"""
        if not response_data or 'data' not in response_data:
            return []
            
        # 检查新的返回结构
        if 'cards' not in response_data['data']:
            self.logger.warning("返回数据结构不包含cards字段")
            return []
            
        results = []
        for card in response_data['data']['cards']:
            try:
                if card.get('card_type') != 9:  # 只处理微博内容卡片
                    continue
                    
                mblog = card.get('mblog')
                if not mblog:
                    continue
                    
                # 提取图片URL列表
                pics = []
                if 'pics' in mblog:
                    for pic in mblog['pics']:
                        if 'large' in pic:
                            pics.append(pic['large']['url'])
                
                # 解析创建时间
                try:
                    created_at = datetime.strptime(mblog['created_at'], '%a %b %d %H:%M:%S %z %Y')
                except:
                    try:
                        # 尝试其他可能的时间格式
                        created_at = datetime.strptime(mblog['created_at'], '%Y-%m-%d %H:%M:%S')
                    except:
                        created_at = datetime.now()
                
                # 清理微博内容文本
                content = clean_html_text(mblog.get('text', ''))
                
                # 构建微博数据
                weibo_data = {
                    'content': content,
                    'weibo_mid_id': str(mblog.get('mid', '')),
                    'weibo_user_id': str(mblog.get('user', {}).get('id', '')),
                    'weibo_user_name': mblog.get('user', {}).get('screen_name', ''),
                    'user_verified': mblog.get('user', {}).get('verified', False),
                    'user_verified_type': mblog.get('user', {}).get('verified_type', -1),
                    'user_verified_reason': mblog.get('user', {}).get('verified_reason', ''),
                    'region': mblog.get('region_name', ''),
                    'attitudes_count': mblog.get('attitudes_count', 0),
                    'comments_count': mblog.get('comments_count', 0),
                    'reposts_count': mblog.get('reposts_count', 0),
                    'pics': ','.join(pics) if pics else None,
                    'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'search_query': search_query,
                    'status': 'pending'
                }
                results.append(weibo_data)
            except Exception as e:
                self.logger.error(f"解析微博数据出错: {str(e)}")
                continue
                
        return results

    def save_to_api(self, data):
        """保存数据到API"""
        url = f"{API_CONFIG['base_url']}/api/spider/data"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'source': 'weibo',
            'data': data
        }
        
        self.logger.info(f"准备保存数据到API: {url}")
        self.logger.info(f"请求Headers: {headers}")
        self.logger.info(f"请求数据: {json.dumps(payload)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            self.logger.info(f"API响应状态码: {response.status_code}")
            self.logger.info(f"API响应内容: {response.text}")
            
            self.stats['total'] += 1
            
            if response.status_code == 200:
                self.stats['new'] += 1
                self.logger.info("数据保存成功")
                return True
            elif response.status_code == 400 and "该微博已存在" in response.text:
                self.stats['existing'] += 1
                self.logger.info("该微博已存在，跳过")
                return True
            else:
                self.stats['error'] += 1
                self.logger.error(f"API请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
                
        except Exception as e:
            self.stats['error'] += 1
            self.logger.error(f"保存数据时发生错误: {str(e)}")
            return False

    def run(self, keyword='辟谣', max_pages=5):
        """运行爬虫"""
        self.logger.info(f"开始运行微博爬虫，关键词: {keyword}, 最大页数: {max_pages}")
        
        if not self.login():
            self.logger.error("登录失败，爬虫终止")
            return
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.info(f"正在爬取第 {page} 页")
                response = self.search(keyword, page)
                
                if not response:
                    self.logger.error(f"获取第 {page} 页数据失败")
                    continue
                
                data_list = self.parse_response(response, keyword)
                for data in data_list:
                    self.save_to_api(data)
                    time.sleep(1)  # 添加延时，避免请求过快
                
                time.sleep(2)  # 页面间延时
            
            self.logger.info("爬虫运行完成")
            self.logger.info(f"统计信息:")
            self.logger.info(f"- 总处理数据: {self.stats['total']}")
            self.logger.info(f"- 新增数据: {self.stats['new']}")
            self.logger.info(f"- 已存在数据: {self.stats['existing']}")
            self.logger.info(f"- 错误数据: {self.stats['error']}")
            
        except Exception as e:
            self.logger.error(f"爬虫运行过程中发生错误: {str(e)}")

if __name__ == '__main__':
    # 创建Flask应用

 

    spider = WeiboSearchSpider()
    spider.run('辟谣', max_pages=5)
