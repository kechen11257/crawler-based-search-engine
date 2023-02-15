from urllib import parse
import re
import json
import scrapy
import datetime

from scrapy.loader import ItemLoader

from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem

try:
    import urlparse as parse
except:
    # python2中的写法
    from urllib import parse

from ArticleSpider.settings import USER, PASSWORD
from ArticleSpider.utils.zhihu_login_sel import Login

class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Cis_labeled%2Cpaid_info%2Cpaid_info_content%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_recognized%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics%3Bdata%5B%2A%5D.settings.table_of_content.enabled&limit={1}&offset={2}&platform=desktop&sort_by=default"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhizhu.com",
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    def start_requests(self):
        # 入口模拟登录拿到cookie,selenium可以取控制浏览器
        # 两种滑动验证码识别 Two kinds of sliding verification code recognition
        # 1. 使用opencv（图像处理库）识别 2. 使用机器学习方法识别

        # 1. 使用opencv, l为zhihu_login_sel里最后得到的cookie 2.机器学习：login_baidu()
        l = Login(USER, PASSWORD, 6)
        cookie_dict = l.login_baidu()

        for url in self.start_urls:
            # 将cookie交给scrapy，那么后续的请求会沿用之前请求的cookie吗？ 不会，所以需要设置一下
            # 伪装成我的一个浏览器
            headers = {
                "HOST": "www.zhihu.com",
                "Referer": "https://www.zhizhu.com",
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }
            yield scrapy.Request(url, cookies=cookie_dict, headers=headers, dont_filter=True)


    def parse(self, response, **kwargs):
        """
        提取出html页面中的所有url 并跟踪这些url进行一步爬取
        如果提取的url中格式为 /question/xxx 就下载之后直接进入解析函数
        """
        # 提取出html页面中所有的yrl，url全部都保存在a标签里面，然后用attr这个属性提取出href
        all_urls = response.css("a::attr(href)").extract()
        # 因为F12出来的url，前面没有域名,例如：/question/56320032/answer/149037527
        # 是一个list，从response里面的url提取出主域名， 和现在取到的url进行一个urljoin
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # x为all_urls当中的每一个值。对all_urls中的每一个元素做lambda函数，如果条件为true，就把加到all_urls这个列表里面，反之，过滤掉
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            # debug: print(url)
            if match_obj:
                request_url = match_obj.group(1)
                # question_id = match_obj.group(2)
                # debug: print(request_url, question_id)
                # 一定要传递scrapy.Request对象，才能够被下载执行， headers不加的话会返回500，
                # 不再是parse_detail了，而是parse_question，处理question页面
                # callback=self.parse_question 一定不能够携程 callback=self.parse_question()callback, 一定不能调用，只能够传函数名称
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
            else:
                # 如果不是question页面则直接进一步跟踪,继续请求这个页面
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        # 处理question页面， 从页面中提取出具体的question item
        question_id = ""
        # 因为新版本F12之后的title有QuestionHeader-title的字段的话，就证明是新的版本（url里之有question）
        # if QuestionHeader-title的字段在返回的字段中的话，就是一个新版本
        if "QuestionHeader-title" in response.text:
            # 处理新版本(url里之有)
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)

            if match_obj:
                question_id = int(match_obj.group(2))

            # 用itemloader处理items，首先创建实例，把item和response传递进去
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-actions button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            # item_loader.add_css("topics", ".QuestionHeader-topics .Popover::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

            question_item = item_loader.load_item()
        else:
            # 处理老版本页面的item提取
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            # item_loader.add_css("title", ".zh-question-title h2 a::text")
            # span标签或者a标签（|）
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            # item_loader.add_css("watch_user_num", "#zh-question-side-header-wrap::text")
            item_loader.add_xpath("watch_user_num",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, reponse):
        # 处理question的answer(paging字段)
        ans_json = json.loads(reponse.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)
