from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import os
import random
import cv2
import numpy as np
import undetected_chromedriver as uc
from ArticleSpider.settings import USER, PASSWORD


# 运用机器学习：EasyDL训练的模型的传入
class BaiDuLogin():
    def __init__(self, ak, sk):
        self.ak = ak
        self.sk = sk

    def get_access_token(self):
        # encoding:utf-8
        import requests

        # client_id 为官网获取的AK， client_secret 为官网获取的SK
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}'.format(
            self.ak, self.sk)
        response = requests.get(host)
        if response.status_code == 200:
            return response.json()["access_token"]
        return None

    def recongnize(self):
        """
        EasyDL 物体检测 调用模型公有云API Python3实现
        """

        import json
        import base64
        import requests
        """
        使用 requests 库发送请求
        使用 pip（或者 pip3）检查我的 python3 环境是否安装了该库，执行命令
          pip freeze | grep requests
        若返回值为空，则安装该库
          pip install requests
        """

        # 目标图片的 本地文件路径，支持jpg/png/bmp格式
        # IMAGE_FILEPATH = "【您的测试图片地址，例如：./example.jpg】"
        IMAGE_FILEPATH = "background"

        # 可选的请求参数
        # threshold: 默认值为建议阈值，请在 我的模型-模型效果-完整评估结果-详细评估 查看建议阈值
        PARAMS = {"threshold": 0.3}

        # 服务详情 中的 接口地址
        MODEL_API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/kechenzhihu"

        # 调用 API 需要 ACCESS_TOKEN。若已有 ACCESS_TOKEN 则于下方填入该字符串
        # 否则，留空 ACCESS_TOKEN，于下方填入 该模型部署的 API_KEY 以及 SECRET_KEY，会自动申请并显示新 ACCESS_TOKEN
        ACCESS_TOKEN = "24.d2c1da489f6196c650bacf4346789f1b.2592000.1678943525.282335-30415821"
        API_KEY = "eBjHV8poSp2oRIVGqvO3UMg2"
        SECRET_KEY = "8QKRwGaL0jdH5lPD0bxkgqwz6S3iHWKq"

        # 读文件
        print("1. 读取目标图片 '{}'".format(IMAGE_FILEPATH))
        with open(IMAGE_FILEPATH, 'rb') as f:
            base64_data = base64.b64encode(f.read())
            base64_str = base64_data.decode('UTF8')
        print("将 BASE64 编码后图片的字符串填入 PARAMS 的 'image' 字段")
        PARAMS["image"] = base64_str

        if not ACCESS_TOKEN:
            print("2. ACCESS_TOKEN 为空，调用鉴权接口获取TOKEN")
            auth_url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials" \
                       "&client_id={}&client_secret={}".format(API_KEY, SECRET_KEY)
            auth_resp = requests.get(auth_url)
            auth_resp_json = auth_resp.json()
            ACCESS_TOKEN = auth_resp_json["access_token"]
            print("新 ACCESS_TOKEN: {}".format(ACCESS_TOKEN))
        else:
            print("2. 使用已有 ACCESS_TOKEN")

        print("3. 向模型接口 'MODEL_API_URL' 发送请求")
        request_url = "{}?access_token={}".format(MODEL_API_URL, ACCESS_TOKEN)
        response = requests.post(url=request_url, json=PARAMS)
        response_json = response.json()
        response_str = json.dumps(response_json, indent=4, ensure_ascii=False)
        # print("结果:\n{}".format(response_str))
        if "results" not in response_str:
            return None
        if len(response.json()["results"]) == 0:
            return None
        if "location" not in response.json()["results"][0]:
            return None
        return response.json()["results"][0]["location"]["left"]


class Login(object):
    def __init__(self, user, password, retry):
        self.browser = uc.Chrome()  # 这里有一个坑：chrome()实例化的时候会自动下载chromedriver--最新的版本
        self.wait = WebDriverWait(self.browser, 20)
        self.url = 'https://www.zhihu.com/signin'
        self.sli = Code()  # 上面有class Code，主要负责和滑动验证码相关的一些功能
        self.user = user
        self.password = password
        self.retry = retry  # 重试次数

    #openvc方式的登录
    def login(self):
        # 请求登录页面网址
        self.browser.get(self.url)
        login_element = self.browser.find_element(By.XPATH,
                                                  # '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[1]/div[2]'
                                                  '//*[@id="root"]/div/main/div/div/div/div/div[2]/div/div[1]/div/div[1]/form/div[1]/div[2]')
        # 本来是可以直接用self.browser.click()模拟点击，但是zhihu把他屏蔽了，所以execute一个script
        self.browser.execute_script("arguments[0].click();", login_element)
        # time.sleep(5)

        # 输入账号，用到selenium的一些方法
        # self.wait = WebDriverWait(self.browser, 20)
        # from selenium.webdriver.support import expected_conditions as Ec 期望什么条件
        username = self.wait.until(
            # 用一个CSS_SELECTOR取查询我们输入的用户名输入框
            # 等待到你可以点击，所以删除上面的time.sleep(5)也是没有问题的
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-account input'))
        )
        username.send_keys(self.user)
        # 输入密码
        password = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-password input'))
        )
        password.send_keys(self.password)

        # 点击登录框
        submit = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
        )
        submit.click()
        time.sleep(3)

        k = 1
        # while True: 使用一个暴力的方法，不停的取识别滑动验证码
        # 原理为： 把验证码滑块的图像交给opencv，让他在验证码背景图片中取识别，是否有哪个形状和验证码滑块的形状一样，找出他的位置在验证码背景图的哪里
        # opencv把验证码滑块的图片灰度化，
        while k < self.retry:
            # 获取滑动前页面的url网址
            # 1. 获取原图， 获取验证码背景图
            bg_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_bg-img'))
            )
            # 获取滑块链接，获取验证码滑块
            # front_img = self.wait.until(
            #     Ec.presence_of_element_located(
            #         (By.CSS_SELECTOR, "#cdn2")))
            front_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_jigsaw'))
            )

            # 获取验证码滑动距离
            # self.sli = Code()  +  def get_element_slide_distance
            distance = self.sli.get_element_slide_distance(front_img, bg_img)
            print('滑动距离是', distance)

            # 2. 乘缩放比例， -去  滑块前面的距离  下面给介绍
            distance = distance - 4
            print('实际滑动距离是', distance)

            # 滑块对象
            element = self.browser.find_element_by_css_selector(
                '.yidun_slider')
            # 滑动函数
            self.sli.slide_verification(self.browser, element, distance)

            # 滑动之后的url链接
            time.sleep(5)
            # 登录框
            try:
                submit = self.wait.until(
                    Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
                )
                submit.click()
                time.sleep(3)
            except:
                pass

            # 查看登录是否成功，判断当前的页面是否为zhihu的首页
            end_url = self.browser.current_url
            print(end_url)

            if end_url == "https://www.zhihu.com/":
                return self.get_cookies()
            else:
                # reload = self.browser.find_element_by_css_selector("#reload div")
                # self.browser.execute_script("arguments[0].click();", reload)
                time.sleep(3)

                k += 1

        return None

    # 机器学习训练模型的登录
    def login_baidu(self):
        # 请求登录页面网址
        self.browser.get(self.url)
        login_element = self.browser.find_element(By.XPATH,
                                                  # '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[1]/div[2]'
                                                  '//*[@id="root"]/div/main/div/div/div/div/div[2]/div/div[1]/div/div[1]/form/div[1]/div[2]')
        # 本来是可以直接用self.browser.click()模拟点击，但是zhihu把他屏蔽了，所以execute一个script
        self.browser.execute_script("arguments[0].click();", login_element)
        # time.sleep(5)

        # 输入账号，用到selenium的一些方法
        # self.wait = WebDriverWait(self.browser, 20)
        # from selenium.webdriver.support import expected_conditions as Ec 期望什么条件
        username = self.wait.until(
            # 用一个CSS_SELECTOR取查询我们输入的用户名输入框
            # 等待到你可以点击，所以删除上面的time.sleep(5)也是没有问题的
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-account input'))
        )
        username.send_keys(self.user)
        # 输入密码
        password = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-password input'))
        )
        password.send_keys(self.password)

        # 点击登录框
        submit = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
        )
        submit.click()
        time.sleep(3)

        k = 1
        # while True: 使用一个暴力的方法，不停的取识别滑动验证码
        # 原理为： 把验证码滑块的图像交给opencv，让他在验证码背景图片中取识别，是否有哪个形状和验证码滑块的形状一样，找出他的位置在验证码背景图的哪里
        # opencv把验证码滑块的图片灰度化，
        while k < self.retry:
            # 获取滑动前页面的url网址
            # 1. 获取原图， 获取验证码背景图
            bg_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_bg-img'))
            )

            # 背景图片下载
            # self.sli = Code()
            # def get_element_slide_distance 里面的 background_url = background_ele.get_attribute('src')
            background_url = bg_img.get_attribute('src')
            background = "background.jpg"
            self.sli.onload_save_img(background_url, background)

            """
                        # 获取滑块链接，获取验证码滑块
            # front_img = self.wait.until(
            #     Ec.presence_of_element_located(
            #         (By.CSS_SELECTOR, "#cdn2")))
            front_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_jigsaw'))
            )
            """

            # 获取验证码滑动距离
            baidu = BaiDuLogin("eBjHV8poSp2oRIVGqvO3UMg2", "8QKRwGaL0jdH5lPD0bxkgqwz6S3iHWKq")
            distance = baidu.recongnize()

            # distance = self.sli.get_element_slide_distance(front_img, bg_img)
            print('滑动距离是', distance)

            # 2. 乘缩放比例， -去  滑块前面的距离  下面给介绍
            distance = distance - 4
            print('实际滑动距离是', distance)

            # 滑块对象
            element = self.browser.find_element_by_css_selector(
                '.yidun_slider')
            # 滑动函数
            self.sli.slide_verification(self.browser, element, distance)

            # 滑动之后的url链接
            time.sleep(5)
            # 登录框
            try:
                submit = self.wait.until(
                    Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
                )
                submit.click()
                time.sleep(3)
            except:
                pass

            # 查看登录是否成功，判断当前的页面是否为zhihu的首页
            end_url = self.browser.current_url
            print(end_url)

            if end_url == "https://www.zhihu.com/":
                return self.get_cookies()
            else:
                # reload = self.browser.find_element_by_css_selector("#reload div")
                # self.browser.execute_script("arguments[0].click();", reload)
                time.sleep(3)

                k += 1

        return None

    def get_cookies(self):
        '''
        登录成功后 保存账号的cookies
        :return:
        '''
        cookies = self.browser.get_cookies()
        self.cookies = ''
        for cookie in cookies:
            self.cookies += '{}={};'.format(cookie.get('name'), cookie.get('value'))
        return cookies

    def __del__(self):
        self.browser.close()
        print('界面关闭')
        # self.display.stop()

class Code():
    '''
    滑动验证码破解
    '''

    def __init__(self, slider_ele=None, background_ele=None, count=1, save_image=False):
        '''

        :param slider_ele:
        :param background_ele:
        :param count:  验证重试次数
        :param save_image:  是否保存验证中产生的图片， 默认 不保存
        '''

        self.count = count
        self.save_images = save_image
        self.slider_ele = slider_ele
        self.background_ele = background_ele

    # 获取滑动验证码滑动的滑块的元素，去计算出滑动轨迹
    def get_slide_locus(self, distance):
        distance += 8
        v = 0
        m = 0.3
        # 保存0.3内的位移
        tracks = []
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            s = v0 * m + 0.5 * a * (m ** 2)
            current += s
            tracks.append(round(s))
            v = v0 + a * m
        # 由于计算机计算的误差，导致模拟人类行为时，会出现分布移动总和大于真实距离，这里就把这个差添加到tracks中，也就是最后进行一步左移。
        # tracks.append(-(sum(tracks) - distance * 0.5))
        # tracks.append(10)
        return tracks

    # 实现具体的滑动
    def slide_verification(self, driver, slide_element, distance):
        '''

        :param driver: driver对象
        :param slide_element: 滑块元祖
        :type   webelement
        :param distance: 滑动距离
        :type: int
        :return:
        '''
        # 获取滑动前页面的url网址
        start_url = driver.current_url
        print('滑动距离是: ', distance)
        # 根据滑动的距离生成滑动轨迹
        locus = self.get_slide_locus(distance)

        print('生成的滑动轨迹为:{},轨迹的距离之和为{}'.format(locus, distance))

        # 按下鼠标左键
        ActionChains(driver).click_and_hold(slide_element).perform()

        time.sleep(0.5)

        # 遍历轨迹进行滑动
        for loc in locus:
            time.sleep(0.01)
            # 此处记得修改scrapy的源码 selenium\webdriver\common\actions\pointer_input.py中将DEFAULT_MOVE_DURATION改为50，否则滑动很慢
            ActionChains(driver).move_by_offset(loc, random.randint(-5, 5)).perform()
            ActionChains(driver).context_click(slide_element)

        # 释放鼠标
        ActionChains(driver).release(on_element=slide_element).perform()

        # # 判断是否通过验证，未通过下重新验证
        # time.sleep(2)
        # # 滑动之后的yurl链接
        # end_url = driver.current_url

        # if start_url == end_url and self.count > 0:
        #     print('第{}次验证失败，开启重试'.format(6 - self.count))
        #     self.count -= 1
        #     self.slide_verification(driver, slide_element, distance)

    def onload_save_img(self, url, filename="image.png"):
        '''
        下载图片并保存
        :param url: 图片网址
        :param filename: 图片名称
        :return:
        '''
        try:
            response = requests.get(url)
        except Exception as e:
            print('图片下载失败')
            raise e
        else:
            with open(filename, 'wb') as f:
                f.write(response.content)

    def get_element_slide_distance(self, slider_ele, background_ele, correct=0):
        '''
        根据传入滑块， 和背景的节点， 计算滑块的距离
        :param slider_ele: 滑块节点参数
        :param background_ele:  背景图的节点
        :param correct:
        :return:
        '''
        # 获取验证码的图片
        slider_url = slider_ele.get_attribute('src')
        background_url = background_ele.get_attribute('src')

        # 下载验证码链接
        slider = 'slider.jpg'
        background = 'background.jpg'

        self.onload_save_img(slider_url, slider)

        self.onload_save_img(background_url, background)

        # 进行图像灰度操作, 转化为numpy 中的数组类型数据
        slider_pic = cv2.imread(slider, 0)
        background_pic = cv2.imread(background, 0)

        # 获取缺口数组的形状
        width, height = slider_pic.shape[::-1]

        # 将处理之后的图片另存
        slider01 = 'slider01.jpg'
        slider02 = 'slider02.jpg'
        background01 = 'background01.jpg'

        cv2.imwrite(slider01, slider_pic)
        cv2.imwrite(background01, background_pic)

        # 读取另存的滑块
        slider_pic = cv2.imread(slider01)

        # 进行色彩转化
        slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)

        # 获取色差的绝对值
        slider_pic = abs(255 - slider_pic)
        # 保存图片
        cv2.imwrite(slider02, slider_pic)
        # 读取滑块
        slider_pic = cv2.imread(slider02)

        # 读取背景图
        background_pic = cv2.imread(background01)

        # 展示图片
        # cv2.imshow('gray1', slider_pic)  # gray1，gray2是窗口名称
        # cv2.imshow('gray2', background_pic)
        #
        # # 释放资源
        # cv2.waitKey(0)  # 按任意键退出图片展示
        # cv2.destroyAllWindows()
        time.sleep(3)

        # 必脚两张图的重叠部分
        result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)

        # 通过数组运算，获取图片缺口位置
        top, left = np.unravel_index(result.argmax(), result.shape)

        # 背景图缺口坐标
        print('当前滑块缺口位置', (left, top, left + width, top + height))

        # 判读是否需求保存识别过程中的截图文件
        if self.save_images:
            loc = [(left + correct, top + correct), (left + width - correct, top + height - correct)]
            self.image_crop(background, loc)

        else:
            # 删除临时文件
            os.remove(slider01)
            os.remove(slider02)
            os.remove(background01)
            os.remove(background)
            os.remove(slider)
            # print('删除')
            # os.remove(slider)
        # 返回需要移动的位置距离
        return left

    def image_crop(self, image, loc):
        cv2.rectangle(image, loc[0], loc[1], (7, 249, 151), 2)
        cv2.imshow('Show', image)
        # cv2.imshow('Show2', slider_pic)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # opencv识别滑动验证码可能失败，机器学习识别概率很高
    l = Login(USER, PASSWORD, 6)
    cookie_dict = l.login_baidu()


