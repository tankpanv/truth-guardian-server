import json
import os
from datetime import datetime
import concurrent.futures
import random
import re
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

from model.article import ArticleContent
from curl2pyreqs.ulti import parseCurlString,parseCurlCommand
from spider.toutiao_search.toutiao_util import parse_toutiao_page_id
from utils.utils import convert_text_count_to_int,get_full_url
from spider.toutiao_search.detail_page import ToutiaoDetailPage

import time

# 搜索关键词映射
query_map = {
    'burning_toutiao_article': '谣言辟谣,官方辟谣,热点辟谣,网络谣言,权威辟谣,真相还原,事实核查,谣言粉碎',
    'burning_toutiao_game_video': '辟谣视频,谣言揭秘,真相大白,事实真相,辟谣澄清',
    'burning_toutiao_music_video': '辟谣短视频,谣言终结者,真相时刻,事实真相'
}

print("搜索关键词配置:")
for key, value in query_map.items():
    print(f"{key}: {value}")

def start_get_toutiao_mobile_articles_out(source:str, search_type='all'):
    """启动头条文章爬取"""
    if source == '':
        print('source is empty')
        return
        
   
    # 创建爬虫实例
    toutiao_crawler = ToutiaoMainListPage(None, source=source)
    toutiao_crawler.start_get_toutiao_list_page(search_type)

class ToutiaoMainListPage:
    def __init__(self, driver, source:str) -> None:
        self.driver = driver
       
        self.cache_dir = 'cache_dir/toutiao'
        self.cookies = []
        self.article_list = []
        self.curl_string = ''
        self.source = source
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            if driver is None:
                options = Options()
                os.environ["DISPLAY"] = ":99"
                # Linux服务器环境必需的配置
                options.binary_location = '/usr/bin/google-chrome-stable'  # 使用实际的Chrome路径
                
                # 必需的基本配置
                options.add_argument('--headless=new')  # 使用新版无头模式
                options.add_argument('--no-sandbox')  # 在Linux服务器端必需
                options.add_argument('--disable-dev-shm-usage')  # 解决内存不足问题
                options.add_argument('--disable-gpu')  # Linux服务器端推荐
                
                # 调试端口配置
                options.add_argument('--remote-debugging-port=9222')
                
                # 浏览器配置
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--start-maximized')
                options.add_argument('--lang=zh-CN')
                options.add_argument('--disable-blink-features=AutomationControlled')
                
                # 设置用户代理
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # 页面加载策略
                options.page_load_strategy = 'normal'
                
                # 创建service并启动driver
                try:
                    service = Service("/usr/local/bin/chromedriver", log_path='chromedriver.log')
                    driver = webdriver.Chrome(service=service, options=options)
                    
                    # 设置超时时间
                    driver.set_page_load_timeout(60)
                    driver.set_script_timeout(60)
                    driver.implicitly_wait(20)
                    
                    print("Chrome WebDriver创建成功")
                except Exception as e:
                    print(f"创建Chrome WebDriver失败: {e}")
                    if driver:
                        driver.quit()
                    raise
                
                print("创建driver成功")
        except Exception as e:
            print(f"创建driver失败: {e}")
            if self.driver:
                self.driver.quit()
            raise e

    def start_get_toutiao_list_page(self,search_type='all'):
        search_words = query_map[self.source]
        searchKeywordList=[]
        if search_words is not None and search_words != '':
            searchKeywordList = search_words.split(',')
        
        print('等待页面加载完成...')
        for searchKeyword in searchKeywordList:
            print(f"\n{'='*50}")
            print(f"当前搜索关键词: {searchKeyword}")
            
            # 为每个关键词创建新的driver实例
            try:
                options = Options()
                
                # 基本设置
       
                options.add_argument('--allow-running-insecure-content')
                
                # 浏览器配置
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--start-maximized')
                options.add_argument('--lang=zh-CN')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument("--headless=new")
              
                options.set_capability('goog:loggingPrefs', {'performance': 'ALL'}) # 开启日志性能监听
                options.add_argument("--auto-open-devtools-for-tabs") 
                # 设置用户代理
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # 页面加载策略
                options.page_load_strategy = 'normal'  # 改为normal，等待页面加载完成
                
                # 创建service
                service = Service("/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=options)
                
                # 设置超时时间
                driver.set_page_load_timeout(60)  # 增加到60秒
                driver.set_script_timeout(60)     # 增加到60秒
                driver.implicitly_wait(20)        # 增加到20秒
                options.add_argument("--disable-blink-features=AutomationControlled")
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
                # 构建搜索URL
                if search_type == 'video':
                    url = f"https://so.toutiao.com/search?keyword={searchKeyword}&pd=xiaoshipin&source=aladdin&dvpf=pc&aid=4916&page_num=0"
                    print(f"视频搜索URL: {url}")
                    self.get_toutiao_search_video(driver,url)
                else:
                    url = f'https://so.toutiao.com/search?dvpf=pc&source=input&keyword={searchKeyword}&pd=synthesis&filter_vendor=site&index_resource=site&filter_period=all'
                    print(f"综合搜索URL: {url}")
                    
                    # 添加重试机制
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            self.get_toutiao_search_all(driver,url)
                            break
                        except Exception as e:
                            print(f"第 {retry + 1} 次尝试失败: {e}")
                            if retry < max_retries - 1:
                                print("等待10秒后重试...")  # 增加重试等待时间
                                time.sleep(10)
                                continue
                            else:
                                print("已达到最大重试次数，跳过当前关键词")
                
            except Exception as e:
                print(f"处理关键词 {searchKeyword} 时出错: {e}")
            finally:
                try:
                    if driver:
                        driver.quit()
                        print(f"关键词 {searchKeyword} 处理完成，已关闭浏览器")
                except:
                    pass
                    
            print(f"{'='*50}\n")
            # 每个关键词之间增加等待时间
            time.sleep(15)

    def get_toutiao_search_all(self,driver,url:str):
        print(f"正在访问搜索页面URL: {url}")
        try:
            # 先访问头条首页
            print("访问头条首页...")
            driver.get("https://baby.sina.cn/")
            time.sleep(5)  # 增加等待时间
            
            # 再访问搜索页面
            print("访问搜索页面...")
            driver.get(url)
            print("页面加载成功")
            
            # 等待页面加载完成
            print("等待页面完全加载...")
            time.sleep(10)  # 增加等待时间
            
            # 遍历多页搜索结果
            for page in range(50):  # 最多获取50页
                print(f"正在获取第 {page + 1} 页")
                
                # 等待搜索结果容器出现
                try:
                    results_container = WebDriverWait(driver, 30).until(  # 增加等待时间
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-result-list"))
                    )
                    print("搜索结果已加载")
                    # 额外等待确保内容完全加载
                    time.sleep(3)
                except Exception as e:
                    print(f"等待搜索结果超时: {e}")
                    break

                # 获取所有结果项
                items = results_container.find_elements(By.CSS_SELECTOR, "div.s-result-list > div")
                if not items:
                    print("未找到搜索结果")
                    break

                print(f"找到 {len(items)} 个搜索结果")
                results = []
                for item in items:
                    try:
                        # 获取跳转 URL
                        url_element = item.find_element(By.CSS_SELECTOR, "div.cs-view.pad-bottom-3.cs-view-block.cs-text.align-items-center.cs-header > div > a")
                        url_result = url_element.get_attribute('href')
                        url_result = get_full_url(url_result)
                        print(f"处理文章URL: {url_result}")

                        # 获取标题
                        title = url_element.text

                        # 获取封面 URL
                        cover_url = ''
                        try:
                            cover_element = item.find_element(By.CSS_SELECTOR, "div.cs-view.cs-view-block.cs-grid.d-flex.flex-row.flex-wrap.grid-m > div.cs-view.cs-view-block.cs-grid-cell.grid-cell-3.grid-cell-x-m > a > div > div > div > img")
                            cover_url = cover_element.get_attribute('src')
                            cover_url = get_full_url(cover_url)
                        except Exception as e:
                            print(f"获取封面图失败: {e}")
                            cover_url = ''

                        # 获取描述
                        abstract_element = item.find_element(By.CSS_SELECTOR, "div.cs-view.cs-view-block.cs-grid.d-flex.flex-row.flex-wrap.grid-m > div.cs-view.cs-view-block.cs-grid-cell.grid-cell-9.grid-cell-x-m > div.cs-view.cs-view-block.cs-text.align-items-center > div > span")
                        abstract = abstract_element.text

                        # 获取作者名称
                        author_element = item.find_element(By.CSS_SELECTOR, "div.cs-view.cs-view-block.cs-grid.d-flex.flex-row.flex-wrap.grid-m > div.cs-view.cs-view-block.cs-grid-cell.grid-cell-9.grid-cell-x-m > div.cs-view.margin-top-3.cs-view-block.cs-source > div > div.cs-view.cs-view-flex.align-items-center.flex-row.cs-source-content > span.d-flex.align-items-center.text-ellipsis.margin-right-4 > span.text-ellipsis")
                        author_name = author_element.text

                        results.append({
                            'url': url_result,
                            'title': title,
                            'cover_url': cover_url,
                            'abstract': abstract,
                            'author_name': author_name
                        })
                        
                        artcle_item = ArticleContent(
                            id_str=parse_toutiao_page_id(url_result),
                            author=author_name,
                            genre=2,
                            origin_url=url_result,
                            image_url=cover_url,
                            title=title
                        )
                        detailInstance = ToutiaoDetailPage(
                            driver=None,
                            source=self.source,
                            cookies=driver.get_cookies(),
                            article_content=artcle_item,
                            update_fource=True
                        )
                        detailInstance.get_detail_page_by_requests(url_result)
                        print(f"文章 {title} 处理完成")
                    except Exception as e:
                        print(f"处理搜索结果项时出错: {e}")
                        continue

                # 输出结果
                print(f"\n第 {page + 1} 页处理完成，共处理 {len(results)} 个结果")
                for result in results:
                    print("\n文章信息:")
                    print("URL:", result['url'])
                    print("Title:", result['title'])
                    print("Cover URL:", result['cover_url'])
                    print("Description:", result['abstract'])
                    print("Author Name:", result['author_name'])
                    print("-" * 40)

                # 尝试点击"下一页"按钮
                try:
                    next_page_button = driver.find_element(By.CLASS_NAME, "cs-button-wrap")
                    next_page_button.click()
                    print("已点击下一页，等待页面加载...")
                    time.sleep(5)  # 增加等待时间
                except Exception as e:
                    print(f"无法找到或点击下一页按钮: {e}")
                    break

        except Exception as e:
            print(f"搜索页面处理出错: {e}")
        finally:
            print("搜索完成，关闭浏览器")
            driver.quit()
    def get_toutiao_search_video(self,driver,url:str):
        self.driver.get(url)
        # 等待视频列表加载
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.main.hide-side-list > div.s-result-list.pd-video"))
            )

            # 获取视频列表
            video_elements = driver.find_elements(By.CSS_SELECTOR, "body > div.main.hide-side-list > div.s-result-list.pd-video > div.cs-view.cs-view-block.cs-grid.d-flex.flex-row.flex-wrap.grid-m.grid-list-container > div")
            result = []
            # 遍历每个视频元素
            for video in video_elements:
                # 获取视频标题
                title_element = video.find_element(By.CSS_SELECTOR, "div > a > div > div.cs-view.margin-top-3.cs-view-block.cs-text.align-items-center.text-wrap > div > span")
                title = title_element.text if title_element else '无标题'

                # 获取封面 URL
                cover_element = video.find_element(By.CSS_SELECTOR, "div > a > div > div.cs-view.cs-view-block.cs-image > div.d-block.position-relative.overflow-hidden.radius-m.cs-image-border.cs-image-wrapper > div > div > img")
                cover_url = cover_element.get_attribute('src') if cover_element else '无封面'

                # 获取作者名
                author_element = video.find_element(By.CSS_SELECTOR, "div > a > div > div.cs-view.margin-top-2.cs-view-block.cs-source > div > div > span.d-flex.align-items-center.text-ellipsis.margin-right-4 > span")
                author_name = author_element.text if author_element else '无作者'

                # 获取视频链接
                link_element = video.find_element(By.CSS_SELECTOR, "div > a")
                video_link = link_element.get_attribute('href') if link_element else '无链接'

                # 打印结果
                print(f"标题: {title}")
                print(f"封面 URL: {cover_url}")
                print(f"作者名: {author_name}")
                print(f"视频链接: {video_link}")
                print('-' * 40)
                artcle_item = ArticleContent(id_str=parse_toutiao_page_id(video_link),genre=1,origin_url=video_link,image_url=cover_url, title=title)
                detailInstance = ToutiaoDetailPage(driver=None,source=self.source,cookies=self.driver.get_cookies(),article_content=artcle_item,update_fource=True)
                # detailInstance.start_get_toutiao_detail_page()
                detailInstance.get_detail_page_by_requests(video_link)
                result.append(artcle_item)
            self.article_list = result
        except Exception as e:
            print('get_toutiao_search_video:',e)
    
    def detail_page_task(self,item):
        try:
            authorId = ''
            if 'author_id' in item:
                authorId = item['author_id']
            docId = item['docid']
            image_url = ''
            if 'thumbs' in item and len(item['thumbs']) > 0:
                image_url = item['thumbs'][0]
            comment_count= item['comment_count']
            url = item['url']
            title = item['title']
            # if 'commentinfo' in item:
            #     comment_count = item['commentinfo']['qreply']
        #                         "commentinfo": {
        #     "qreply": 3874,
        #     "qreply_show": 2441,
        #     "show": 192,
        #     "thread_show": 154,
        #     "total": 4116
        # },
            print(item)
            article_content = ArticleContent(id_str=docId,genre=2,author=authorId,origin_url=url,image_url=image_url, title=title,comment_count= comment_count)
            detailInstance = ToutiaoDetailPage(driver=None,source=self.source,cookies=self.driver.get_cookies(),article_content=article_content)
            # detailInstance.start_get_toutiao_detail_page()
            detailInstance.get_detail_page_by_requests(url)
            return 0
        except Exception as e:
            print('detail_page_task:',e)
            return 1
    def read_more_page(self,driver,page_num):
        try:
            if page_num > 30:
                return
        # 示例使用
            curl_string = self.curl_string
            # urllib_request = curl_to_urllib(curl_string, url_params=url_params, data_params=data_params)
            if curl_string.startswith("curl --location"):
                curl_string = 'curl ' + curl_string[len("curl --location"):]
            curl_cmd = parseCurlCommand(curl_string)
            # print(curl_cmd.params)
            params = {key: value for key, value in curl_cmd.params}

        
            params['up'] = page_num
            headers = curl_cmd.headers
            callback = params['callback']
            if callback is  None:
                callback = ''
            cookies = curl_cmd.cookies
            target_url = curl_cmd.url
            method = curl_cmd.method

            # 使用代理下载图像
    # 根据 method 执行不同的请求
                # 创建线程池，最多使用 5 个线程
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # 提交任务
                # futures =[] {executor.submit(self.detail_page_task, ): i for i in range(10)}  # 提交 10 个任务
                futures =[]
                # 处理结果
                
                if method.upper() == 'GET':
                    # 使用 requests 库的 GET 请求
                    response = requests.get(target_url, params=params, headers=headers, cookies=cookies)
                    print('response',response.status_code)
                    if response.status_code != 200:
                        print(f"Failed to send request: {response.status_code}")
                        if f'{response}'.find('Failed to establish a new connection') != -1:
                            return e
                        return
                    # json_text = response_text.split('(', 1)[1].rsplit(')', 1)[0]
                    r = json.loads(response.text[len(callback+"("):len(response.text)-len(");")])
                    for item in r['data']['feed']:
                        if item['view_name'] == '专题':
                            continue
                        additional_future = executor.submit(self.detail_page_task, item)
                        futures.append(additional_future)
                        
                    # parseDouyinAuthorId(response.text,headers,cookies)
                    
                    # print(response.text)

                elif method.upper() == 'POST':
                    # 使用 requests 库的 POST 请求
                    response = requests.post(target_url, data=params, headers=headers, cookies=cookies)
                    print(response.text)

                elif method.upper() == 'PUT':
                    # 使用 requests 库的 PUT 请求
                    response = requests.put(target_url, data=params, headers=headers, cookies=cookies)
                    print(response.text)

                elif method.upper() == 'DELETE':
                    # 使用 requests 库的 DELETE 请求
                    response = requests.delete(target_url, headers=headers, cookies=cookies)
                    print('status code ',response.status_code)
                    print(response.text)
                for future in concurrent.futures.as_completed(futures):
                    task_id = futures[future]
                    try:
                        result = future.result(timeout=120)   # 获取任务的返回值
                        print(f"Task {task_id} result: {result}")
                    except Exception as e:
                        print(f"Task {task_id} generated an exception: {e}")
        except Exception as e:
            if f'{e}'.find('Max retries exceeded with url') != -1:
                print(f"Failed to send request: {e}")
                return e
            print(f"Failed to send request: {e}")
        self.read_more_page(driver,page_num+1)
        return None
    def get_list_page(self, driver):
        try:
            # 等待元素可见
            # time.sleep(5)
            xpath='//*[@id="artibody"]'
            # close_button_selector = "#login-pannel > div > div > div.toutiao-login__close.dy-account-close"
            # WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, xpath)))
            # time.sleep(5)
            print("等待短信登录元素可见")
            # 获取元素位置
            save_image_name = 'message_return_button'
            screenshot_path = os.path.join(self.cache_dir,f"{save_image_name}_before.png")
            driver.save_screenshot(screenshot_path)
            article = driver.find_element(By.XPATH, xpath)
            html_content = article.get_attribute('outerHTML')
            with open('article.html', 'w', encoding='utf-8') as file:
                file.write(html_content)

            # 截图
            driver.save_screenshot(os.path.join(self.cache_dir,f"{save_image_name}_end.png"))



        except Exception as e:
            print('get login message button no found:',e)  
       
   
    