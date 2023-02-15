# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
import scrapy
from scrapy.loader import ItemLoader
# from scrapy.loader.processors import MapCompose, TakeFirst, Identity, Join
from itemloaders.processors import TakeFirst, MapCompose, Join, Identity


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
