import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from scrapy.http import Response


class LagouSpider(CrawlSpider):
    name = "lagou"
    allowed_domains = ["www.lagou.com"]
    start_urls = ["https://www.lagou.com/"]

    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_job", follow=True),)

    def parse_start_url(self, response, **kwargs):
        return []

    def process_results(self, response: Response, results: list):
        return results

    def parse_job(self, response):
        # 解析拉勾网的职位
        item = {}
        # item["domain_id"] = response.xpath('//input[@id="sid"]/@value').get()
        # item["name"] = response.xpath('//div[@id="name"]').get()
        # item["description"] = response.xpath('//div[@id="description"]').get()
        return item
