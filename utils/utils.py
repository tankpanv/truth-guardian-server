import os
import shutil
import hashlib


def delete_all_in_directory(directory):
    # 确保目录存在
    if os.path.exists(directory):
        # 遍历目录中的所有元素
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            # 如果是目录，使用 shutil.rmtree 删除；如果是文件，使用 os.remove 删除
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除目录及其内容
            else:
                os.remove(item_path)  # 删除文件
        print(f"已删除 {directory} 中的所有元素。")
    else:
        print(f"目录 {directory} 不存在。")
def safe_str_to_int(value):
    """
    尝试将字符串转换为整数。如果转换失败，返回 0。
    
    :param value: 要转换的字符串
    :return: 转换后的整数或 0
    """
    try:
        if type(value) == int:
            return value
        return int(value)
    except (ValueError, TypeError):
        print(f"无法将 {value} 转换为整数。")
        return 0
def encrypt_string(password: str) -> str:
    if password == "":
        return ""
    
    # 将密码转换为字节
    password_bytes = password.encode('utf-8')
    
    # 计算 SHA-256 哈希值
    hash_object = hashlib.sha256(password_bytes)
    
    # 返回哈希值的十六进制表示
    hash_hex = hash_object.hexdigest()
    
    print(hash_hex)  # 打印哈希值
    return hash_hex
def convert_text_count_to_int(likes_text):
    if type(likes_text) == int:
        return likes_text
    
    print(likes_text)
    if likes_text is None:
        return 0
    
    if likes_text == "评论":
        return 0
    if likes_text == "点赞":
        return 0
    if likes_text == "收藏":
        return 0
    try :
        if '万' in likes_text:
            return int(float(likes_text.replace('万', '').strip()) * 10000)
        elif '千' in likes_text:
            return int(float(likes_text.replace('千', '').strip()) * 1000)
        elif '亿' in likes_text:
            return int(float(likes_text.replace('亿', '').strip()) * 100000000)
        elif 'w' in likes_text:
            return int(float(likes_text.replace('w', '').strip()) * 10000)
        elif 'k' in likes_text:
            return int(float(likes_text.replace('k', '').strip()) * 1000)
        else:
            return int(likes_text.strip())
    except Exception as e:
        print(e)
        return 0
def get_full_url(url):
    """确保 URL 以 https 开头"""
    if not url.startswith("http"):
        return "https:" + url
    return url