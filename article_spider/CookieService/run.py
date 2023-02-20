from server import CookieServer
from services.zhihu_login_sel import Login

import settings

srv = CookieServer(settings)

# 注册需要登录的服务,接口
srv.register(Login)

# 启动cookie服务
print("启动cookie池服务")
srv.start()
