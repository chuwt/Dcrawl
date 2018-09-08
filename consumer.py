# coding: utf-8
"""
Created by chuwt at 2018/9/7
"""
# os
import os
import time
import json
import logging
import socket
import signal
from collections import deque
from logging.handlers import TimedRotatingFileHandler
# third
import asyncio
import aiohttp
import redis
# self


def init_logo():
    print(
        """              %@@(                              @@ 
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


class Consumer:
    """
    初始化配置，缓存，log等
    """
    def __init__(self):
        self.CONFIG = self.init_config()
        self.cache = self.init_cache()
        self.HOSTNAME = self.init_hostname()
        self.init_log()
        self.init_signal()

        self.RUNNING_SIG = True
        # 未执行队列
        self.undo_tasks = deque()
        # 已执行队列
        self.done_tasks = list()
        # 任务等待时间
        self.delay_dict = dict()
        # 任务锁
        self.locker_dict = dict()   # {'task1': [], 'task2': []}
        self.init_task()

    def init_config(self):
        # todo 不存在时的判断
        with open('./config.json', 'r') as f:
            config = json.load(f)
            return config

    def init_cache(self):
        pwd, host = self.CONFIG['broker_uri'].split('@')
        if pwd:
            cache_pool = redis.ConnectionPool(host=host, password=pwd, decode_responses=True)
        else:
            cache_pool = redis.ConnectionPool(host=host, decode_responses=True)
        # cache = redis.StrictRedis(connection_pool=cache_pool)
        cache = redis.Redis(connection_pool=cache_pool)
        return cache

    def init_hostname(self):
        hostname = socket.gethostname()
        hosts = self.cache.lrange('hosts', 0, 100)
        print(hosts)
        if hostname not in hosts:
            self.cache.lpush('hosts', hostname)
        return hostname

    def init_log(self, log_level='INFO'):
        logging.basicConfig(
            level={
                "INFO": logging.INFO,
                "DEBUG": logging.DEBUG,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR}[log_level],
            format='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s]<%(thread)s>:%(message)s',
            datefmt='%Y%m%d %H:%M:%S',
            handlers=[
                TimedRotatingFileHandler(
                    filename=os.path.join(self.CONFIG['log_path']),
                    when='D',
                    encoding='utf-8')])

    def init_signal(self):
        # Ctrl-C
        signal.signal(signal.SIGINT, self._put_running_sig)
        # nohup
        signal.signal(signal.SIGHUP, self._put_running_sig)
        # kill
        signal.signal(signal.SIGTERM, self._put_running_sig)

    def init_task(self):
        tasks_key = "{}.task".format(self.HOSTNAME)
        # 获取tasks
        while True:
            tasks = self.cache.lrange(tasks_key, 0, 10000)
            logging.info('start loading tasks from redis')
            if tasks:
                for task in tasks:
                    task_data = json.loads(task)
                    group_name = task_data.get('group')
                    delay = self.cache.get(group_name) or 5
                    # set delay time
                    self.delay_dict[group_name] = delay
                    # push into undo task
                    self.undo_tasks.append(task_data)
                    # init locker
                    self.locker_dict[group_name] = [1]
                    logging.info("loading task %s success", task_data.get('name'))
                logging.info('loading tasks into memory success')
                return
            else:
                logging.info("no tasks in cache, retry 5s later")
                time.sleep(5)

    def _put_running_sig(self, sig, frame):
        self.RUNNING_SIG = False
        print('shutdowning ...')

    async def release_locker(self, group_name, sleep_time):
        import time
        await asyncio.sleep(int(sleep_time))
        self.locker_dict[group_name].append(1)

    async def worker(self):
        while self.RUNNING_SIG:
            if self.undo_tasks:
                task = self.undo_tasks.popleft()
            else:
                task = None
            if task:
                group_name = task['group']
                if self.locker_dict.get(group_name, None):
                    self.locker_dict.get(group_name).pop()
                    url = task['url']
                    name = task['name']
                    headers = task['headers']
                    body_data = task['data']
                    method = task['method'].upper()
                    # request
                    await self.request_task(url, method, headers, body_data, name)
                    self.done_tasks.append(task)
                    # release locker
                    await self.release_locker(group_name, self.delay_dict.get(group_name, 5))
                else:
                    self.undo_tasks.append(task)
                    await asyncio.sleep(1)
            else:
                self.undo_tasks += self.done_tasks
                self.done_tasks = list()
                await asyncio.sleep(1)

    async def request_task(self, url, method, headers, data, name):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            if method == 'GET':
                async with session.get(url, headers=headers, timeout=5000) as resp:
                    t = await resp.text()
                    await Consumer.result(t, name)
                    # print(t)
            elif method == 'POST':
                async with session.post(url, data=json.dumps(data), headers=headers, timeout=5000) as resp:
                    t = await resp.text()
                    await Consumer.result(t, name)
                    # print(t)

    @staticmethod
    def handle(func):
        Consumer.result = func
        return

    @staticmethod
    async def result(resp, name=None):
        # await asyncio.sleep(0.1)
        print(resp)

    async def run(self):
        task = [asyncio.ensure_future(self.worker()) for _ in range(3)]
        await asyncio.wait(task)

    def loop_task(self):
        while self.RUNNING_SIG:
            print("running ...")
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(asyncio.ensure_future(self.run()))
            except Exception as e:
                logging.error(e)
                self.RUNNING_SIG = False

    def loop_stop(self):
        self.RUNNING_SIG = False
