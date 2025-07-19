#!/usr/bin/env python3
"""
导入辟谣 ld.htm 页面爬虫JSON数据到数据库
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.debunk import DebunkContent, DebunkArticle

def import_piyao_ld_json():
    """导入辟谣 ld.htm 页面JSON数据到数据库"""
    json_file = os.path.join(project_root, 'piyao_ld_results.json')
    
    print(f"查找JSON文件: {json_file}")
    
    if not os.path.exists(json_file):
        print(f"JSON文件不存在: {json_file}")
        print("请先运行辟谣 ld.htm 页面爬虫生成数据文件")
        return False
    
    app = create_app()
    with app.app_context():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"读取到 {len(data)} 条记录")
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for index, item in enumerate(data, 1):
                try:
                    title = item.get('title', '').strip()
                    content = item.get('content', '').strip()
                    url = item.get('url', '').strip()
                    
                    if not title:
                        print(f"记录 {index}: 标题为空，跳过")
                        skip_count += 1
                        continue
                    
                    if not content:
                        print(f"记录 {index}: 内容为空，跳过")
                        skip_count += 1
                        continue
                    
                    # 检查是否已存在（基于标题）
                    existing = DebunkArticle.query.filter_by(
                        title=title
                    ).first()

                    if existing:
                        print(f"记录 {index}: 已存在 - {title[:50]}...")
                        skip_count += 1
                        continue

                    # 提取发布时间和来源信息
                    publish_time = item.get('publish_time', '')
                    source_info = item.get('source', '辟谣平台')

                    # 创建新记录 - 使用 DebunkArticle 模型
                    debunk_article = DebunkArticle(
                        title=title,
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,  # 生成摘要
                        source='piyao.org.cn',
                        author_id=1,  # 使用默认作者ID
                        status='published',
                        created_at=datetime.now(),
                        published_at=datetime.now(),  # 设置发布时间为当前时间
                        tags='辟谣,官方'  # 添加默认标签
                    )
                    
                    # 如果有发布时间信息，尝试解析
                    if publish_time:
                        try:
                            # 这里可以根据实际的时间格式进行解析
                            # 暂时使用当前时间
                            pass
                        except:
                            pass

                    db.session.add(debunk_article)
                    success_count += 1
                    print(f"记录 {index}: 成功添加 - {title[:50]}...")
                    
                except Exception as e:
                    error_count += 1
                    print(f"记录 {index}: 处理失败 - {str(e)}")
                    continue
            
            # 提交所有更改
            db.session.commit()
            print(f"\n导入完成:")
            print(f"  成功: {success_count} 条")
            print(f"  跳过: {skip_count} 条")
            print(f"  错误: {error_count} 条")
            
            return success_count > 0
            
        except json.JSONDecodeError as e:
            print(f"JSON文件格式错误: {str(e)}")
            return False
        except Exception as e:
            db.session.rollback()
            print(f"导入失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("开始导入辟谣 ld.htm 页面数据到数据库")
    print("=" * 60)
    
    success = import_piyao_ld_json()
    
    if success:
        print("\n✅ 导入成功完成")
        print("\n使用方法:")
        print("1. 运行完整爬虫: python run_piyao_ld_spider_full.py")
        print("2. 导入数据库: python scripts/import_piyao_ld_data.py")
        return 0
    else:
        print("\n❌ 导入失败")
        return 1

if __name__ == '__main__':
    exit(main())
