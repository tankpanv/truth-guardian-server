"""
辟谣网站爬虫
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin
import re
import json

class PiyaoSpider:
    def __init__(self):
        self.base_url = "https://www.piyao.org.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        self.logger = logging.getLogger(__name__)

    def get_page_content(self, url):
        """获取页面内容"""
        try:
            self.logger.info(f"正在请求页面: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # 检查响应状态
            response.encoding = 'utf-8'
            
            # 记录响应状态
            self.logger.info(f"页面请求成功: {url}, 状态码: {response.status_code}")
            
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {url}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}")
            return None

    def parse_list_page(self):
        """解析列表页"""
        url = f"{self.base_url}/bq/index.htm"
        content = self.get_page_content(url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        try:
            # 打印页面结构以便调试
            self.logger.debug(f"页面结构:\n{soup.prettify()[:500]}")
            
            # 尝试多个可能的选择器
            article_list = soup.select('div.list ul li a') or \
                         soup.select('.list ul li a') or \
                         soup.select('ul li a')
                         
            self.logger.info(f"找到 {len(article_list)} 篇文章")
            
            for article in article_list:
                href = article.get('href', '')
                if not href:
                    continue
                    
                # 处理相对路径
                if href.startswith('..'):
                    href = href.replace('..', '')
                elif href.startswith('/'):
                    href = href[1:]
                    
                full_url = urljoin(self.base_url, href)
                title = article.get_text(strip=True)
                
                self.logger.info(f"解析到文章: {title} - {full_url}")
                
                articles.append({
                    'title': title,
                    'url': full_url
                })
                
        except Exception as e:
            self.logger.error(f"解析列表页失败: {str(e)}", exc_info=True)
            return None

        return articles

    def parse_detail_page(self, url):
        """解析详情页"""
        content = self.get_page_content(url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')
        article_data = {}

        try:
            # 获取标题
            title = soup.select_one('h2') or soup.select_one('.article-title')
            if title:
                article_data['title'] = title.get_text(strip=True)
                self.logger.info(f"获取到标题: {article_data['title']}")

            # 获取来源和时间
            source_time = soup.select_one('div.source') or soup.select_one('.article-info')
            if source_time:
                text = source_time.get_text(strip=True)
                self.logger.debug(f"源时间文本: {text}")
                
                # 使用更灵活的正则表达式
                source_match = re.search(r'来源[：:]\s*(.*?)(?=时间|$)', text)
                time_match = re.search(r'时间[：:]\s*(.*?)(?=来源|$)', text)
                
                if source_match:
                    article_data['source'] = source_match.group(1).strip()
                if time_match:
                    article_data['time'] = time_match.group(1).strip()

            # 获取正文内容
            content_div = soup.select_one('div#detailContent') or \
                         soup.select_one('.article-content') or \
                         soup.select_one('.content')
                         
            if content_div:
                # 获取所有段落文本
                paragraphs = content_div.find_all(['p', 'div'])
                content_text = []
                for p in paragraphs:
                    # 跳过包含"点击真相"的段落
                    if '点击真相' in p.get_text():
                        continue
                    text = p.get_text(strip=True)
                    if text:
                        content_text.append(text)
                article_data['content'] = '\n'.join(content_text)
                
                self.logger.info(f"获取到内容长度: {len(article_data['content'])}")

            # 查找"点击真相"链接
            truth_links = soup.select('#detailContent p a') or \
                         soup.select('.article-content p a') or \
                         soup.select('.content p a')
                         
            for link in truth_links:
                if '点击真相' in link.get_text():
                    href = link.get('href', '')
                    if href:
                        article_data['truth_link'] = urljoin(self.base_url, href)
                        self.logger.info(f"找到真相链接: {article_data['truth_link']}")
                        break

        except Exception as e:
            self.logger.error(f"解析详情页失败: {url}, 错误: {str(e)}", exc_info=True)
            return None

        return article_data

    def crawl(self):
        """开始爬取"""
        self.logger.info("开始爬取辟谣网站")
        
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
                    truth_detail = self.parse_detail_page(detail['truth_link'])
                    if truth_detail:
                        detail['truth_content'] = truth_detail
                results.append(detail)
            
            # 添加延时，避免请求过快
            time.sleep(2)

        # 保存结果到文件
        if results:
            try:
                with open('piyao_results.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                self.logger.info("结果已保存到 piyao_results.json")
            except Exception as e:
                self.logger.error(f"保存结果失败: {str(e)}")

        return results

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