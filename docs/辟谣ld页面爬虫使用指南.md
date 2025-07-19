# 辟谣网站 ld.htm 页面爬虫使用指南

## 概述

这个爬虫专门用于爬取 https://www.piyao.org.cn/ld.htm 页面的辟谣文章列表和详细内容。

## 功能特点

- ✅ 自动获取列表页面的所有文章链接
- ✅ 使用指定的CSS选择器精确提取标题和内容
- ✅ 支持限制爬取数量（用于测试）
- ✅ 自动保存为JSON格式
- ✅ 完整的日志记录
- ✅ 支持导入到数据库

## 文件结构

```
├── spider/
│   └── piyao_ld_spider.py          # 主爬虫类
├── test_piyao_ld_spider.py         # 测试脚本（爬取3篇）
├── run_piyao_ld_spider_full.py     # 完整爬虫脚本（爬取所有）
├── scripts/
│   └── import_piyao_ld_data.py     # 数据库导入脚本
└── docs/
    └── 辟谣ld页面爬虫使用指南.md    # 本文档
```

## 使用方法

### 1. 环境准备

确保已安装依赖：
```bash
pip install -r requirements.txt
```

激活虚拟环境（如果使用）：
```bash
source .venv/bin/activate
```

### 2. 测试爬虫（推荐先测试）

```bash
python test_piyao_ld_spider.py
```

这会爬取前3篇文章进行测试，确保爬虫正常工作。

### 3. 完整爬取

```bash
python run_piyao_ld_spider_full.py
```

这会爬取所有文章（通常20篇左右）。

### 4. 导入数据库

```bash
python scripts/import_piyao_ld_data.py
```

将爬取的数据导入到数据库中。

## 输出文件

运行爬虫后会生成以下文件：

- `piyao_ld_results.json` - 完整的爬取数据
- `piyao_ld_summary.json` - 文章摘要（仅标题和URL）
- `piyao_ld_spider.log` - 详细的运行日志

## 数据格式

### JSON数据结构

```json
[
  {
    "url": "https://www.piyao.org.cn/20250717/xxx/c.html",
    "title": "文章标题",
    "content": "文章完整内容...",
    "list_title": "列表页显示的标题",
    "aria_title": "aria-arttitle属性值",
    "target": "_blank",
    "publish_time": "发布时间（如果有）",
    "source": "来源（如果有）"
  }
]
```

## 技术细节

### CSS选择器

爬虫使用以下CSS选择器：

**列表页文章链接：**
- 主选择器：`#list > li > h2 > a`
- 备用选择器：`#list li h2 a`, `#list li a`, `.list li a`

**详情页标题：**
- 主选择器：`body > div.content > div.con_left.left > div > div.con_tit > h2`
- 备用选择器：`h2`, `.con_tit h2`

**详情页内容：**
- 主选择器：`body > div.content > div.con_left.left > div > div.con_txt`
- 备用选择器：`.con_txt`, `.content`

### 爬取策略

- 每次请求间隔2秒，避免对服务器造成压力
- 使用标准的浏览器User-Agent
- 自动处理相对路径和绝对路径
- 错误重试和异常处理

## 常见问题

### Q: 为什么只爬取了3篇文章？
A: 如果使用的是测试脚本 `test_piyao_ld_spider.py`，它默认只爬取3篇用于测试。使用 `run_piyao_ld_spider_full.py` 可以爬取所有文章。

### Q: 爬虫运行失败怎么办？
A: 
1. 检查网络连接
2. 查看日志文件 `piyao_ld_spider.log`
3. 确认网站结构是否发生变化
4. 检查依赖是否正确安装

### Q: 如何修改爬取数量？
A: 在调用 `run_spider()` 时传入 `max_articles` 参数：
```python
results = run_spider(max_articles=10)  # 只爬取10篇
```

### Q: 数据导入失败怎么办？
A: 
1. 确保数据库连接正常
2. 检查JSON文件是否存在且格式正确
3. 查看错误日志确定具体问题

## 自定义配置

### 修改请求头

在 `spider/piyao_ld_spider.py` 中修改 `headers` 字典：

```python
self.headers = {
    'User-Agent': '你的User-Agent',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    # 添加其他请求头
}
```

### 修改延时

修改 `crawl()` 方法中的延时：

```python
time.sleep(1)  # 改为1秒延时
```

### 添加新的选择器

如果网站结构发生变化，可以在相应方法中添加新的选择器：

```python
# 在 parse_detail_page 方法中添加
title_element = soup.select_one("新的标题选择器") or \
               soup.select_one("备用选择器")
```

## 维护说明

- 定期检查网站结构是否发生变化
- 根据需要调整CSS选择器
- 监控爬取成功率和数据质量
- 及时更新User-Agent等请求头信息

## 联系支持

如有问题或建议，请查看项目文档或联系开发团队。
