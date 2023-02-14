import scrapy

from ArticleSpider.utils import zhihu_login_opencv
from ArticleSpider.settings import USER, PASSWORD

class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']
    custom_settings = {
        "COOKIES_ENABLED" : True
    }

    def start_requests(self):
        # 入口模拟登录拿到cookie,selenium可以取控制浏览器
        # 两种滑动验证码识别 Two kinds of sliding verification code recognition
        # 1. 使用opencv（图像处理库）识别 2. 使用机器学习方法识别

        # 1. 使用opencv, l为zhihu_login_opencv里最后得到的cookie
        l = Login(USER, PASSWORD, 6)
        cookie_dict = l.login()

        for url in self.start_urls:
            # 将cookie交给scrapy，那么后续的请求会沿用之前请求的cookie吗？ 不会，所以需要设置一下
            # 伪装成我的一个浏览器
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }
            yield scrapy.Request(url, cookies=cookie_dict, headers=headers, dont_filter=True)

    def parse(self, response, **kwargs):
        pass


