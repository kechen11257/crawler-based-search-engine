import json
import re
from urllib import parse

import scrapy
from scrapy.loader import ItemLoader
from scrapy import Request
import requests
from ArticleSpider.items import CnblogsArticleItem
from ArticleSpider.utils import common
from ArticleSpider.items import ArticleItemLoader
from ArticleSpider.utils.common import get_md5

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class CnblogsSpider(scrapy.Spider):
    name = "cnblogs"
    allowed_domains = ["news.cnblogs.com"]
    start_urls = ["http://news.cnblogs.com/"]
    custom_settings = {
        "COOKIES_ENABLED" : True
    }

    def start_requests(self):
        #入口可以模拟登录拿到cookie,selenium控制浏览器会被一些
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
            #将cookie交给scrapy，那么后续的请求会沿用之前请求的cookie吗？ 不会，所以需要设置一下
            # 伪装成我的一个浏览器
            headers = {
                'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }
            yield scrapy.Request(url, cookies = cookie_dict, headers = headers, dont_filter = True)

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
        """
        # 为了调试简单，先把它注释掉
        next_url = response.css("div.pager a:last-child::text").extract_first("")
        # next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")
        if next_url == "Next >":
            next_url = response.css("div.pager a:last-child::attr(href)").extract_first("")
            # yield一个Request交给scrapy进行下载，下载完成后交给parse继续跟进
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
        """

    """ parse_detail版本1/3 采用同步的库
    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)",response.url)
        if match_re:
            title = response.css("#news_title a::text").extract_first("")
            created_date = response.css("#news_info .time::text").extract_first("")
            content = response.css("#news_content ").extract()[0]
            tag_list = response.css(".news_tags a::text").extract()
            # 因为tag是一个list，数据库没有这种储存方式，所以要变成一个字符串
            tags = ",".join(tag_list)

            post_id = match_re.group(1)
            
            但是对于很多异步的IO框架来说，尽量不要取使用同步的方法或者同步的库，这个request就是一个同步的库，
            所以在上面虽然能够完成我们的功能，但是实际上不建议这样做，这样做的好处是因为非常的简单.
            # html = requests.get(parse.urljoin(response.url, "NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
            html = requests.get(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
            # 对html进行一个解析：
            j_data = json.loads(html.text)

            diggcount = j_data["DiggCount"]
            totalview = j_data["TotalView"]
            commentcount = j_data["CommentCount"]
    """

    """ parse_detail版本2/3 采用异步的库
    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)",response.url)
        if match_re:
            post_id = match_re.group(1)
            
            '''css选择器模式
            title = response.css("#news_title a::text").extract_first("")
            created_date = response.css("#news_info .time::text").extract_first("")
            content = response.css("#news_content ").extract()[0]
            tag_list = response.css(".news_tags a::text").extract()
            # 因为tag是一个list，数据库没有这种储存方式，所以要变成一个字符串
            tags = ",".join(tag_list)
            '''
            
            article_item = CnblogsArticleItem()
            # xpath模式
            title = response.xpath("//*[@id='news_title']//a/text()").extract_first("")

            created_date = response.css("//*[@id='news_info']//*[@class='time']/text()").extract_first("")
            match_re = re.match(".*?(/d+.*)", created_date)
            if match_re:
                created_date = match_re.group(1)

            content = response.css("//*[@id='news_content']").extract()[0]
            tag_list = response.css("//*[@class='news_tags']//a/text()").extract()
            tags = ",".join(tag_list)

            # 动态生成的值
            article_item["title"] = title
            article_item["created_date"] = created_date
            article_item["url"] = response.url
            # 一定要注意是传一个list进去
            if response.meta.get("front_image_url",""):
                article_item["front_image_url"] = [response.meta.get("front_image_url", "")]
            else:
                article_item["front_image_url"] = []

            # article_item["front_image_path"] = title
            article_item["content"] = content
            article_item["tags"] = tags

            # yield Request(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)), callback=self.parse.nums)
            # 让article_item继续传递：
            yield Request(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                          meta={"article_item":article_item},callback=self.parse.nums)
    """

    # parse_detail 版本3/3 采用itemloader让代码更加简单且容易维护
    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)", response.url)
        if match_re:
            post_id = match_re.group(1)

        item_loader = ArticleItemLoader(item=CnblogsArticleItem(), response=response)
        item_loader.add_css("title", "#news_title a::text")
        item_loader.add_css("created_date", "#news_info .time::text")
        item_loader.add_css("content", "#news_content")
        item_loader.add_css("tags", ".news_tags a::text")
        item_loader.add_value("url", response.url)
        if response.meta.get("front_image_url", []):
            item_loader.add_value("front_image_url", response.meta.get("front_image_url", []))

        # article_item = item_loader.load_item()
        print(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
        # 让article_item继续传递：
        #yield Request(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
        #              meta={"article_item": article_item}, callback=self.parse.nums)
        yield Request(url=parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                      meta={"article_item": item_loader, "url": response.url}, callback=self.parse_nums)

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        # article_item = response.meta.get("article_item", "")
        item_loader = response.meta.get("article_item", "")

        diggcount = j_data["DiggCount"]
        totalview = j_data["TotalView"]
        commentcount = j_data["CommentCount"]

        """
        article_item["diggcount"] = diggcount
        article_item["totalview"] = totalview
        article_item["commentcount"] = commentcount

        article_item["url_object_id"] = common.get_md5(article_item["url"])
        """

        item_loader.add_value("diggcount", j_data["DiggCount"])
        item_loader.add_value("totalview", j_data["TotalView"])
        item_loader.add_value("commentcount", j_data["CommentCount"])
        item_loader.add_value("url_object_id", get_md5(response.meta.get("url", "")))

        # 最后要记得加上，因为不再一开始调用，而是延迟调用了
        article_item = item_loader.load_item()

        yield article_item



