#!/usr/bin/env python3
"""
导入辟谣爬虫JSON数据到数据库
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.debunk import DebunkContent

def import_piyao_json():
    """导入辟谣JSON数据到数据库"""
    json_file = os.path.join(project_root, 'piyao_results.json')
    
    print(f"查找JSON文件: {json_file}")
    
    if not os.path.exists(json_file):
        print(f"JSON文件不存在: {json_file}")
        print("请先运行辟谣爬虫生成数据文件")
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
                    truth_content = item.get('truth_content', {})
                    if not truth_content:
                        print(f"记录 {index}: 缺少truth_content，跳过")
                        skip_count += 1
                        continue
                    
                    title = truth_content.get('title', '').strip()
                    content = truth_content.get('content', '').strip()
                    
                    if not title:
                        print(f"记录 {index}: 标题为空，跳过")
                        skip_count += 1
                        continue
                    
                    # 检查是否已存在
                    existing = DebunkContent.query.filter_by(
                        title=title,
                        source='piyao.org.cn'
                    ).first()
                    
                    if existing:
                        print(f"记录 {index}: 已存在 - {title[:50]}...")
                        skip_count += 1
                        continue
                    
                    # 创建新记录
                    debunk_content = DebunkContent(
                        title=title,
                        content=content or '暂无内容',
                        source='piyao.org.cn',
                        author_name=truth_content.get('source', '辟谣平台'),
                        link=item.get('truth_link', ''),
                        region='全国',
                        search_query='辟谣',
                        status='published',
                        created_at=datetime.now()
                    )
                    
                    db.session.add(debunk_content)
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
    print("=" * 50)
    print("开始导入辟谣数据到数据库")
    print("=" * 50)
    
    success = import_piyao_json()
    
    if success:
        print("\n✅ 导入成功完成")
        return 0
    else:
        print("\n❌ 导入失败")
        return 1

if __name__ == '__main__':
    exit(main())