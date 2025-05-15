import os
import re
from urllib.parse import quote
from app.models.book import BookType, BookFormat

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    if not filename:
        return None
        
    # 移除路径分隔符和其他非法字符
    filename = os.path.basename(filename)
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    return filename.strip()

def get_file_type(filename):
    """根据文件名判断文件类型"""
    if not filename:
        return None
        
    ext = os.path.splitext(filename.lower())[1]
    
    # 文本类型
    if ext in ['.txt', '.epub', '.pdf', '.mobi', '.azw', '.azw3']:
        return BookType.BOOK
    # 音频类型
    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
        return BookType.AUDIO
    # 视频类型
    elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']:
        return BookType.VIDEO
    # 不支持的类型
    else:
        return None

def get_file_format(filename):
    """判断文件格式，返回BookFormat枚举值"""
    if not filename:
        return BookFormat.OTHER
        
    ext = os.path.splitext(filename.lower())[1]
    
    # 匹配具体格式
    format_map = {
        '.txt': BookFormat.TXT,
        '.epub': BookFormat.EPUB,
        '.pdf': BookFormat.PDF,
        '.mp3': BookFormat.MP3,
        '.mp4': BookFormat.MP4
    }
    
    return format_map.get(ext, BookFormat.OTHER) 