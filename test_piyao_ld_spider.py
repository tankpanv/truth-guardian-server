#!/usr/bin/env python3
"""
测试辟谣网站 ld.htm 页面爬虫
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spider.piyao_ld_spider import run_spider

def main():
    """主函数"""
    print("开始测试辟谣网站 ld.htm 页面爬虫...")
    print("=" * 50)
    
    # 先爬取少量文章进行测试
    results = run_spider(max_articles=3)
    
    if results:
        print(f"\n✅ 测试成功！共爬取 {len(results)} 篇文章")
        print("\n文章摘要:")
        print("-" * 30)
        for i, article in enumerate(results, 1):
            title = article.get('title', '无标题')
            url = article.get('url', '无URL')
            content_length = len(article.get('content', ''))
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   内容长度: {content_length} 字符")
            print()
    else:
        print("❌ 测试失败！请检查日志文件 piyao_ld_spider.log")
    
    print("=" * 50)
    print("测试完成！")
    print("结果文件:")
    print("- piyao_ld_results.json (完整数据)")
    print("- piyao_ld_summary.json (摘要数据)")
    print("- piyao_ld_spider.log (日志文件)")

if __name__ == "__main__":
    main()
