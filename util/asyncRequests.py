import asyncio

from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup


class AsyncHttpHelper:
    @classmethod
    async def _get(cls, request):
        async with ClientSession(connector=TCPConnector(verify_ssl=False), headers=request.headers) as session:
            try:
                async with session.get(url=request.url) as response:
                    if response.status != 200:
                        print("Wrong response status: " + str(response.status))
                        return None

                    if request.raw:
                        return await response.read()
                    else:
                        return BeautifulSoup(await response.read(), 'html.parser')
            except Exception as e:
                print(e)
                return None

    @classmethod
    async def _post(cls, request):
        async with ClientSession(connector=TCPConnector(verify_ssl=False), headers=request.headers) as session:
            async with session.post(url=request.url, data=request.data) as response:
                return await response.read()

    @classmethod
    async def process(cls, request):
        response = await cls._get(request)

        if request.post_func:
            return request.post_func(request, response)
        else:
            return response

    @classmethod
    def get(cls, requests):
        # create object to loop event
        event_loop = asyncio.get_event_loop()

        # generate task with future
        tasks = map(lambda request: asyncio.ensure_future(cls.process(request)), requests)

        # start process and wait for result
        return event_loop.run_until_complete(asyncio.gather(*tasks))


class HttpReq:
    url = None
    headers = None
    data = None
    raw = False
    post_func = None
    extra_info = None

    def __init__(self, url, headers, data=None, raw=False, post_func=None, extra_info=None):
        self.url = url
        self.headers = headers
        self.data = data
        self.raw = raw
        self.post_func = post_func
        self.extra_info = extra_info


if __name__ == '__main__':
    urls = ["https://www.baidu.com/", "http://www.163.com", "http://weibo.com"]
    requests = list()
    DEFAULT_HEADER = {
        "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36"
    }


    def func(resp):
        print(resp)
        return resp


    requests.append(HttpReq("https://www.baidu.com/", DEFAULT_HEADER, raw=True, post_func=func))
    requests.append(HttpReq("http://www.163.com", DEFAULT_HEADER))
    requests.append(HttpReq("http://weibo.com", DEFAULT_HEADER))

    result = AsyncHttpHelper.get(requests)
    print("finish")
