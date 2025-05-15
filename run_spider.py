from spider.toutiao_search.main_page import start_get_toutiao_mobile_articles_out

def main():
    """
    爬取头条辟谣文章数据
    source: burning_toutiao_article - 辟谣文章
    search_type: all - 所有类型内容
    """
    # 爬取辟谣文章
    start_get_toutiao_mobile_articles_out(
        source='burning_toutiao_article',
        search_type='all'
    )

if __name__ == '__main__':
    main() 