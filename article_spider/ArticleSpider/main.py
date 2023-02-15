import os.path
import sys

from scrapy.cmdline import execute

# print(__file__)
# output： C:\Project\crawler-based-search-engine\artical_spider\ArticleSpider\main.py

# print(os.path.dirname(__file__))
# output : C:\Project\crawler-based-search-engine\artical_spider\ArticleSpider

# print(os.path.dirname(os.path.abspath(__file__)))
# output: C:\Project\crawler-based-search-engine\artical_spider\ArticleSpider

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# execute(["scrapy","crawl","cnblogs"])
execute(["scrapy", "crawl", "zhihu"])
