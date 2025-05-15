"""爬虫设置文件

此文件包含Scrapy爬虫的所有设置
"""

# 爬虫名称
BOT_NAME = 'truth_guardian'

# 用户代理
USER_AGENT = 'Truth-Guardian-Bot/1.0 (+https://truth-guardian.com)'

# 遵守robots.txt规则
ROBOTSTXT_OBEY = True

# 请求延迟
DOWNLOAD_DELAY = 2

# 并发请求数
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 超时设置
DOWNLOAD_TIMEOUT = 30

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 启用Cookie
COOKIES_ENABLED = True

# 请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 启用中间件
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

# 下载中间件
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 130,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 900,
}

# 项目管道
ITEM_PIPELINES = {
    'app.scraper.pipelines.data_clean.DataCleanPipeline': 300,
    'app.scraper.pipelines.duplicate_filter.DuplicateFilterPipeline': 500,
    'app.scraper.pipelines.db_storage.DatabaseStoragePipeline': 800,
}

# 允许的HTTP状态码
HTTPERROR_ALLOWED_CODES = [404]

# 自动限流
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# 断点续爬
JOBDIR = 'crawls/truth_guardian-1'

# 日志级别
LOG_LEVEL = 'DEBUG'

# 日志配置
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# 启用详细的HTTP请求和响应日志
LOG_ENABLED = True
LOG_STDOUT = True

# 添加自定义设置
TRUTH_GUARDIAN_SETTINGS = {
    # 爬取周期（小时）
    'CRAWL_INTERVAL': 2,
    
    # 数据源列表
    'SOURCES': {
        'news': [
            'news.sina.com.cn',
            'news.163.com',
            'news.qq.com',
            'news.ifeng.com',
            'news.sohu.com'
        ],
        'government': [
            'www.gov.cn',
            'www.nhc.gov.cn',
            'www.moe.gov.cn',
            'www.mfa.gov.cn',
            'www.samr.gov.cn'
        ],
        'rumor': [
            'piyao.org.cn',
            'fact.qq.com',
            'jiaozhen.com',
            'www.piyao.org.cn'
        ],
        'social': {
            'weibo': {
                'url': 'https://weibo.com',
                'api': 'https://m.weibo.cn/api/container/getIndex',
                'comment_api': 'https://m.weibo.cn/comments/hotflow'
            }
        }
    },
    
    # API密钥和配置
    'API_KEYS': {
        'weibo': {
            # 在此处填入您的微博Cookie
            # 登录 https://m.weibo.cn 后从浏览器开发者工具中获取
            # 需要包含以下字段：SUB, SUBP, _T_WM, XSRF-TOKEN, WBPSESS
            'cookie': 'WEIBOCN_FROM=1110006030; _T_WM=62081816904; XSRF-TOKEN=b28d84; MLOGIN=0; mweibo_short_token=2d08df35e9; M_WEIBOCN_PARAMS=lfid%3D102803%26luicode%3D20000174%26uicode%3D20000174',  # 例如：'SUB=xxx; SUBP=xxx; _T_WM=xxx; XSRF-TOKEN=xxx; WBPSESS=xxx'
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'timeout': 30
        }
    },
    
    # 关键词过滤
    'KEYWORDS': [
        '疫情', '病毒', '肺炎', '疫苗', '核酸', '防控',
        '谣言', '辟谣', '真相', '事实', '真实',
        '安全', '健康', '预防', '感染', '传播',
        '官方', '权威', '发布', '通报', '声明'
    ]
} 