import json


class Tasker:
    """data = {
        "name": "",
        "group": "",
        "url": "",
        "headers": {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML,'
                          ' like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        },
        "data": {},
        "method": "get",
        # "times": 1
    }"""
    def __init__(self):
        self.name = ""
        self.group = ""
        self.url = ""
        self.headers = {}
        self.data = {}
        self.method = ""
        self.times = None

    def __call__(self):
        return json.dumps(self.__dict__)

