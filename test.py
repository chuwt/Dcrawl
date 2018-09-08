import asyncio
import aiohttp

url = 'wss://live.trading212.com/streaming/events/?app=WC4&appVersion=5.38.6&EIO=3&transport=websocket'

headers = {
'Cookie': 'PLATFORM_LOADED_212=eyJ3ZWl0YW9jaHVAZ21haWwuY29tIjoiUkVBTCJ9; _ga=GA1.2.1458621006.1534352634; _gid=GA1.2.478560197.1534352634; TRADING_LANG=ZH; __zlcmid=nuhZJe7KrcBxHB; _gat_UA-101403076-1=1; JSESSIONID=55313E70F736387C434F9B59DB126946; CUSTOMER_SESSION=6f2a5118-d8a3-4d60-93c6-092919f2ff94; TRADING212_SESSION_LIVE=2_-1o8kekj3cbgmdmbw2506chsgb-10b4e7d4hbfab194g33u35j23m; 6e51e0a33e755f844c1cddd1bc6690eecd7880d9=eyJ1c2VybmFtZSI6IndlaXRhb2NodUBnbWFpbC5jb20iLCJ0b2tlbiI6IjgxOWIxYWJlLWQyYzQtNDgyNi04YjExLTAxNTdiYzExNzg4MSJ9; user_device=%7B%22location%22%3A%22unknown%22%2C%22language%22%3A%22en%22%2C%22country%22%3A%22%22%2C%22tablet%22%3Afalse%2C%22phone%22%3Afalse%2C%22mobile%22%3Afalse%7D; user_locale=%7B%22locale%22%3A%22en%22%7D; 5d60904a5b52802c63d8b5b97bf8a1ea=%225b745cf6299ad%22',
}


async def websocket_link():
    async with aiohttp.ClientSession().ws_connect(url, ssl=False, headers=headers) as ws:
        await ws.send_str('42["subscribe","/QUOTES",["BTCUSD","REAL"]]')
        async for msg in ws:
            print(msg.data)
            if msg.data == '2':
                await ws.send_str('2')


loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.ensure_future(websocket_link()))