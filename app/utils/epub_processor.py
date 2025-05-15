import os
import tempfile
import base64
import mimetypes
import uuid
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

def process_epub_to_html(epub_file, oss_service, book_id, oss_prefix):
    """
    将EPUB文件处理成单一HTML文件并上传到OSS，所有资源内联在HTML中
    
    Args:
        epub_file: 文件对象，EPUB文件
        oss_service: OSSService实例
        book_id: 书籍ID
        oss_prefix: OSS存储前缀
        
    Returns:
        tuple: (bool, str, dict) - (成功标志, HTML文件OSS路径, 额外元数据)
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # 保存上传的文件到临时目录
        epub_path = os.path.join(temp_dir, f"{book_id}.epub")
        epub_file.seek(0)
        with open(epub_path, 'wb') as f:
            f.write(epub_file.read())
        
        # 使用ebooklib读取EPUB文件
        book = epub.read_epub(epub_path)
        
        # 提取元数据
        metadata = {}
        dc_ns = 'http://purl.org/dc/elements/1.1/'
        
        for name in ['title', 'creator', 'description', 'publisher', 'identifier', 'language', 'rights', 'subject']:
            values = book.get_metadata(dc_ns, name)
            if values:
                metadata[name] = values[0][0]
        
        # 资源内容字典，用于存储所有资源的二进制数据和MIME类型
        resource_data = {}
        
        # 提取所有资源并转为base64
        for item in book.get_items():
            if item.get_type() in [ebooklib.ITEM_IMAGE, ebooklib.ITEM_STYLE, ebooklib.ITEM_FONT]:
                # 获取MIME类型
                mime_type, _ = mimetypes.guess_type(item.file_name)
                if not mime_type:
                    # 根据扩展名猜测MIME类型
                    ext = os.path.splitext(item.file_name)[1].lower()
                    if ext == '.css':
                        mime_type = 'text/css'
                    elif ext in ['.ttf', '.otf']:
                        mime_type = 'font/' + ext[1:]
                    elif ext == '.svg':
                        mime_type = 'image/svg+xml'
                    else:
                        mime_type = 'application/octet-stream'
                
                # 添加到资源字典
                resource_data[item.file_name] = {
                    'content': item.content,
                    'mime_type': mime_type
                }
        
        # 封面处理
        cover_data = None
        cover_mime = None
        
        # 尝试查找封面
        for item in book.get_items_of_type(ebooklib.ITEM_COVER):
            cover_data = item.content
            cover_mime, _ = mimetypes.guess_type(item.file_name)
            break
            
        # 如果没有专门的封面，尝试从图片中查找
        if not cover_data:
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if 'cover' in item.file_name.lower():
                    cover_data = item.content
                    cover_mime, _ = mimetypes.guess_type(item.file_name)
                    break
        
        # 处理文档内容
        chapters = []
        toc_items = []
        
        # CSS内容收集
        css_content = []
        for item_name, data in resource_data.items():
            if data['mime_type'] == 'text/css':
                try:
                    css_text = data['content'].decode('utf-8')
                    css_content.append(css_text)
                except UnicodeDecodeError:
                    try:
                        css_text = data['content'].decode('latin-1')
                        css_content.append(css_text)
                    except:
                        print(f"无法解码CSS: {item_name}")
        
        # 处理文档项
        for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
            # 获取文档内容
            try:
                content = item.content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = item.content.decode('utf-16')
                except UnicodeDecodeError:
                    content = item.content.decode('latin-1', errors='replace')
            
            # 使用BeautifulSoup处理HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 处理图片和资源引用，将它们转换为内联资源
            for img in soup.find_all('img'):
                if img.get('src'):
                    src = img['src']
                    # 查找匹配的资源
                    for resource_path, resource in resource_data.items():
                        if resource_path.endswith(src) or src.endswith(resource_path):
                            # 转换为base64内联图片
                            if resource['mime_type'].startswith('image/'):
                                base64_data = base64.b64encode(resource['content']).decode('utf-8')
                                img['src'] = f"data:{resource['mime_type']};base64,{base64_data}"
                                break
            
            # 移除外部CSS链接，因为我们将在最终HTML中内联所有CSS
            for link in soup.find_all('link', rel='stylesheet'):
                link.decompose()
            
            # 添加章节ID和标题
            chapter_id = f"chapter_{i}"
            chapter_title = soup.title.string if soup.title else f"章节 {i+1}"
            toc_items.append(f'<li><a href="#{chapter_id}">{chapter_title}</a></li>')
            
            # 获取正文内容
            chapter_content = str(soup.body.decode_contents()) if soup.body else str(soup)
            chapters.append(f'<div id="{chapter_id}" class="chapter"><h2>{chapter_title}</h2>{chapter_content}</div>')
        
        # 创建完整的HTML内容
        # 包含所有CSS和内联资源
        cover_html = ''
        if cover_data and cover_mime:
            base64_cover = base64.b64encode(cover_data).decode('utf-8')
            cover_html = f'<div class="cover"><img src="data:{cover_mime};base64,{base64_cover}" alt="封面"></div>'
        
        title = metadata.get('title', '未知标题')
        
        # 创建HTML模板，包含所有内联CSS
        html_template = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                /* 基础样式 */
                body {{ 
                    font-family: 'Noto Serif', serif; 
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #fcfcfc;
                    color: #333;
                }}
                h1 {{ 
                    text-align: center; 
                    margin-bottom: 1em;
                    color: #2c3e50;
                }}
                h2 {{ 
                    border-bottom: 1px solid #eee;
                    padding-bottom: 0.5em;
                    color: #2c3e50;
                }}
                nav {{ 
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .chapter {{ 
                    margin-bottom: 2em;
                    border-bottom: 1px dashed #ddd;
                    padding-bottom: 1em;
                }}
                img {{ 
                    max-width: 100%; 
                    height: auto;
                    display: block;
                    margin: 1em auto;
                    border-radius: 3px;
                }}
                .cover img {{ 
                    max-height: 500px; 
                    margin: 0 auto;
                    display: block;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                
                /* 从EPUB提取的CSS */
                {' '.join(css_content)}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {cover_html}
            <nav>
                <h2>目录</h2>
                <ul>
                    {''.join(toc_items)}
                </ul>
            </nav>
            <div class="content">
                {''.join(chapters)}
            </div>
            <footer>
                <p>来源: {metadata.get('creator', '未知作者')}</p>
                <p>转换自EPUB格式</p>
            </footer>
        </body>
        </html>
        """
        
        # 保存完整HTML到临时文件
        html_path = os.path.join(temp_dir, f"{book_id}_complete.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        # 上传单一HTML文件到OSS
        html_oss_path = f"{oss_prefix}/complete.html"
        with open(html_path, 'rb') as f:
            upload_success = oss_service.upload_file(f, html_oss_path)
            if not upload_success:
                return False, "", {}
        
        # 返回处理结果
        extra_data = {
            "is_epub_html": True,
            "original_metadata": metadata,
            "complete_html": True,
            "chapters_count": len(chapters)
        }
        
        return True, html_oss_path, extra_data
        
    except Exception as e:
        print(f"EPUB处理错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, "", {"error": str(e)}
    
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True) 