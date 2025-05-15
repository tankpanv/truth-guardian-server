import re
import uuid
from typing import Tuple, List
import urllib.parse

class ArticleContentSpider:
    def __init__(self, content_html: str, image_urls: List[str]):
        self.content_html = content_html
        self.image_urls = image_urls

def put_image(image_url: str) -> str:
    """
    模拟上传图像并返回编码后的 URL。
    这里应该实现上传到 OSS 的逻辑。
    """
    # 这是一个模拟函数，实际应与 OSS 交互
    return f"https://example.com/{uuid.uuid4()}.jpg"  # 示例返回值
def parse_toutiao_page_id(url:str):
        extracted_id = ''
        
        try:
            pattern = r'www\.toutiao\.com%2Fa(\d+)%2F'
            match = re.search(pattern, url)
            if match:
                extracted_id = match.group(1)  # 提取匹配的 ID
                print(f"提取的 ID: {extracted_id}")
                return extracted_id
            if extracted_id == '':
                # 使用正则表达式提取 ID
                decoded_url = re.search(r'url=([^&]+)', url)
                if decoded_url:
                    decoded_url = decoded_url.group(1)
                    decoded_url = re.sub(r'%3A', ':', decoded_url)
                    decoded_url = re.sub(r'%2F', '/', decoded_url)
                    decoded_url = re.sub(r'%3F', '?', decoded_url)
                    decoded_url = re.sub(r'%26', '&', decoded_url)

                    # 使用正则表达式提取 ID
                    match = re.search(r'/group/(\d+)/', decoded_url)
                    if match:
                        extracted_id = match.group(1)
                        print(f"提取的 ID: {extracted_id}")
                        return extracted_id
            if extracted_id == '':
                # 使用正则表达式提取 ID
                match = re.search(r'https://v3-web.toutiaovod.com/([a-z0-9]+)/', url)
                if match:
                    extracted_id = match.group(1)
                    print(f"提取的 ID: {extracted_id}")
                    return extracted_id
            if extracted_id == '':
                # 使用正则表达式提取 ID
                decoded_url = re.search(r'url=([^&]+)', url)
                if decoded_url:
                    decoded_url = decoded_url.group(1)
                    decoded_url = urllib.parse.unquote(decoded_url)  # 解码 URL

                    # 使用正则表达式提取 ID
                    match = re.search(r'/video/(\d+)/', decoded_url)
                    if match:
                        extracted_id = match.group(1)
                        print(f"提取的 ID: {extracted_id}")
                    else:
                        print("未找到 ID")

                 
        except Exception as e:
            print("未找到匹配的 ID e,url",e,url,extracted_id)
            return extracted_id
        
        print("未找到匹配的 ID,url",url,extracted_id)
        return extracted_id
 
def replace_image_url(item: ArticleContentSpider) -> Tuple[str, Exception]:
    text = item.content_html
    pattern = r'<img\s+src="([^"]+)"[^>]*>'
    re_uri = r'web_uri="[^"]*"'

    # 查找所有匹配的图片链接
    img_urls = re.findall(pattern, text)

    # 替换 web_uri
    text = re.sub(re_uri, '', text)

    # 打印和替换图片链接
    for img_url in img_urls:
        img_url = img_url.replace("&amp;", "&")
        print(img_url)
        image_name = f"image/{uuid.uuid4()}"
        encoded_url = put_image(img_url)  # 上传图像并获取编码的 URL
        text = text.replace(img_url, encoded_url)

    # 替换 item 的 image_urls
    for i in range(len(item.image_urls)):
        item.image_urls[i] = item.image_urls[i].replace("&amp;", "&")
        item.image_urls[i] = put_image(item.image_urls[i])  # 上传并获取编码的 URL

    item.content_html = text
    return text, None  # 返回处理后的 HTML 和错误（如果有的话）

# 示例使用
# article = ArticleContentSpider(
#     content_html='<img src="http://example.com/image1.jpg" /><img src="http://example.com/image2.jpg" />',
#     image_urls=["http://example.com/image3.jpg", "http://example.com/image4.jpg"]
# )

# result_html, error = replace_image_url(article)
# if error:
#     print("Error:", error)
# else:
#     print("Updated HTML:", result_html)
#     print("Updated Image URLs:", article.image_urls)
