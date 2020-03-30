import json
import os
import re
import base64
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from core.login import Login
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    process_thread = None
    book_id = 0

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

        soup_obj = HttpUtils.get("http://www.u17.com/comic/%s.html" % cls.book_id)
        assert soup_obj is not None

        chapters = soup_obj.select("ul#chapter li a")

        cls.init_thread()

        for chapter in chapters:
            final_url = chapter["href"]
            cls.parse_lvl_two(final_url)
        cls.process_thread.join()

        # code below should be useless if everything goes well
        while not cls.task_pool.empty():
            print("pool size = " + str(cls.task_pool.qsize()))
            cls.init_thread()
            cls.process_thread.join()

    @classmethod
    def parse_lvl_two(cls, url):
        content = HttpUtils.get(url, return_raw=True)
        assert content is not None

        m = re.search("chapter: \$\.evalJSON\(\'(.*)\'\),", content.text)
        if not m or m.group(1) == "null":
            m = re.search("chapter: (.*),", content.text)
        assert m
        json_data = json.loads(m.group(1))
        book = json_data["comic_id"]
        number = json_data["chapter_id"]
        title = json_data["name"].strip().replace(" ", "-").replace("（", "(").replace("）", ")")

        # create folder once
        folder_name = "%s/%08d_%s" % (book, int(number), title)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        m = re.search("image_list: \$\.evalJSON\(\'(.*)\'\),", content.text)
        if not m or m.group(1) == "null":
            m = re.search("image_list: (.*),", content.text)
        assert m
        json_data = json.loads(m.group(1))

        for index in json_data.keys():
            image_data = json_data[index]
            page = image_data["page"]
            image_url = base64.decodebytes(image_data["src"].encode("utf-8")).decode("utf-8")
            format = image_url.split(".")[-1]
            image_file_name = "%03d.%s" % (int(page), format)

            file_path = "/".join([folder_name, image_file_name])
            cls.task_pool.put([file_path, image_url, 0])


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
            if not HttpUtils.download_file(url=url, dest_path=path):
                print("Fail download %s %d" % (path, retry))
                item[2] += 1
                cls.task_pool.put(item)
                cls.init_thread()
        else:
            print("Exceed max retry time: " + path)

    @classmethod
    def generate_site(cls):
        site = Site()
        site.home_page = "http://u.ishuhui.com/"
        site.login_page = "http://u.ishuhui.com/login"

        site.login_needed = True
        site.login_verify_str = Config.get("shuhui_nickname")
        site.login_username = Config.get("shuhui_username")
        site.login_password = Config.get("shuhui_password")

        return site

    @classmethod
    def build_post_data(self, site):
        data = dict()
        data['name'] = site.login_username
        data['password'] = site.login_password

        return data

    @classmethod
    def check_login(self, site):
        resp = HttpUtils.post(site.home_page, data={}, returnRaw=True).text
        jsonValue = json.loads(resp)
        if jsonValue['errNo'] == 0:
            content = jsonValue['data']['name']
            return content is not None and content == site.login_verify_str
        else:
            return False

    @classmethod
    def try_login(cls):
        assert cls.login(cls.generate_site())


if __name__ == "__main__":
    Crawler.start(704)
    # Crawler.try_login()