"""
辟谣网站爬虫 - Selenium版本
"""
import os
import json
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin

# API配置
API_CONFIG = {
    'base_url': 'http://localhost:5005',
    'username': 'user1',
    'password': 'user1123456'
}

class PiyaoSpider:
    def __init__(self):
        self.base_url = "https://www.piyao.org.cn"
        self.logger = logging.getLogger(__name__)
        self.api_base_url = API_CONFIG['base_url']
        self.token = None
        # 初始化统计信息
        self.stats = {
            'total': 0,    # 总处理数
            'new': 0,      # 新增数
            'existing': 0, # 已存在数
            'error': 0     # 错误数
        }
        # 登录获取token
        if not self.login():
            raise Exception("API登录失败")
        self.driver = self._init_driver()

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

    def _init_driver(self):
        """初始化Chrome驱动"""
        # 确保使用虚拟显示
        os.environ["DISPLAY"] = ":99"

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        
        # 添加自定义请求头
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # 显式指定Chrome路径
        options.binary_location = "/usr/bin/google-chrome-stable"
        
        return webdriver.Chrome(options=options)

    def wait_and_get_element(self, by, value, timeout=10):
        """等待并获取元素"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {value}")
            return None

    def wait_and_get_elements(self, by, value, timeout=10):
        """等待并获取多个元素"""
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {value}")
            return []

    def get_page_content(self, url):
        """获取页面内容"""
        try:
            self.logger.info(f"正在请求页面: {url}")
            self.driver.get(url)
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            return True
        except Exception as e:
            self.logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
            return False

    def parse_list_page(self):
        """解析列表页"""
        url = f"{self.base_url}/bq/index.htm"
        if not self.get_page_content(url):
            return None

        articles = []
        try:
            # 尝试获取特定的列表项
            article_elements = (
                self.wait_and_get_elements(By.CSS_SELECTOR, 'body > div.part04.partList.clearfix > div > ul > li')
            )

            self.logger.info(f"找到 {len(article_elements)} 篇文章")
            
            for article in article_elements:
                try:
                    # 获取图片信息
                    img_element = article.find_element(By.CSS_SELECTOR, 'div.img img')
                    img_src = img_element.get_attribute('src') if img_element else None
                    img_alt = img_element.get_attribute('alt') if img_element else None

                    # 获取标题链接
                    title_element = article.find_element(By.CSS_SELECTOR, 'h2 a')
                    title = title_element.text.strip()
                    href = title_element.get_attribute('href')
                    
                    # 获取来源信息
                    source_element = article.find_element(By.CSS_SELECTOR, 'h3')
                    source = source_element.text.strip() if source_element else None

                    # 获取"查看真相"链接
                    truth_link_element = article.find_element(By.CSS_SELECTOR, 'span a')
                    truth_link = truth_link_element.get_attribute('href') if truth_link_element else None

                    if href:
                        href = urljoin(self.base_url, href)
                        self.logger.info(f"解析到文章: {title} - {href}")
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'image_src': urljoin(self.base_url, img_src) if img_src else None,
                            'image_alt': img_alt,
                            'source': source,
                            'truth_link': urljoin(self.base_url, truth_link) if truth_link else None
                        })
                except Exception as e:
                    self.logger.error(f"解析文章链接失败: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"解析列表页失败: {str(e)}", exc_info=True)
            return None

        return articles

    def parse_truth_page(self, url):
        """解析真相页面的详细内容"""
        if not self.get_page_content(url):
            return None

        article_data = {}
        try:
            # 获取标题
            title_element = self.wait_and_get_element(By.CSS_SELECTOR, 'div.con_tit h2')
            if title_element:
                article_data['title'] = title_element.text.strip()
                self.logger.info(f"获取到真相标题: {article_data['title']}")

            # 获取来源和时间
            source_time_element = self.wait_and_get_element(By.CSS_SELECTOR, 'div.con_tit p')
            if source_time_element:
                text = source_time_element.text.strip()
                # 分离来源和时间
                if '来源：' in text and '时间：' in text:
                    source = text.split('来源：')[1].split('时间：')[0].strip()
                    time_str = text.split('时间：')[1].strip()
                    article_data['source'] = source
                    article_data['time'] = time_str

            # 获取正文内容
            content_element = self.wait_and_get_element(By.CSS_SELECTOR, 'div#detailContent')
            if content_element:
                # 获取原始HTML内容
                article_data['content'] = content_element.get_attribute('innerHTML')
                self.logger.info(f"获取到真相内容HTML长度: {len(article_data['content'])}")
                
                # 获取纯文本内容作为备用
                paragraphs = content_element.find_elements(By.TAG_NAME, 'p')
                content_text = []
                for p in paragraphs:
                    text = p.text.strip()
                    if text:
                        content_text.append(text)
                article_data['content_text'] = '\n'.join(content_text)

            # 获取责任编辑
            editor_element = self.wait_and_get_element(By.CSS_SELECTOR, 'div.zrbj')
            if editor_element:
                article_data['editor'] = editor_element.text.strip()

        except Exception as e:
            self.logger.error(f"解析真相页面失败: {url}, 错误: {str(e)}", exc_info=True)
            return None

        return article_data

    def parse_detail_page(self, url):
        """解析详情页，主要用于获取真相链接"""
        if not self.get_page_content(url):
            return None

        article_data = {}
        try:
            # 获取标题（用于日志）
            title_element = self.wait_and_get_element(By.CSS_SELECTOR, 'div.con_tit h2')
            if title_element:
                article_data['title'] = title_element.text.strip()
                self.logger.info(f"获取到标题: {article_data['title']}")

            # 查找"点击真相"链接
            truth_link = self.wait_and_get_element(By.CSS_SELECTOR, "p[style*='text-align: center'] a[href*='piyao.org.cn']")
            if truth_link:
                href = truth_link.get_attribute('href')
                if href:
                    article_data['truth_link'] = href
                    self.logger.info(f"找到真相链接: {article_data['truth_link']}")

        except Exception as e:
            self.logger.error(f"解析详情页失败: {url}, 错误: {str(e)}", exc_info=True)
            return None

        return article_data

    def save_to_api(self, data):
        """保存数据到API"""
        url = f"{self.api_base_url}/api/spider/data"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'source': 'piyao',
            'data': data
        }
        
        self.logger.info(f"准备保存数据到API: {url}")
        # self.logger.info(f"请求Headers: {headers}")
        # self.logger.info(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            self.logger.info(f"API响应状态码: {response.status_code}")
            self.logger.info(f"API响应内容: {response.text}")
            
            self.stats['total'] += 1
            
            if response.status_code == 200:
                self.stats['new'] += 1
                self.logger.info("数据保存成功")
                return True
            elif response.status_code == 400 and "已存在" in response.text:
                self.stats['existing'] += 1
                self.logger.info("该文章已存在，跳过")
                return True
            else:
                self.stats['error'] += 1
                self.logger.error(f"API请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
                
        except Exception as e:
            self.stats['error'] += 1
            self.logger.error(f"保存数据时发生错误: {str(e)}")
            return False

    def crawl(self):
        """开始爬取"""
        self.logger.info("开始爬取辟谣网站")
        
        try:
            # 获取列表页文章
            articles = self.parse_list_page()
            if not articles:
                self.logger.error("获取文章列表失败")
                return None

            results = []
            for index, article in enumerate(articles, 1):
                self.logger.info(f"正在爬取第 {index}/{len(articles)} 篇文章: {article['title']}")
                
                # 获取文章详情
                detail = self.parse_detail_page(article['url'])
                if detail:
                    # 如果存在真相链接，继续爬取
                    if 'truth_link' in detail:
                        self.logger.info(f"正在爬取真相页面: {detail['truth_link']}")
                        truth_detail = self.parse_truth_page(detail['truth_link'])
                        if truth_detail:
                            detail['truth_content'] = truth_detail
                            # 保存到API
                            self.save_to_api(truth_detail)
                    results.append(detail)
                
                # 添加延时，避免请求过快
                time.sleep(2)

            # 记录统计信息
            self.logger.info(f"爬取完成，统计信息：{json.dumps(self.stats, ensure_ascii=False)}")
            return results

        finally:
            # 确保关闭浏览器
            self.driver.quit()

def run_spider():
    """运行爬虫"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('piyao_spider.log', encoding='utf-8')
        ]
    )
    
    spider = PiyaoSpider()
    results = spider.crawl()
    
    if results:
        logging.info(f"成功爬取 {len(results)} 篇文章")
        return results
    else:
        logging.error("爬取失败")
        return None

if __name__ == "__main__":
    run_spider() 