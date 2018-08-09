# Dcrawl(这次不装逼，用中文)
一个分布式异步爬虫，采用生产Producer和消费Consumer模式

# Updates
    
    - 0.1.1
        - 修复aredsi造成的warnning
        - 修复consumer 处理请求次数的bug
    
    - 0.1
        - 添加producer_demo中循环添加data的提示
        - 修复consumer的get请求带有空data会出错的bug
        - 将consumer原本控制台输出放入log作为info
        - 将consumer的同步redis改为异步aredis，set_host 会报warnning，后期改进
        - 任务添加times字段，表示执行次数

# TODO List
    
    - 添加consumer result里带有本次请求的name，用于分类
    - websocket的支持（待定）
    - pypi修复

# pip

    # todo pypi配置问题，暂时无法使用，后面修复
    # pip install chuwt-Dcrawl

# producer_demo

    from producer import Producer
    p = Producer()
    // 留意for循环插入时data不要放到for外面，造成data引用问题
    data = {
            "name":        'baidu',                     
            "url":         "https://baidu.com",     
            "headers":     {"Content-Type": "application/json"},                         
            "data":        {},
            "method":      "get"                       
    }
    p.add_task(data)
    p.run()

# consumer_demo

    from consumer import Consumer
    cons = Consumer()
    
    # 数据处理方法 todo 可以根据不同的name写不同的handle
    @Consumer.handle
    def result(resp):
        print('test')
        print(resp)
        
    cons.loop_task()
