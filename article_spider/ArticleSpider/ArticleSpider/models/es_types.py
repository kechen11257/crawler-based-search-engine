from datetime import datetime
from elasticsearch_dsl import Document, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class ArticleType(Document):
    #伯乐在线文章类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    # 定义放到哪一个index和type之下
    class Meta:
        index = "jobbole"
        doc_type = "article"


class LagouJobType(Document):
    #拉勾网的职位
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    salary = Keyword()
    job_city = Keyword()
    work_years = Keyword()
    degree_need = Keyword()
    job_type = Keyword()
    publish_time = Keyword()
    job_advantage = Keyword()
    job_desc = Keyword()
    job_addr = Keyword()
    company_name = Keyword()
    company_url = Keyword()
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "lagou"
        doc_type = "lagou"

# 通过定义的类型（通过定义的类）直接生成mapping
if __name__ == "__main__":
    ArticleType.init()
    LagouJobType.init()