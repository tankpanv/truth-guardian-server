"""爬虫数据管道包

包含用于数据清洗、去重和数据库存储的管道类

管道流程：
1. DataCleanPipeline：清洗爬取的数据
   - 去除HTML标签、多余空白字符、特殊字符等
   - 过滤广告内容
   - 检查标题和内容是否为空

2. DuplicateFilterPipeline：过滤重复数据
   - 使用指纹算法检测重复项
   - 与数据库中已有数据比较，避免重复存储

3. DatabaseStoragePipeline：存储到数据库
   - 根据数据类型存储到对应的表
   - 支持新闻、谣言和社交媒体数据
   - 提供更新已有记录的功能

使用方法：
在settings.py中已配置管道及优先级：
ITEM_PIPELINES = {
    'app.scraper.pipelines.data_clean.DataCleanPipeline': 300,
    'app.scraper.pipelines.duplicate_filter.DuplicateFilterPipeline': 500,
    'app.scraper.pipelines.db_storage.DatabaseStoragePipeline': 800,
}
"""

from app.scraper.pipelines.data_clean import DataCleanPipeline
from app.scraper.pipelines.duplicate_filter import DuplicateFilterPipeline
from app.scraper.pipelines.db_storage import DatabaseStoragePipeline

__all__ = [
    'DataCleanPipeline',
    'DuplicateFilterPipeline',
    'DatabaseStoragePipeline'
] 