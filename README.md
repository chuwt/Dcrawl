# Dcrawl(这次不装逼，用中文)
一个分布式异步爬虫，采用生产Producer和消费Consumer模式

# Updates

    - v0.2
        - 重构consumer：
            1. 改变原有的初始化方式，将原来的redis异步读取，改为一次性读取到内存中
            2. 修改原来的worker方法，添加未完成队列和完成队列来进行任务跟踪，这样每个task都会被
                执行一遍，不存在一个task被执行多次，而另一个task（同一group中）被执行多次
            3. 添加了格式化log

    - v0.1.2
        - 添加请求时group参数，用于将task分组，同一组享有共同的timeout
        - 添加tasker模块，用于构造发送的请求
        - 添加conumser result的返回name
        - 修复aredis请求资源竞争问题
    
    - v0.1.1
        - 修复aredsi造成的warnning
        - 修复consumer 处理请求次数的bug
    
    - v0.1
        - 添加producer_demo中循环添加data的提示
        - 修复consumer的get请求带有空data会出错的bug
        - 将consumer原本控制台输出放入log作为info
        - 将consumer的同步redis改为异步aredis，set_host 会报warnning，后期改进
        - 任务添加times字段，表示执行次数

# bug list
    
    

# TODO List
    
    - 优化woker， 添加log输出
    - 添加websocket的支持（已完成初步）
    - 添加proxy支持
    - pypi修复

# pip

    # todo pypi配置问题，暂时无法使用，后面修复
    # pip install chuwt-Dcrawl

# producer_demo

    from producer import Producer
    from tasker import Tasker
    p = Producer()
    task = Tasker()
    task.name = 'baidu'
    task.url = 'https://baidu.com'
    task.headers = {"Content-Type": "application/json"}
    task.method = "get"
    p.add_task(task)
    p.run()

# consumer_demo

    from consumer import Consumer
    cons = Consumer()
    
    # 数据处理方法 todo 可以根据不同的name写不同的handle
    @Consumer.handle
    def result(resp, name):
        print('test')
        print(resp)
        
    cons.loop_task()
