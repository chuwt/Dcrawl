"""
1. 各个consumer注册自己的host
2. 等待任务到达
"""
import json
import logging
import redis
import socket
import asyncio
import aiohttp
import signal
import aredis


class Consumer:
    def __init__(self):
        self.CONFIG = self._get_config()
        self.cache = self._get_cache()
        self.HOSTNAME = self._get_hostname()
        self.init()
        self.RUNNING_SIG = True
        self.log_cache = ''

    def init(self):
        # self._set_host()
        self._set_log()
        self._set_signal()

    def _set_log(self):
        logging.basicConfig(filename=self.CONFIG['log_path'], level=logging.INFO)

    def _get_config(self):
        with open('./config.json', 'r') as f:
            config = json.load(f)
            return config

    def _get_cache(self):
        pwd, host = self.CONFIG['broker_uri'].split('@')
        if pwd:
            cache_pool = aredis.ConnectionPool(host=host, password=pwd, decode_responses=True)
        else:
            cache_pool = aredis.ConnectionPool(host=host, decode_responses=True)
        cache = aredis.StrictRedis(connection_pool=cache_pool)
        # cache = redis.Redis(connection_pool=cache_pool)
        return cache

    def _get_hostname(self):
        hostname = socket.gethostname()
        return hostname

    async def _set_host(self):
        hosts = await self.cache.lrange('hosts', 0, 100)
        print(hosts)
        if self.HOSTNAME not in hosts:
            await self.cache.lpush('hosts', self.HOSTNAME)

    def _put_running_sig(self, sig, frame):
        self.RUNNING_SIG = False
        print('shutdowning ...')

    def _set_signal(self):
        # Ctrl-C
        signal.signal(signal.SIGINT, self._put_running_sig)
        # nohup
        signal.signal(signal.SIGHUP, self._put_running_sig)
        # kill
        signal.signal(signal.SIGTERM, self._put_running_sig)

    async def worker(self):
        """
        1. 检查Running_sig
            1.1 获取顶部信息，如果获取不到则阻塞
                1.1.1 检查锁的状态，可用则继续
        :return:
        """
        tasks_key = "{}.task".format(self.HOSTNAME)
        while self.RUNNING_SIG:
            cache_data = await self.cache.blpop(tasks_key, 5)
            if cache_data:
                cache_data = cache_data[1]  # 获取顶部纪录
                data = json.loads(cache_data)
                name = data.get('name', '')
                # times = int(data.get('times', 1)) - 1
                times = data.get('times', None)
                # 如果设置了次数
                if times:
                    data['times'] = int(times) - 1
                    if data['times'] < 0:
                        continue
                lock_key = "{}.{}.lock".format(self.HOSTNAME, name)
                await self.cache.rpush(tasks_key, json.dumps(data))    # 将纪录插回底部
                # 检查时间锁的状态
                if not await self.cache.get(lock_key):
                    url = data['url']
                    headers = data['headers']
                    body_data = data['data']
                    method = data['method'].upper()
                    # 重新设置时间锁的状态
                    await self.cache.set(lock_key, 1, int(await self.cache.get(name) or 1))
                    logging.info(f"{url} done")
                    await self.request_task(url, method, headers, body_data)

    async def request_task(self, url, method, headers, data):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            if method == 'GET':
                async with session.get(url, headers=headers, timeout=5000) as resp:
                    t = await resp.text()
                    await Consumer.result(t)
                    # print(t)
            elif method == 'POST':
                async with session.post(url, data=json.dumps(data), headers=headers, timeout=5000) as resp:
                    t = await resp.text()
                    await Consumer.result(t)
                    # print(t)

    @staticmethod
    def handle(func):
        Consumer.result = func
        return

    @staticmethod
    async def result(resp):
        # await asyncio.sleep(0.1)
        print(resp)

    async def run(self):
        await self._set_host()
        task = [asyncio.ensure_future(self.worker()) for _ in range(10)]
        await asyncio.wait(task)

    def loop_task(self):
        while self.RUNNING_SIG:
            print("running ...")
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(asyncio.ensure_future(self.run()))
            except Exception as e:
                if self.log_cache != e:
                    logging.error(e)
                self.log_cache = e
                self.RUNNING_SIG = False

    def loop_stop(self):
        self.RUNNING_SIG = False
