import requests
from scrapy import Selector
import MySQLdb

# mysql的连接
conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="root", db="article_spider", charset="utf8")
# Once the connection is established, a cursor object is created using conn.cursor().
# The cursor object allows the program to execute queries on the database using its execute() method
cursor = conn.cursor()

def crawl_ips():
    #爬取西刺的免费ip代理
    # The function first sets a user agent header to imitate a browser,
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0"}
    # and then iterates over a range of page numbers (from 0 to 1567) in order to access each page of proxy IPs.
    for i in range(1568):
        # For each page, the function sends a GET request to the website and receives a response
        re = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)

        # 前面的spider都是利用xpath，css来进行的解析
        # to parse the HTML text of the response into a Selector object
        # This object is used to extract specific HTML elements from the page using CSS selectors
        selector = Selector(text=re.text)
        # the CSS selector #ip_list tr is used to select all the tr tags in the ip_list element.
        all_trs = selector.css("#ip_list tr")


        ip_list = []
        # starting from the second element (i.e. skipping the header row).
        for tr in all_trs[1:]:
            # the title attribute of the <div> element with class bar
            speed_str = tr.css(".bar::attr(title)").extract()[0]
            if speed_str:
                # It converts the speed string to a float
                speed = float(speed_str.split("秒")[0])

            all_texts = tr.css("td::text").extract()
            ip = all_texts[0]
            port = all_texts[1]
            proxy_type = all_texts[5]

            ip_list.append((ip, port, proxy_type, speed))

        # insert into mysql
        for ip_info in ip_list:
            cursor.execute(
                "insert proxy_ip(ip, port, speed, proxy_type) VALUES('{0}', '{1}', {2}, 'HTTP')".format(
                    ip_info[0], ip_info[1], ip_info[3]
                )
            )
            # is called on the connection object to commit the changes to the database
            conn.commit()

class GetIP(object):
    def get_random_ip(self):
        #从数据库中随机获取一个可用的ip
        random_sql = """
              SELECT ip, port FROM proxy_ip
            ORDER BY RAND()
            LIMIT 1
            """
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            # 判断ip是否合法
            judge_re = self.judge_ip(ip, port)
            if judge_re:
                return "http://{0}:{1}".format(ip, port)
            else:
                return self.get_random_ip()

    # to check if a given IP proxy is valid and can be used to access a website.
    def judge_ip(self, ip, port):
        #判断ip是否可用
        # 用request，发一个request到http_url中判断是否可用
        # http_url, which is set to the URL of the website to be used for testing the proxy
        http_url = "http://www.baidu.com"
        # proxy_url, which is set to the URL of the proxy server using the ip and port arguments.
        proxy_url = "http://{0}:{1}".format(ip, port)
        try:
            # contains the http key with the proxy_url value
            proxy_dict = {
                "http":proxy_url,
            }
            # proxy_dict is then passed as the proxies argument to the requests.get() function,
            # which sends a GET request to the http_url using the specified proxy.
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print ("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print ("effective ip")
                return True
            else:
                print  ("invalid ip and port")
                self.delete_ip(ip)
                return False

    def delete_ip(self, ip):
        #从数据库中删除无效的ip
        delete_sql = """
            delete from proxy_ip where ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True




