"""
辟谣网站 ld.htm 页面爬虫
爬取 https://www.piyao.org.cn/ld.htm 列表页面的文章
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin
import json
import os

class PiyaoLdSpider:
    def __init__(self):
        self.base_url = "https://www.piyao.org.cn"
        self.list_url = "https://www.piyao.org.cn/ld.htm"
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
        """解析列表页面，获取文章链接"""
        content = self.get_page_content(self.list_url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        
        try:
            # 使用指定的选择器获取文章链接
            # 首先尝试精确的选择器
            article_links = soup.select('#list > li > h2 > a')
            
            # 如果没有找到，尝试更宽泛的选择器
            if not article_links:
                article_links = soup.select('#list li h2 a') or \
                               soup.select('#list li a') or \
                               soup.select('.list li a')
                               
            self.logger.info(f"找到 {len(article_links)} 篇文章链接")
            
            for link in article_links:
                href = link.get('href', '')
                if not href:
                    continue
                    
                # 构建完整URL
                if href.startswith('http'):
                    full_url = href
                else:
                    # 处理相对路径
                    if href.startswith('/'):
                        href = href[1:]
                    full_url = urljoin(self.base_url, href)
                
                title = link.get_text(strip=True)
                
                # 获取其他属性
                aria_title = link.get('aria-arttitle', '')
                target = link.get('target', '')
                
                self.logger.info(f"解析到文章: {title} - {full_url}")
                
                articles.append({
                    'title': title,
                    'url': full_url,
                    'aria_title': aria_title,
                    'target': target
                })
                
        except Exception as e:
            self.logger.error(f"解析列表页失败: {str(e)}", exc_info=True)
            return None

        return articles

    def parse_detail_page(self, url):
        """解析详情页面，获取标题和内容"""
        content = self.get_page_content(url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')
        article_data = {'url': url}

        try:
            # 使用指定的选择器获取标题
            title_element = soup.select_one("body > div.content > div.con_left.left > div > div.con_tit > h2")
            if title_element:
                article_data['title'] = title_element.get_text(strip=True)
                self.logger.info(f"获取到标题: {article_data['title']}")
            else:
                # 备用选择器
                title_element = soup.select_one("h2") or soup.select_one(".con_tit h2")
                if title_element:
                    article_data['title'] = title_element.get_text(strip=True)
                    self.logger.info(f"使用备用选择器获取到标题: {article_data['title']}")

            # 使用指定的选择器获取内容
            content_element = soup.select_one("body > div.content > div.con_left.left > div > div.con_txt")
            if content_element:
                # 获取所有文本内容，保持段落结构
                paragraphs = content_element.find_all(['p', 'div'])
                if paragraphs:
                    content_text = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text:
                            content_text.append(text)
                    article_data['content'] = '\n'.join(content_text)
                else:
                    # 如果没有段落，直接获取文本
                    article_data['content'] = content_element.get_text(strip=True)
                
                self.logger.info(f"获取到内容长度: {len(article_data['content'])}")
            else:
                # 备用选择器
                content_element = soup.select_one(".con_txt") or soup.select_one(".content")
                if content_element:
                    article_data['content'] = content_element.get_text(strip=True)
                    self.logger.info(f"使用备用选择器获取到内容长度: {len(article_data['content'])}")

            # 获取发布时间（如果存在）
            time_element = soup.select_one(".con_tit .time") or soup.select_one(".time")
            if time_element:
                article_data['publish_time'] = time_element.get_text(strip=True)

            # 获取来源（如果存在）
            source_element = soup.select_one(".con_tit .source") or soup.select_one(".source")
            if source_element:
                article_data['source'] = source_element.get_text(strip=True)

        except Exception as e:
            self.logger.error(f"解析详情页失败: {url}, 错误: {str(e)}", exc_info=True)
            return None

        return article_data

    def crawl(self, max_articles=None):
        """开始爬取"""
        self.logger.info("开始爬取辟谣网站 ld.htm 页面")
        
        # 获取列表页文章
        articles = self.parse_list_page()
        if not articles:
            self.logger.error("获取文章列表失败")
            return None

        # 限制爬取数量
        if max_articles and len(articles) > max_articles:
            articles = articles[:max_articles]
            self.logger.info(f"限制爬取数量为 {max_articles} 篇")

        results = []
        for index, article in enumerate(articles, 1):
            self.logger.info(f"正在爬取第 {index}/{len(articles)} 篇文章: {article['title']}")
            
            # 获取文章详情
            detail = self.parse_detail_page(article['url'])
            if detail:
                # 合并列表页和详情页的信息
                detail.update({
                    'list_title': article['title'],
                    'aria_title': article.get('aria_title', ''),
                    'target': article.get('target', '')
                })
                results.append(detail)
            else:
                self.logger.warning(f"跳过文章: {article['title']}")
            
            # 添加延时，避免请求过快
            time.sleep(2)

        # 保存结果到文件
        if results:
            try:
                output_file = 'piyao_ld_results.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                self.logger.info(f"结果已保存到 {output_file}")
                
                # 同时保存一个简化版本，只包含标题和URL
                summary_file = 'piyao_ld_summary.json'
                summary = [{'title': r.get('title', ''), 'url': r.get('url', '')} for r in results]
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                self.logger.info(f"摘要已保存到 {summary_file}")
                
            except Exception as e:
                self.logger.error(f"保存结果失败: {str(e)}")

        return results

def run_spider(max_articles=None):
    """运行爬虫"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('piyao_ld_spider.log', encoding='utf-8')
        ]
    )
    
    spider = PiyaoLdSpider()
    results = spider.crawl(max_articles=max_articles)
    
    if results:
        logging.info(f"成功爬取 {len(results)} 篇文章")
        return results
    else:
        logging.error("爬取失败")
        return None

if __name__ == "__main__":
    # 可以通过参数限制爬取数量，避免第一次测试时爬取太多
    run_spider(max_articles=5)  # 先爬取5篇测试
