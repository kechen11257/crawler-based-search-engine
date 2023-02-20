# 1. cookie保存在redis中应该使用什么数据结构
# 2. 数据结构应该满足： 1. 可以随机获取 2. 可以防止重复 - set
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

import redis


# 1. 如何确保每一个网站都会被单独的运行
class CookieServer():
    # 主要管理login和check_cookies
    # 首先会启动需要登录的网站

    # redis的启动
    def __init__(self, settings):
        # initializes a Redis client
        # sets an empty list for service_list
        # saves the settings argument as an instance variable.
        self.redis_cli = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        self.service_list = []
        self.settings = settings

    # 提供一个接口：哪个网站需要做
    # This is a way for the class to keep track of which services it needs to manage.
    # This method takes a class(cls) as an argument and appends it to the service_list instance variable.
    def register(self, cls):
        self.service_list.append(cls)

    # This method takes a service class (srv) as an argument
    # and continuously attempts to log in to the service using the login method of the srv object.
    def login_service(self, srv):
        # If the number of cookies stored in Redis for the service is less than the maximum allowed,
        # it saves the cookie using Redis.
        while 1:
            srv_cli = srv(self.settings)
            srv_name = srv_cli.name
            cookie_nums = self.redis_cli.scard(self.settings.Accounts[srv_name]["cookie_key"])
            if cookie_nums < self.settings.Accounts[srv_name]["max_cookie_nums"]:
                # the method calls the login method of the srv object to get a new cookie, adds the cookie to Redis, and repeats the loop
                cookie_dict = srv_cli.login()
                self.redis_cli.sadd(self.settings.Accounts[srv_name]["cookie_key"], json.dumps(cookie_dict))
            # If the cookie pool is full, it waits for 10 seconds and tries again.
            else:
                print("{srv_name} 的cookie池已满，等待10s".format(srv_name=srv_name))
                time.sleep(10)

    # celery
    # This method takes a service class (srv) as an argument
    # and continuously checks if the cookies stored in Redis for the service are valid using the check_cookie method of the srv object.
    def check_cookie_service(self, srv):
        while 1:
            print("开始检测cookie是否可用")
            srv_cli = srv(self.settings)
            srv_name = srv_cli.name
            all_cookies = self.redis_cli.smembers(self.settings.Accounts[srv_name]["cookie_key"])
            print("目前可用cookie数量: {}".format(len(all_cookies)))
            # If a cookie is valid, it prints "cookie 有效".
            # If a cookie is invalid, it removes the cookie from Redis and prints "cookie已经失效， 删除cookie".
            for cookie_str in all_cookies:
                print("获取到cookie: {}".format(cookie_str))
                cookie_dict = json.loads(cookie_str)
                valid = srv_cli.check_cookie(cookie_dict)
                if valid:
                    print("cookie 有效")
                else:
                    print("cookie已经失效， 删除cookie")
                    self.redis_cli.srem(self.settings.Accounts[srv_name]["cookie_key"], cookie_str)
            # 设置间隔，防止出现请求过于频繁，导致本来没失效的cookie失效了
            # The method waits for a specified interval before starting the process again.
            interval = self.settings.Accounts[srv_name]["check_interval"]
            print("{}s 后重新开始检测cookie".format(interval))
            time.sleep(interval)

    # The start method initializes two thread pools using ThreadPoolExecutor
    # and creates two tasks for each service: one to run the login_service method
    # and one to run the check_cookie_service method.
    # 要想要实现多个网站同时模拟登录，一定会使用到多线程
    # 通过多线程来完成上面主要函数的调度
    # 当线程过多的时候，我们可以用线程池来进行管理
    def start(self):
        task_list = []
        print("启动登录服务")
        login_executor = ThreadPoolExecutor(max_workers=5)
        for srv in self.service_list:
            task = login_executor.submit(partial(self.login_service, srv))
            task_list.append(task)

        print("启动cookie检测服务")
        check_executor = ThreadPoolExecutor(max_workers=5)
        #  def register(self, cls): self.service_list.append(cls)
        for srv in self.service_list:
            task = check_executor.submit(partial(self.check_cookie_service, srv))
            task_list.append(task)

        # The method then waits for all tasks to complete and prints the result of each task.
        for future in as_completed(task_list):
            data = future.result()
            print(data)
