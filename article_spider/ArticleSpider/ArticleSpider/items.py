# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
from datetime import datetime

import scrapy
from scrapy.loader import ItemLoader
# from scrapy.loader.processors import MapCompose, TakeFirst, Identity, Join
from itemloaders.processors import TakeFirst, MapCompose, Join, Identity

from ArticleSpider.settings import SQL_DATETIME_FORMAT
from ArticleSpider.utils.common import extract_num


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


""" 测试下面的items
def add_kechen(value):
    return value + "-kechen"
def add_test(value):
    return value + "-test"
"""


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


def date_convert(value):
    match_re = re.match(".*?(\d+.*)", value)
    if match_re:
        return match_re.group(1)
    else:
        return "0000-00-00"


def remove_comment_tags(value):
    # 去掉tag中提取的评论
    if value == "linux":  # linux只是一个举例
        return ""
    else:
        return value


class CnblogsArticleItem(scrapy.Item):
    """
    # 定义好需要解析的字段
    title = scrapy.Field()
    created_date = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field()
    front_image_path = scrapy.Field()

    content = scrapy.Field()
    tags = scrapy.Field()

    diggcount = scrapy.Field()
    totalview = scrapy.Field()
    commentcount = scrapy.Field()
    """

    title = scrapy.Field()
    """
    title = scrapy.Field()(
        input_processor = MapCompose(add_author, add_test), # 测试用，MapCompose可以对括号里面的方法进行逐一的调用
        output_processor=TakeFirst() # 测试用,只获得第一个值
    )
    """
    created_date = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )

    url = scrapy.Field()
    url_object_id = scrapy.Field()

    front_image_url = scrapy.Field(
        output_processor=Identity()
    )
    front_image_path = scrapy.Field()

    content = scrapy.Field()
    tags = scrapy.Field(
        output_processor=Join(separator=",")
    )

    diggcount = scrapy.Field()
    commentcount = scrapy.Field()
    totalview = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                                insert into cnblogs_article(title, url, url_object_id, front_image_url, front_image_path,
                                diggcount, totalview, commentcount, tags, content, created_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                title = VALUES(title), url = VALUES(url), url_object_id = VALUES(url_object_id),
                                front_image_url = VALUES(front_image_url), front_image_path = VALUES(front_image_path),
                                diggcount = VALUES(diggcount), totalview = VALUES(totalview), commentcount = VALUES(commentcount),
                                tags = VALUES(tags), content = VALUES(content), created_date = VALUES(created_date),
                            """
        params = list()
        params.append(self.get("title", ""))
        params.append(self.get("url", ""))
        params.append(self.get("url_object_id", ""))
        front_image = ",".join(self.get("front_image_url", []))
        params.append(front_image)
        params.append(self.get("front_image_path", ""))
        params.append(self.get("diggcount", 0))
        params.append(self.get("totalview", 0))
        params.append(self.get("commentcount", 0))
        params.append(self.get("tags", ""))
        params.append(self.get("content", ""))
        params.append(self.get("created_date", "0000-00-00"))

        return insert_sql, params

class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num,
              watch_user_num, click_num, crawl_time
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
        """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))

        if len(self["watch_user_num"]) == 2:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = int(self["watch_user_num"][1])
        else:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = 0

        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num,
                  watch_user_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    #知乎的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, parise_num, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), parise_num=VALUES(parise_num),
              update_time=VALUES(update_time)
        """

        # 从json传过来的时候是int类型，需要做单独的处理
        # datetime.datetime.fromtimestamp() 将int转换成datatime类型
        # 将datatime类型装换成字符串
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["parise_num"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params
