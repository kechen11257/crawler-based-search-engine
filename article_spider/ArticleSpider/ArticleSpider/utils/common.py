import hashlib

def get_md5(url):
    # 判断url是否是一个string类型
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)

    return m.hexdigest()

