import qrcode
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

def generate_book_qrcode(book_id, title, output_path=None):
    """
    生成带有标题的书籍二维码
    
    Args:
        book_id: 书籍ID
        title: 书籍标题
        output_path: 输出路径，如果为None则返回字节流
        
    Returns:
        字节流或保存路径
    """
    # 创建二维码内容（前端URL）
   
        # 构建小程序路径
    # 格式: pages/bookDetail/bookDetail?id=book_id
    path = f"pages/bookDetail/bookDetail?id={book_id}"
    
    # 构建小程序码数据
    # 参考: https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/qr-code.html
    data = {
        "path": path,  # 扫描后打开的页面路径
        "scene": f"id={book_id}",  # scene参数可以传递少量数据
        "width": 280,  # 二维码宽度
        "auto_color": False,
        "is_hyaline": False
    }
    
    # 生成二维码图像
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    
    # 添加完整的URL (使用微信小程序的URL Scheme)
    # 注意: 替换 YOUR_APPID 为您的小程序 AppID
    appId = "wx9ca5f6db5943bfe5"
    qr.add_data(f"weixin://dl/business/?t={appId}&path={path}")
    qr.make(fit=True)
    # 生成二维码图像
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # 获取二维码尺寸
    qr_width, qr_height = qr_img.size
    
    # 创建一个带有边距的白色背景
    margin = 20
    canvas_width = qr_width + 2 * margin
    canvas_height = qr_height + margin + 40  # 额外空间用于标题
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    
    # 将QR码粘贴到背景上，注意这里要指定位置
    canvas.paste(qr_img, (margin, margin))
    
    # 添加标题文本
    draw = ImageDraw.Draw(canvas)
    
    # 尝试加载字体，如果失败则使用默认字体
    try:
        # 尝试使用系统字体
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Ubuntu常见路径
        if not os.path.exists(font_path):
            # 尝试其他常见路径
            font_path = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 16)
        else:
            # 如果找不到字体文件，使用默认字体
            font = ImageFont.load_default()
    except Exception:
        # 出错时使用默认字体
        font = ImageFont.load_default()
    
    # 限制标题长度，避免超出图像边界
    max_title_len = 20
    if len(title) > max_title_len:
        title = title[:max_title_len-3] + "..."
    
    # 计算文本位置使其居中
    text_width = draw.textlength(title, font=font)
    text_position = ((canvas_width - text_width) // 2, qr_height + margin + 10)
    
    # 绘制文本
    draw.text(text_position, title, fill="black", font=font)
    
    # 根据需要输出
    if output_path:
        canvas.save(output_path)
        return output_path
    else:
        # 转换为字节流
        img_byte_arr = io.BytesIO()
        canvas.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

def generate_qrcode(content, output_path=None):
    """
    生成简单的二维码
    
    Args:
        content: 二维码内容
        output_path: 输出路径，如果为None则返回字节流
        
    Returns:
        字节流或保存路径
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    if output_path:
        qr_img.save(output_path)
        return output_path
    else:
        img_byte_arr = io.BytesIO()
        qr_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

def batch_generate_qrcodes(books_data_file, output_dir="qrcodes"):
    """
    批量为书籍生成二维码
    
    参数:
    books_data_file (str): 包含书籍数据的JSON文件路径
    output_dir (str): 输出目录
    """
    with open(books_data_file, 'r', encoding='utf-8') as f:
        books = json.load(f)
    
    for book in books:
        book_id = book.get('id')
        book_title = book.get('title', '')
        if book_id:
            generate_book_qrcode(book_id, book_title, output_dir)
        else:
            print(f"警告: 书籍缺少ID: {book}")
    
    print(f"已完成所有二维码生成，共 {len(books)} 本书")

# 示例用法
if __name__ == "__main__":
    # 单本书的二维码
    generate_book_qrcode("1111", "测试书籍标题", "test_qr.png")
    print("二维码已保存到 test_qr.png")
    
    # 批量生成二维码 (假设有一个books.json文件)
    # books.json格式示例: [{"id": "1", "title": "三国演义"}, {"id": "2", "title": "红楼梦"}]
    # batch_generate_qrcodes("books.json")