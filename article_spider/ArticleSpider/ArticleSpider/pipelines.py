# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import  JsonItemExporter
import MySQLdb
from twisted.enterprise import adbapi


class ArticlespiderPipeline:
    def process_item(self, item, spider):
        return item

class ArticleImagePipeline(ImagesPipeline):
    # 实际上可以理解为图片下载过程中的拦截，拦截图片的信息
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            image_file_path = ""
            # for循环results里面的：下载是否正确，值是什么，然后从value里面取image_file_path
            for ok, value in results:
                image_file_path = value['path']
            item["front_image_path"] = image_file_path

        return item

class JsonWithEncodingPipeline(object):
    # 自定义Jason文件的导出, step1:打开文件，
    def __init__(self):
        # 文件名称为article.json，w= write, a = append
        self.file = codecs.open("article.json", "a", encoding="utf-8")

    def process_item(self, item, spider):
        # 将json转换为字符串，将item强制转换成一个dict, "\n": 每个数据之间就会有一个回车换行
        lines = json.dumps(dict(item),ensure_ascii= False) + "\n"
        self.file.write(lines)
        return item

    # 文件的打开一定会对应一个文件的关闭,名称不要随便写
    def spider_closed(self,spider):
        self.file.close()

class JsonExporterPipleline(object):
    #调用scrapy提供的json export导出json文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

class MysqlPipeline(object):
    #采用同步的机制写入mysql
    def __init__(self):
        # 参数：url，用户名，密码，数据库名称
        self.conn = MySQLdb.connect('127.0.0.1', 'root', 'secure1234', 'article_spider', charset="utf8", use_unicode=True)
        # 规定需要一个cursor
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into cnblogs_article(title, url, url_object_id, front_image_url, front_image_path,
            diggcount, totalview, commentcount, tags, content, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE diggcount = VALUES(diggcount),
        """
        params = list()
        params.append(item.get("title",""))
        params.append(item.get("url",""))
        params.append(item.get("url_object_id",""))
        front_image = ",".join(item.get("front_image_url",[]))
        params.append(front_image)
        params.append(item.get("front_image_path",""))
        params.append(item.get("diggcount",0))
        params.append(item.get("totalview",0))
        params.append(item.get("commentcount",0))
        params.append(item.get("tags",""))
        params.append(item.get("content",""))
        params.append(item.get("created_date","1970-07-01"))
        self.cursor.execute(insert_sql,tuple(params))
        self.conn.commit()
        return item

class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        # 数据直接从setting里面读进去，所以需要在setting里面配置好
        from MySQLdb.cursors import DictCursor
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
           #  cursorclass=MySQLdb.cursors.DictCursor,
            cursorclass= DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常

    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
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
        params.append(item.get("title", ""))
        params.append(item.get("url", ""))
        params.append(item.get("url_object_id", ""))
        front_image = ",".join(item.get("front_image_url", []))
        params.append(front_image)
        params.append(item.get("front_image_path", ""))
        params.append(item.get("diggcount", 0))
        params.append(item.get("totalview", 0))
        params.append(item.get("commentcount", 0))
        params.append(item.get("tags", ""))
        params.append(item.get("content", ""))
        params.append(item.get("created_date", "0000-00-00"))

        cursor.execute(insert_sql, tuple(params))
        self.conn.commit()

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print (failure)




