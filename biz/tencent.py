import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from core.login import Login
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    process_thread = None
    book_id = 0
    stopFlag = False

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

        soup_obj = HttpUtils.get("http://ac.qq.com/Comic/ComicInfo/id/%s" % cls.book_id)
        assert soup_obj is not None

        chapters = soup_obj.select("ol.works-chapter-list span.works-chapter-item a")

        cls.init_thread()

        for chapter in chapters:
            final_url = "http://ac.qq.com" + chapter["href"]
            cls.parse_lvl_two(final_url)

        # code below should be useless if everything goes well
        while not cls.task_pool.empty():
            print("pool size = " + str(cls.task_pool.qsize()))
            time.sleep(10)

        cls.stopFlag = True

    @classmethod
    def parse_lvl_two(cls, url):
        content = HttpUtils.get(url, return_raw=True)
        assert content is not None

        location = os.path.join(os.path.dirname(__file__), "../bin/phantomjs")
        jsFile = os.path.join(os.path.dirname(__file__), "../static/tencent_comic.js")

        print(">>> parsing " + url)
        data = os.popen("%s %s %s" % (location, jsFile, url)).read()
        # retry twice
        if data is None:
            data = os.popen("%s %s %s" % (location, jsFile, url)).read()

        assert data is not None
        print("****** data=" + data)
        json_data = json.loads(data)

        book = json_data["title"]
        number = json_data["cid"]
        title = json_data["cTitle"].strip().replace(" ", "-").replace("（", "(").replace("）", ")")

        # create folder once
        folder_name = "%s/%08d_%s" % (book, int(number), title)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for index in json_data["picture"].keys():
            image_url = json_data["picture"][index]
            format = "png"
            image_file_name = "%03d.%s" % (int(index), format)

            file_path = "/".join([folder_name, image_file_name])
            cls.task_pool.put([file_path, image_url, 0])

    @classmethod
    def process(cls):
        print("#### process thread started")
        with ThreadPoolExecutor(max_workers=50) as executor:
            while not cls.stopFlag:
                try:
                    # queue timeout should be greater than the download timeout
                    item = cls.task_pool.get(timeout=60)
                    executor.submit(cls.do_process, item)
                except Empty as e:
                    print("#### queue timeout")
                    # break
        cls.process_thread = None
        print("#### process thread stopped")

    @classmethod
    def do_process(cls, item):
        path = item[0]
        url = item[1]
        retry = item[2]
        if retry <= 5:
            if not HttpUtils.download_file(url=url, dest_path=path):
                print("Fail download %s %d" % (path, retry))
                item[2] += 1
                cls.task_pool.put(item)
                cls.init_thread()
        else:
            print("Exceed max retry time: " + path)


if __name__ == "__main__":
    Crawler.start(530131)
