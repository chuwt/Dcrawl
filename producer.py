"""
1. 设置请求间隔
2. 生成消费队列
"""
import math
import redis
import json


def init_logo():
    print(
        """      %@@(                              @@ 
               &@@@#                          @@@@ 
           @@@(  /@@@%                      @@@@@@ 
            %@@@#   @@@@                  @@@@@@@* 
        @@@%  ,@@@( @@@@@@              #@@@@@@@&  
         (@@@%   @@@@@@@@@@@          &@@@@@@@@@   
           ,@@@%&@@@@@@@@@@@#       &@@@@@@@@@@    
              @@@@@@@@@@@@@@&     %@@@@@@@@@@@     
                @@@@@@@@@@@@    #@@@@@@@@@@@#      
                  @@@@@@@@@   (@@@@@@@@@@@@        
                            %@@@@@@@@@@@@&         
                          #@@@@@@@@@@@@@           
                        (@@@@@@*   @@@             
                      &@@@@@@@                     
                    &@@@@@@@     @@@@#@@%          
                  %@@@@@@@(        @@@@@@@%        
                %@@@@@@@&            @@@@@@@(      
               @@@@@@@@               %@@@@@@@&    
             @@@@@@@@                   @@@@@@@@&  
           %@@@@@@@&                      @@@@@@@@%
          @@@@@@@                         &@@@@@@@
        """)


init_logo()


class Producer:

    def __init__(self):
        self.CONFIG = self._get_config()
        self.cache = self._get_cache()
        self.MAX_HOST = self.CONFIG['consumer_amount']
        self.queue = list()
        self.time_delay = list()

    def add_task(self, task):
        self.queue.append(task)

    def add_task_delay(self, data):
        self.time_delay.append(data)

    def run(self):
        self.init_cache()
        self.set_task_delay()
        self.set_task_to_mq()

    def set_task_delay(self):
        print('init task time delay ...')
        """
        data = {
            "name": "xxx",
            "time": int(5)
        }
        """
        for data in self.time_delay:
            name = data['name']
            exp = math.ceil(int(data['time']) // self.MAX_HOST)
            self.cache.set(name, exp)
        print('task time delay done\n')

    def set_task_to_mq(self):
        """
        data 结构
            {
                "name":        "baidu",                     # 名称，区别同一ip
                "url":         "https://www.baidu.com",     # url
                "headers":     {},                          # 请求头
                "data":        {}                           # 请求体
                "status":      "pending"                    # 任务状态
                "method":      "get"                        # 方法
            }
        任务分配的key: "{hostname}.task"
        """
        print('init distribute task ...')
        hosts = self.cache.lrange('hosts', 0, 999)  # 获取所有consumer_hostname
        # todo 给每个host分配任务
        task_number = 0
        for task in self.queue:
            host_index = task_number % self.MAX_HOST
            task_name = "{}.task".format(hosts[host_index])
            if not task.group:
                task.group = task.name
            self.cache.lpush(task_name, task())
            task_number += 1
        print('task done')

    def init_cache(self):
        # 清空缓存
        for key in self.cache.keys('*.task'):
            self.cache.delete(key)

    def _get_config(self):
        with open('./config.json', 'r') as f:
            config = json.load(f)
            return config
            
    def _get_cache(self):
        pwd, host = self.CONFIG['broker_uri'].split('@')
        if pwd:
            cache_pool = redis.ConnectionPool(host=host, password=pwd, decode_responses=True)
        else:
            cache_pool = redis.ConnectionPool(host=host, decode_responses=True)
        cache = redis.Redis(connection_pool=cache_pool)
        return cache
