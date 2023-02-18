# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import UserAgent

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from ArticleSpider.tools.crawl_xici_ip import GetIP


class ArticlespiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ArticlespiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RandomUserAgentMiddlware(object):
    # 随机更换user-agent
    # 相当于java里面的构造函数
    def __init__(self, crawler):
        super(RandomUserAgentMiddlware, self).__init__()
        # from fake_useragent import UserAgent
        self.ua = UserAgent()
        # If the RANDOM_UA_TYPE setting is not found in the crawler settings, it defaults to the string "random".
        self.ua_type = crawler.settings.get("RANDOM_UA_TYPE", "random")

    @classmethod
    # 类似于之前的from_setting，可以调用setting里面的值
    # to instantiate the class
    # It returns an instance of the class, passing the crawler object as a parameter.
    def from_crawler(cls, crawler):
        return cls(crawler)

    # is called for each request that is sent by the spider.
    # It randomly selects a user agent and adds it to the request headers.
    def process_request(self, request, spider):
        def get_ua():
            # returns a random user agent based on the value of ua_type
            return getattr(self.ua, self.ua_type)

        # request.headers.setdefault('User-Agent', self.ua.random)
        #  randomly selects a user agent and adds it to the request headers
        request.headers.setdefault('User-Agent', get_ua())


class RandomProxyMiddleware(object):
    # 动态设置ip代理
    def process_request(self, request, spider):
        # instantiates a GetIP object
        get_ip = GetIP()
        #  the meta attribute is a dictionary that is used to pass data between Scrapy components,
        #  such as between spider callbacks, between middleware components and downloader, etc.
        request.meta["proxy"] = get_ip.get_random_ip()


from scrapy.http import HtmlResponse

# 同步方法，不推荐
class JSPageMiddleware(object):
    # 通过chrome请求动态网页
    def process_request(self, request, spider):
        if spider.name == "lagou":
            # browser = webdriver.Chrome(executable_path="D:/Temp/chromedriver.exe")
            spider.browser.get(request.url)
            import time
            time.sleep(3)
            print("访问:{0}".format(request.url))

            callback = request.callback
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source, encoding="utf-8",
                                request=request)

# from pyvirtualdisplay import Display
# display = Display(visible=0, size=(800, 600))
# display.start()
#
# browser = webdriver.Chrome()
# browser.get()

# print (crawl_ips())
if __name__ == "__main__":
    get_ip = GetIP()
    get_ip.get_random_ip()
