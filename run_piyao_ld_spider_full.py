#!/usr/bin/env python3
"""
完整运行辟谣网站 ld.htm 页面爬虫
爬取所有文章
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spider.piyao_ld_spider import run_spider

def main():
    """主函数"""
    print("开始完整爬取辟谣网站 ld.htm 页面...")
    print("=" * 60)
    
    # 爬取所有文章（不限制数量）
    results = run_spider(max_articles=None)
    
    if results:
        print(f"\n✅ 爬取成功！共爬取 {len(results)} 篇文章")
        print("\n文章摘要:")
        print("-" * 40)
        for i, article in enumerate(results, 1):
            title = article.get('title', '无标题')
            url = article.get('url', '无URL')
            content_length = len(article.get('content', ''))
            print(f"{i:2d}. {title}")
            print(f"    URL: {url}")
            print(f"    内容长度: {content_length} 字符")
            print()
            
        # 统计信息
        total_content_length = sum(len(article.get('content', '')) for article in results)
        avg_content_length = total_content_length // len(results) if results else 0
        
        print("=" * 60)
        print("统计信息:")
        print(f"- 总文章数: {len(results)}")
        print(f"- 总内容长度: {total_content_length:,} 字符")
        print(f"- 平均内容长度: {avg_content_length:,} 字符")
        
    else:
        print("❌ 爬取失败！请检查日志文件 piyao_ld_spider.log")
    
    print("=" * 60)
    print("爬取完成！")
    print("结果文件:")
    print("- piyao_ld_results.json (完整数据)")
    print("- piyao_ld_summary.json (摘要数据)")
    print("- piyao_ld_spider.log (日志文件)")

if __name__ == "__main__":
    main()
