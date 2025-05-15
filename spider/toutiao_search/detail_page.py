import json
import os
from datetime import datetime
import random
import re
from typing import Tuple
import uuid
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from model.article import ArticleContent, Comment
from spider.toutiao_search.toutiao_util import parse_toutiao_page_id
from utils.utils import convert_text_count_to_int
from bs4 import BeautifulSoup
import zipfile
import cv2
import time

def start_get_toutiao_detail_page_out(request_url):
    toutiaoDetailPage =ToutiaoDetailPage(None)
    toutiaoDetailPage.start_get_toutiao_detail_page(request_url,quit_driver=True)

class ToutiaoDetailPage:
    def __init__(self,driver,source,cookies=[],data_from='web',article_content=ArticleContent(),update_fource=False) -> None:
        self.driver = driver
        self.cache_dir = 'cache_dir/toutiao'
        self.article_content = article_content
        self.data_from = data_from
        self.source = source
        self.update_fource = update_fource
        os.makedirs(self.cache_dir , exist_ok=True)
        try:
            if driver is None:
                options = Options()
                options.add_argument('--headless')  # 无头模式
                options.add_argument('--no-sandbox')  # 禁用沙箱
                options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
                options.add_argument('--disable-gpu')  # 禁用GPU加速
                options.add_argument('--disable-infobars')  # 禁用信息栏
                options.add_argument('--disable-notifications')  # 禁用通知
                options.add_argument('--disable-extensions')  # 禁用扩展
                options.add_argument('--remote-debugging-port=9222')  # 设置调试端口
                options.add_argument('--window-size=1920,1080')  # 设置窗口大小
                options.add_argument('--start-maximized')  # 最大化窗口
                options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化控制检测
                
                # 使用 webdriver_manager 自动管理 ChromeDriver
                service = Service("/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(
                    service=service,
                    options=options
                )
                print("创建driver成功")
        except Exception as e:
            print(f"创建driver失败: {e}")        

    def start_get_toutiao_detail_page(self,request_url='',quit_driver=False):
        driver = self.driver
        try:
            print("正在访问用户页面...")
            
            # 设置页面加载超时时间
            driver.set_page_load_timeout(30)  # 30秒超时
            driver.set_script_timeout(30)     # JavaScript执行超时
            
            # 设置初始URL
            initial_url = "https://www.toutiao.com"
            try:
                driver.get(initial_url)
                print(f"成功访问初始页面: {initial_url}")
            except Exception as e:
                print(f"访问初始页面失败: {e}")
                return None
                
            # 等待页面加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("页面基本元素加载完成")
            except Exception as e:
                print(f"等待页面加载超时: {e}")
                return None
            
            # 执行实际的爬取操作
            print("开始爬取内容...")
            result = self.get_detail_page(driver, request_url)
            return result
            
        except Exception as e:
            print(f"爬取过程发生错误: {e}")
            return None
        finally:
            if quit_driver:
                try:
                    driver.quit()
                    print("浏览器已关闭")
                except:
                    print("关闭浏览器时发生错误")

    def replace_image_url(self,item: ArticleContent) -> Tuple[str, Exception]:
        text = item.content_html
        pattern = r'<img\s+src="([^"]+)"[^>]*>'
        re_uri = r'web_uri="[^"]*"'

        # 查找所有匹配的图片链接
        img_urls = re.findall(pattern, text)

        # 替换 web_uri
        text = re.sub(re_uri, '', text)

        # 打印和替换图片链接
        for img_url in img_urls:
            img_url_tmp = img_url.replace("&amp;", "&")
            print(img_url_tmp)
            image_name = f"image/{uuid.uuid4()}"
            file_info = upload_editor_image(url=img_url_tmp)  # 上传图像并获取编码的 URL
            if file_info is None or file_info['url'] is None:
                print(f"上传图片失败: {img_url_tmp}")
                return text, Exception(f"上传图片失败: {img_url_tmp}")
            text = text.replace(img_url, file_info['url'])
            print(f"替换图片成功: {file_info['url']}")


        # 替换 item 的 image_urls
        # for i in range(len(item.image_url)):
        #     item.image_urls[i] = item.image_urls[i].replace("&amp;", "&")
        #     item.image_urls[i] = upload_editor_image(item.image_urls[i])  # 上传并获取编码的 URL
        item.content_html = text
        print(f"替换图片成功: {text}")
        return text, None  # 返回处理后的 HTML 和错误（如果有的话）
    def save_w_item_ori_video(self,article:ArticleContent,update_force=False):
        if self.source == '':
            print('detail page source 为空')
            return
        try:
            categorys = ['burning']
            oriItem = OriItem(genre=1,source=self.source,aweme_id=article.id_str,categorys=categorys, ori_url=article.origin_url, author_uid='',download_url='',preview_title=article.title,author_sec_uid='',desc=article.abstract,comment_count=article.comment_count,like_count=article.like_count,data=article.to_json())
            if article.genre == 1 and article.origin_url == '':
                print('视频链接为空')
                return
            if "今日头条"in article.content_html:
                print('今日头条')
            w_item_ori = create_item_ori_with_check(oriItem)
            if article.title == '':
                print("创建 w_item_ori 失败,title 为空")
                return
            upload_cover_url= ''
            if 'cover'in w_item_ori :
                upload_cover_url = w_item_ori['cover']
          
            if w_item_ori is None or w_item_ori['id'] is None:
                print("创建 w_item_ori 失败")
                return
            if update_force == False and  w_item_ori['data'] is not None and  w_item_ori['data'] != '' and upload_cover_url != '':
                is_exist = True
                print("创建 w_item_ori url 已经存在，不再上传")
                return
            cover_url = article.image_url
            

          
            # if upload_cover_url is None or upload_cover_url == '' :
            if True:
   
                    if 'http' in upload_cover_url and "oss.huanfangsk.com" not in upload_cover_url:   
                        try:
                           
                            file_info = upload_avatar(cover_url,headers=[],cookies=[],max_size=1024*1024*2)
                            if file_info is None or file_info['url'] is None:
                                print(f"上传cover失败: {cover_url}")
                                return
                            upload_cover_url= file_info['url']
                          
                        except requests.RequestException as e:
                            print(f"上传avatar失败Failed to send request: {e}")
            article.image_url = upload_cover_url
            article.cover = upload_cover_url
            w_item_ori['cover'] = upload_cover_url
            w_item_ori['title'] = article.title
            w_item_ori['desc'] = article.title
            w_item_ori['data'] = article.to_json()
            
            update_item = update_w_item_ori(w_item_ori)
            if update_item is None:
                print(f"更新 w_item_ori 失败: ")
            else:
                print(f"更新 w_item_ori:{update_item['id']} {update_item['obj_url']}")

        except Exception as e:
            print(f"Failed to send request: {e}")

    def save_w_item_ori(self,article:ArticleContent,update_force=False):
        try:
            categorys = ['burning']
            if self.source == '':
                print('detail page source 为空')
                return
            oriItem = OriItem(genre=article.genre,source=self.source,aweme_id=article.id_str,categorys=categorys, ori_url=article.origin_url, author_uid='',download_url='',preview_title=article.title,author_sec_uid='',desc=article.abstract,comment_count=article.comment_count,like_count=article.like_count,data=article.to_json())
            if article.genre == 1 and article.origin_url == '':
                print('视频链接为空')
                return
            if "今日头条"in article.content_html:
                print('今日头条')
            w_item_ori = create_item_ori_with_check(oriItem)
            if article.title == '':
                print("创建 w_item_ori 失败,title 为空")
                return
            upload_cover_url= ''
            upload_tiny_cover_url= ''
            if 'cover'in w_item_ori :
                upload_cover_url = w_item_ori['cover']
            if 'tiny_cover'in w_item_ori :
                upload_tiny_cover_url = w_item_ori['tiny_cover']
            if w_item_ori is None or w_item_ori['id'] is None:
                print("创建 w_item_ori 失败")
                return
            if update_force == False and  w_item_ori['data'] is not None and  w_item_ori['data'] != '' and upload_cover_url != '':
                is_exist = True
                print("创建 w_item_ori url 已经存在，不再上传")
                return
            cover_url = article.image_url
            video_url = w_item_ori['obj_url']
            if article.genre == 1:
                if 'http' in article.origin_url and "oss.huanfangsk.com" not in video_url:   
                    try:
                        
                        file_info = upload_file(article.origin_url,headers=[],cookies=[])
                        if file_info is None or file_info['url'] is None:
                            print(f"上传视频失败: {article.origin_url}")
                            return
                        video_url= file_info['url']
                        
                    except requests.RequestException as e:
                        print(f"上传avatar失败Failed to send request: {e}")
          
            # if upload_cover_url is None or upload_cover_url == '' :
            
            if 'http' in cover_url and ("oss.huanfangsk.com" not in upload_cover_url and "ostart:" not in upload_cover_url):   
                try:
                    
                    file_info = upload_avatar(cover_url,headers=[],cookies=[],max_size=1024*1024*2)
                    if file_info is None or file_info['url'] is None:
                        print(f"上传cover失败: {cover_url}")
                        return
                    upload_cover_url= file_info['url']

                except requests.RequestException as e:
                    print(f"上传avatar失败Failed to send request: {e}")
            if 'http' in cover_url and ("oss.huanfangsk.com" not in upload_tiny_cover_url and "ostart:" not in upload_tiny_cover_url):
                try:
                    file_info_tiny = upload_avatar(cover_url,headers=[],cookies=[],max_size=256*256)
                    if file_info_tiny is None or file_info_tiny['url'] is None:
                        print(f"上传tiny cover失败: {cover_url}")
                        return
                    upload_tiny_cover_url= file_info_tiny['url']
                except requests.RequestException as e:
                    print(f"上传avatar失败Failed to send request: {e}")
            article.image_url = upload_cover_url
            article.cover = upload_cover_url
            article.obj_url = video_url
            w_item_ori['obj_url'] = video_url
            w_item_ori['tiny_cover'] = upload_tiny_cover_url
            w_item_ori['cover'] = upload_cover_url
            w_item_ori['title'] = article.title
            w_item_ori['desc'] = article.title
            w_item_ori['data'] = article.to_json()
            
            update_item = update_w_item_ori(w_item_ori)
            if update_item is None:
                print(f"更新 w_item_ori 失败: ")
            else:
                print(f"更新 w_item_ori:{update_item['id']} {update_item['obj_url']}")
            return update_item
        except Exception as e:
            print(f"Failed to send request: {e}")
            return None

    def get_video_detail_page(self,detail_url:str):
        try:
            print("get_video_detail_page",detail_url)
            if "douyin.com" in detail_url:
                print("douyin.com")
                return
            driver = self.driver
    # 获取视频 URL
            video_url = ''
            driver.get(detail_url)
            # 等待视频元素可见（超时40秒）
            try:
                video_element = WebDriverWait(driver, 40).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#root > div > div.main-content > div.left-content > div > div.video-slider-wrapper > ul > li:nth-child(2) > div > video"))
                )
                video_url = video_element.get_attribute('src')
            except Exception as e:
                print("Error while waiting for video element:", e)
                driver.quit()
                return

            # video_url = video_element.get_attribute('src')
            if video_url == '':
                print("Video URL not found.")
                driver.quit()
                return
            # 获取标题
            title_element = driver.find_element(By.CSS_SELECTOR, "#root > div > div.main-content > div.left-content > div > div.ttp-video-extras-bar > div.left-block > div.ttp-video-extras-title > h1")
            title = title_element.get_attribute('title')

            # 获取点赞量
            like_element = driver.find_element(By.CSS_SELECTOR, "#root > div > div.main-content > div.left-content > div > div.ttp-video-extras-bar > div.right-block > ul > li:nth-child(1) > button > span")
            likes_text = like_element.text
            like_count = convert_text_count_to_int(likes_text)

            # 获取评论量
            comments_element = driver.find_element(By.CSS_SELECTOR, "#root > div > div.main-content > div.left-content > div > div.ttp-video-extras-bar > div.right-block > ul > li:nth-child(2) > button > span")
            comments =convert_text_count_to_int( comments_element.text)

            # 获取收藏量
            favorites_element = driver.find_element(By.CSS_SELECTOR, "#root > div > div.main-content > div.left-content > div > div.ttp-video-extras-bar > div.right-block > ul > li:nth-child(3) > button > span")
            favorites = convert_text_count_to_int(favorites_element.text)
            self.article_content.like_count = like_count
            if title != '' and title  != "展开":
                self.article_content.title = title
            self.article_content.comment_count = comments
            self.article_content.origin_url = video_url
            # 创建请求
            w_item_ori = self.save_w_item_ori(self.article_content,update_force=True)
            # 输出结果
            print("Video URL:", video_url)
            print("Title:", title)
            print("Likes:", like_count)
            print("Comments:", comments)
            print("Favorites:", favorites)
            return w_item_ori
        except Exception as e:
            print(f"get video detail page fail: {e}")
            return None
        
    def get_detail_page_by_requests(self,detail_url:str):
        if self.source == '':
            print('detail page source 为空')
            return
        print('get_detail_page_by_requests',detail_url)
        if self.article_content.id_str == None or self.article_content.id_str == '':
            self.article_content.id_str = parse_toutiao_page_id(detail_url)
        if self.article_content.id_str == None or self.article_content.id_str == '':
            print("获取id 为空，不处理",self.article_content)
            return
        if self.update_fource == False:
            exist_w_items_ori = get_w_item_ori(self.source,id=self.article_content.id_str)
            if   exist_w_items_ori is not None and len(exist_w_items_ori) > 0:
                print("已经存在")
                return
        if detail_url is None or detail_url == "":
            detail_url = self.article_content.origin_url
        if self.article_content.genre == 1:
            w_item_ori = self.get_video_detail_page(detail_url)
            return w_item_ori
        elif self.article_content.genre == 2:
            w_item_ori = self.get_article_detail_page_toutiao(detail_url)
            return  w_item_ori 
    def get_article_detail_page_toutiao(self,detail_url:str):
        # 等待文章详情可见（超时40秒）
        driver = self.driver
        driver.get(detail_url)
        article_html = ''
        try:
            article_element = WebDriverWait(driver, 40).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#root > div.article-detail-container > div.main > div:nth-child(1) > div > div > div > div > article"))
            )
            # cssPath = "#root > div.article-detail-container > div.main > div:nth-child(1) > div > div > div > div > article"
            article_html = article_element.get_attribute('outerHTML')
    
    # 打印 HTML 内容
            print("Article HTML:",article_html)
        except Exception as e:
            print("Error while waiting for article element:", e)
           
        if article_html == '':
            try:
                article_element = driver.find_element(By.CSS_SELECTOR, "#root > div.article-detail-container > div.main > div.show-monitor > div > div > div > div > article")
                article_html = author_element.text
            except Exception as e:
                print("Error while getting author URL:", e)
                driver.quit()
                return

        # 获取作者链接
        try:
            author_element = driver.find_element(By.CSS_SELECTOR, "#root > div.article-detail-container > div.main > div:nth-child(1) > div > div > div > div > div > span.name > a")
            author_url = author_element.get_attribute('href')
            author_url = get_full_author_url(author_url)
            self.article_content.author = author_element.text
        except Exception as e:
            print("Error while getting author URL:", e)
           
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "#root > div.article-detail-container > div.main > div:nth-child(1) > div > div > div > div > h1")
            title = title_element.text
            if title != '':
                self.article_content.title = title
        except Exception as e:
            print("Error while getting author URL:", e)
        # 获取评论列表
        comments = []
        try:
            like_count = driver.find_element(By.CSS_SELECTOR, "#root > div.article-detail-container > div.left-sidebar > div > div.fadeIn > div > div.detail-like > span")
            like_count = like_count.text
            self.article_content.like_count = like_count
        except Exception as e:
            print("Error while getting like count:", e)
        try:
            comment_count = driver.find_element(By.CSS_SELECTOR, "#root > div.article-detail-container > div.left-sidebar > div > div.fadeIn > div > div.detail-interaction-comment > span")
            comment_count = comment_count.text
            self.article_content.comment_count = convert_text_count_to_int(comment_count)
        except Exception as e:
            print("Error while getting like count:", e)
        try:
            comment_list = driver.find_elements(By.CSS_SELECTOR, "#comment-area > ul > li")
            for comment_item in comment_list:
                try:
                    reply_text_element = comment_item.find_element(By.CSS_SELECTOR, "div > div > div.body > p")
                    reply_text = reply_text_element.text
                    commentItem = Comment(content=reply_text)
                    comments.append(commentItem.__dict__)
                except Exception as e:
                    print("Error while processing a comment item:", e)
        except Exception as e:
            print("Error while getting comment list:", e)

        self.article_content.author_url = author_url
        self.article_content.content_html = article_html
        self.article_content.content_html = self.replace_image_url(self.article_content)
        self.article_content.content_html = clean_html(article_html,selectors_to_remove=[],clean_words={"编辑":"","今日头条":""})
        self.article_content.comment_data = json.dumps(comments)
        # 创建请求
        w_item_ori =  self.save_w_item_ori(self.article_content,update_force=True)
        # 输出结果
        print("Author URL:", author_url)
        print("Comments:")
        for reply in comments:
            print("-", reply)
        return w_item_ori
        # 关闭浏览器
        driver.quit()
    def get_article_detail_page(self,detail_url:str):
        if detail_url is None or detail_url == "":
            detail_url = self.article_content.origin_url
        
        selectors_to_remove = [
            '#artibody > p.article-editor',
            '#ad_44099',
            '#artibody > div.clearfix.appendQr_wrap',
            '#article_content > div.article-content-left > div.new_style_article',
            'body > main > section.j_main_art > section > article > section > p.article-editor',
            '#wx_pic',
            '#ad_44099',
            '.clearfix.appendQr_wrap',
            'p.article-editor',
            '.ldy_art_bottom_button_box',
            'blockquote',
        ]
        try:
            # 发送 HTTP 请求
            response = requests.get(detail_url)
            response.raise_for_status()  # 检查请求是否成功
            response.encoding = response.apparent_encoding  # 自动检测编码

            # 获取响应数据
            response_data = response.text
            soup = BeautifulSoup(response_data, 'html.parser')

            content_html = ''
            comment_list = []
            # 获取 ID 为 artibody 的元素
            if "detail-" in self.article_content.id_str and '.d' in self.article_content.id_str:
                section_element = soup.select_one('main > section:nth-of-type(1) > section > article > section:nth-of-type(2)')
                for selector in selectors_to_remove:
                    for element in section_element.select(selector):
                        element.decompose()  # 从树中移除元素
                # 检查元素是否存在并打印内容
                comments = soup.find_all('b', class_='discuss_com_txt')
                if comments:
                    for comment in comments:
                        commentItem = Comment(content=comment.text)
                        comment_list.append(commentItem.__dict__)

                if section_element:
                    html_content = str(section_element) 
                else:
                    print("Element not found.")

            else:
                section_element = soup.find(id='artibody')  # 使用 find 方法
                for selector in selectors_to_remove:
                    for element in section_element.select(selector):
                        element.decompose()  # 从树中移除元素
                comments = soup.find_all('div', class_='txt', comment_type='itemTxt')
                if comments:
                    for comment in comments:
                        commentItem = Comment(content=comment.text)
                        comment_list.append(commentItem.__dict__)
                # 检查元素是否存在并打印内容
                if section_element:
                    html_content = str(section_element) 
                else:
                    print("Element with ID 'artibody' not found.")
                if len(html_content) == 0:
                    print("文章内容为空")
                    return
                self.article_content.content_html = html_content
                self.article_content.comment_data = json.dumps(comment_list)
                # 创建请求
                self.save_w_item_ori(self.article_content,update_force=True)
            # 获取修改后的 HTML
            return response_data
        except requests.RequestException as e:
            print(f"get detail article fail: {e}")
            return None
    def get_detail_page(self, driver, detail_url:str, item_from='web'):
        if detail_url is None or detail_url == "":
            detail_url = self.article_content.origin_url
            
        print(f"准备访问页面: {detail_url}")
        
        try:
            # 设置页面加载超时
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            
            # 访问目标页面
            try:
                driver.get(detail_url)
                print("页面访问成功")
            except Exception as e:
                print(f"访问页面失败: {e}")
                return None
                
            # 等待页面主要内容加载
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
                print("文章内容已加载")
            except Exception as e:
                print(f"等待文章内容超时: {e}")
                return None
                
            # 获取文章内容
            try:
                article = driver.find_element(By.TAG_NAME, "article")
                html_content = article.get_attribute('outerHTML')
                print(f"成功获取文章内容，长度: {len(html_content)}")
                
                # 处理文章内容
                self.article_content.content_html = html_content
                self.save_w_item_ori(self.article_content, update_force=True)
                return html_content
                
            except Exception as e:
                print(f"获取文章内容失败: {e}")
                return None
                
        except Exception as e:
            print(f"处理页面时发生错误: {e}")
            return None


def get_full_author_url(author_url):
    """确保作者 URL 以 https://www.toutiao.com 开头"""
    if author_url.startswith('/c/'):
        return "https://www.toutiao.com" + author_url
    return author_url
