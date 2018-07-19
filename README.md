# Dcrawal(这次不装逼，用中文)
一个分布式异步爬虫，采用生产Producer和消费Consumer模式

# producer_demo

    from producer import Producer
    p = Producer()
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

