import glob
import os
import re
import threading
import urllib
import execjs
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

    root_url = "http://www.36mh.com"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "www.36mh.com",
        "If-Modified-Since": "Sun, 30 Aug 2020 07:32:53 GMT",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
    }

    mobile_headers = {
        "Host": "img001.shmkks.com:443",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36"""
    }

    @classmethod
    def start(cls, book_id):
        cls.book_id = book_id
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

        url = "http://www.36mh.com/manhua/%s/" % cls.book_id
        retry = 0
        while True:
            resp = HttpUtils.get(url, headers=cls.headers)
            if resp is not None:
                break
            else:
                retry += 1

            assert retry < 5, "fail to query %s" % url

        cls.comic_name = HttpUtils.get_content(resp, "title").strip()
        links = HttpUtils.get_attrs(resp, "#chapter-list-4 li a", "href")

        titles = HttpUtils.get_contents(resp, "#chapter-list-4 li a span")

        assert len(titles) == len(links)

        cls.init_thread()

        for index in range(len(titles)):
            link = links[index]
            title = titles[index].strip()
            cls.parse_lvl_two((link, title))
            break
        cls.process_thread.join()

        # code below should be useless if everything goes well
        while not cls.task_pool.empty():
            print("pool size = " + str(cls.task_pool.qsize()))
            cls.init_thread()
            cls.process_thread.join()

    @classmethod
    def parse_lvl_two(cls, info):
        chapter_url = info[0]
        title = info[1]

        # create folder once
        folder_name = "output/" + cls.comic_name + "/" + title
        if not os.path.exists(folder_name):
            os.makedirs(folder_name, exist_ok=True)

        #
        # path_file_number = len(glob.glob(pathname=folder_name + '/*'))
        # if path_file_number == image_number:
        #     print("下载完毕：" + title)
        #     # already downloaded all
        #     return

        print("开始下载: " + title)

        query_url = cls.root_url + chapter_url

        retry = 0
        while True:
            content = HttpUtils.get(query_url, headers=cls.headers)
            if content is not None:
                break
            else:
                retry += 1

        assert retry < 5, "fail to query %s" % query_url

        script_content = HttpUtils.get_contents(content, "script")
        # print(script_content[2][1:].replace(";;", ";").replace(";", ";\n"))

        image_url_list = re.search("chapterImages.*=.*\[(.*)\];", script_content[2]).group(1).replace("\"", "").split(
            ",")

        path = re.search("chapterPath.*?=.*?\"(.*?)\";", script_content[2]).group(1)

        assert len(image_url_list) > 0

        index = 1
        for image_url in image_url_list:
            full_image_url = "https://img001.shmkks.com/" + path + image_url
            file_path = "%s/%03d_%s" % (folder_name, index, image_url)
            cls.task_pool.put([file_path, full_image_url, 0])
            index += 1

    @classmethod
    def process(cls):
        print("#### process thread started")
        with ThreadPoolExecutor(max_workers=50) as executor:
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
            if not HttpUtils.download_file(url=url, dest_path=path, headers=cls.mobile_headers):
                item[2] += 1
                cls.task_pool.put(item)
                cls.init_thread()
        else:
            print("Exceed max retry time: " + path)


if __name__ == "__main__":
    Crawler.start("wunengdenainai")
