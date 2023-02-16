from datetime import datetime

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from scrapy.http import Response
from selenium.webdriver.chrome import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from ArticleSpider.items import LagouJobItemLoader, LagouJobItem
from ArticleSpider.utils.common import get_md5


class LagouSpider(CrawlSpider):
    name = "lagou"
    allowed_domains = ["www.lagou.com"]
    start_urls = ["https://www.lagou.com/"]

    rules = {
        Rule(LinkExtractor(allow=r"zhaopin/.*"), callback="parse_job", follow=True),
        Rule(LinkExtractor(allow=r"jobs/\d+.html"), callback="parse_job", follow=True),
        Rule(LinkExtractor(allow=r"gongsi/j\d+.html"), callback="parse_job", follow=True),
    }

    def start_requests(self):
        # 入口可以模拟登录拿到cookie,selenium控制浏览器会被一些
        import undetected_chromedriver as uc
        driver = uc.Chrome()
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get('https://passport.lagou.com/login/login.html')

        # 自动化输入，自动化识别滑动验证码并拖动的整个自动化，在之后的知乎等网站上都会实现
        input("回车继续")
        cookies = driver.get_cookies()
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']

        for url in self.start_urls:
            # 将cookie交给scrapy，那么后续的请求会沿用之前请求的cookie吗？ 不会，所以需要设置一下
            # 伪装成我的一个浏览器
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }
            yield scrapy.Request(url, cookies=cookie_dict, headers=headers, dont_filter=True)

    def parse_start_url(self, response, **kwargs):
        return []

    def process_results(self, response: Response, results: list):
        return results

    def parse_job(self, response):
        # 解析拉勾网的职位
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".position-head-wrap-name::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("salary", ".job_request .salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']//span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']//span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']//span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']//span[5]/text()")

        item_loader.add_css("tags", '.position-label li::text')
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company dt a img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_value("crawl_time", datetime.now())

        job_item = item_loader.load_item()

        return job_item
