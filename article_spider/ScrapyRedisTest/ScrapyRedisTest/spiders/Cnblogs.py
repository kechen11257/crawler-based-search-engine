import scrapy
from scrapy.http import Request
from urllib import parse

from scrapy_redis.spiders import RedisSpider

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class CnblogsSpider(RedisSpider):
    name = "cnblogs"
    allowed_domains = ["news.cnblogs.com"]
    redis_key = 'cnblogs:start_urls'

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    def start_requests(self):
        # 入口可以模拟登录拿到cookie,selenium控制浏览器会被一些
        import undetected_chromedriver as uc
        driver = uc.Chrome()
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get('https://account.cnblogs.com/signin')

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

    def parse(self, response):
        # url = response.xpath('//div[@id="news_list"]//h2/a/@href').extract_first("")
        # post_node = response.xpath('//div[@id="news_list"]//h2/a/@href').extract_first("")

        """
        1. 获取新闻列表页中的新闻url并交给scrapy进行下载后调用相应的解析方法
        2. 获取下一页的url并交给scrapy进行下载，下载完成后交给parse继续跟进
        """
        # post_nodes = response.css('#news_list .news_block').extract_first("") 为了debug简单
        post_nodes = response.css('#news_list .news_block')
        # 1.获取新闻列表页中的新闻url并交给scrapy进行下载后调用相应的解析方法
        for post_node in post_nodes:
            image_url = post_node.css('.entry_summary a img::attr(src)').extract_first("")
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            # 得到一个url就yield一个Request交给scrapy进行下载： 深度优先的抓取方法
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        # 2. 获取下一页的url
        """ xpath提取方法
        next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")
        yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
        """

        # 为了调试简单，先把它注释掉
        next_url = response.css("div.pager a:last-child::text").extract_first("")
        # next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")
        if next_url == "Next >":
            next_url = response.css("div.pager a:last-child::attr(href)").extract_first("")
            # yield一个Request交给scrapy进行下载，下载完成后交给parse继续跟进
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        pass
