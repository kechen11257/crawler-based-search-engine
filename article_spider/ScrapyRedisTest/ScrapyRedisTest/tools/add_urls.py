import redis
import json

rd = redis.Redis("127.0.0.1", decode_responses=True)
rd.lpush("cnblogs:news_urls", "http://news.cnblogs.com/")

urls = [("https://news.cnblogs.com/n/656059/", 3),
        ("https://news.cnblogs.com/n/656048/", 5),
        ("https://news.cnblogs.com/n/656023/", 8),
        ("https://news.cnblogs.com/n/656147/", 50),
        ]

for url in urls:
    rd.rpush("cnblogs:news_urls", json.dumps(url))
