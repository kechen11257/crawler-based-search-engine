import abc


# metaclass=abc.ABCMeta ： 元类编程
class BaseService(metaclass=abc.ABCMeta):
    # 如果lagou没有实现自己class里面的login方法
    # 1. 第一种解决方案： 在父类的方法中抛出异常：如果lagou没有实现自己class里面的login方法，就会实现父类的login方法
    # 父类的login不实现任何东西
    # 2. 第二种解决方案： 使用抽象基类，在实例化的时候就会报错（l = Lagou()）
    @abc.abstractmethod
    def login(self):
        # raise NotImplementedError
        pass

    @abc.abstractmethod
    def check_cookie(self, cookie_dict):
        pass


# 假设
class Lagou(BaseService):
    name = "lagou"

    # 强制性的效果
    # def login(self):
    #    print("login in {}".format(self.name))


if __name__ == "__main__":
    l = Lagou()
    l.login()
