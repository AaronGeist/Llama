import json
import os
import re
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

        soup_obj = HttpUtils.get("http://www.ishuhui.com/cartoon/book/%d" % cls.book_id)
        sub_book_id = json.loads(soup_obj.select("meta[name='ver']")[0]['content'])['c']

        resp = HttpUtils.get("http://api.ishuhui.com/cartoon/book_ish/ver/%s/id/%d.json" % (sub_book_id, cls.book_id),
                             return_raw=True)
        assert resp is not None

        json_data = json.loads(resp.text)
        cartoons = json_data["data"]["cartoon"]

        cls.init_thread()

        for type in cartoons.keys():
            posts = cartoons[type]["posts"]
            for post_id in posts.keys():
                url = "http://api.ishuhui.com/cartoon/post/ver/%s/num/%d-%s-%s.json" % (sub_book_id,
                                                                                        cls.book_id, type, post_id)
                inner_content = HttpUtils.get(url, return_raw=True)
                assert inner_content is not None
                inner_json_data = json.loads(inner_content.text)
                inner_url = inner_json_data["data"]["posts"][0]["url"]
                m = re.search('id=(\d+)', inner_url)
                if m:
                    inner_id = m.group(1)
                    final_url = "http://hhzapi.ishuhui.com/cartoon/post/ver/%s/id/%s.json" % (sub_book_id, inner_id)
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
        json_data = json.loads(content.text)
        book = json_data["data"]["book"]
        title = json_data["data"]["title"]
        number = json_data["data"]["number"]
        content_img = json_data["data"]["content_img"]
        images = json.loads(content_img)

        # create folder once
        folder_name = "%s/%03d_%s" % (book, int(number), title)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for image in images.keys():
            image_file_name = image
            image_url = "http://hhzapi.ishuhui.com%s" % images[image]
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
        resp = HttpUtils.post(site.home_page, data={}, returnRaw=True)
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
    Crawler.start(56)
    # Crawler.try_login()
