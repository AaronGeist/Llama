import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from core.login import Login
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    process_thread = None
    book_id = 0
    comic_id = "0"
    comic_name = ""

    root_url = "http://www.mangabz.com"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "www.mangabz.com",
        "If-Modified-Since": "Sun, 30 Aug 2020 07:32:53 GMT",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
    }

    @classmethod
    def start(cls, book_id):
        cls.book_id = book_id
        cls.comic_id = re.match("(\d+)", book_id).group(1)
        cls.parse_lvl_one()

    @classmethod
    def init_thread(cls):
        if cls.process_thread is None:
            cls.process_thread = threading.Thread(target=cls.process)
            cls.process_thread.start()

    @classmethod
    def parse_lvl_one(cls):
        if cls.book_id is None:
            return

        url = "http://comic.dragonballcn.com/list/gain_1.php?did=0-6-"

        cls.init_thread()

        for index in range(0, 34):
            print(url + str(index))
            cls.parse_lvl_two((url + str(index), index))
        cls.process_thread.join()

        # code below should be useless if everything goes well
        while not cls.task_pool.empty():
            print("pool size = " + str(cls.task_pool.qsize()))
            cls.init_thread()
            cls.process_thread.join()

    @classmethod
    def parse_lvl_two(cls, info):
        url = info[0]
        index = info[1]

        # create folder once
        folder_name = "output/龙珠/" + str(index)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name, exist_ok=True)

        retry = 0
        while True:
            resp = HttpUtils.get(url)
            if resp is not None:
                break
            else:
                retry += 1

            assert retry < 5, "fail to query %s" % url

        links = HttpUtils.get_attrs(resp, ".ListContainer .ItemThumb a", "style")

        assert links is not None

        for link in links:
            url = re.search("background:url\(.*'(.*)'", link).group(1).replace("_thumb.", "")
            file_name = url.split("/")[-1]
            cls.task_pool.put([folder_name + "/" + file_name, url, 0])

    @classmethod
    def process(cls):
        print("#### process thread started")
        with ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                try:
                    # queue timeout should be greater than the download timeout
                    item = cls.task_pool.get(timeout=60)
                    executor.submit(cls.do_process, item)
                except Empty as e:
                    print("#### queue timeout")
                    break
        cls.process_thread = None
        print("#### process thread stopped")

    @classmethod
    def do_process(cls, item):
        path = item[0]
        url = item[1]
        retry = item[2]
        if retry <= 5:
            if not HttpUtils.download_file(url=url, dest_path=path):
                item[2] += 1
                cls.task_pool.put(item)
                cls.init_thread()
        else:
            print("Exceed max retry time: " + path)


if __name__ == "__main__":
    Crawler.start("289bz")
