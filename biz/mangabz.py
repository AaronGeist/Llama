# -*- coding:utf-8 -*-

import glob
import os

import re
import threading
import urllib

import execjs
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from biz.Image2pdf import Image2pdf
from biz.reorg import Reorg
from core.login import Login
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    process_thread = None
    book_id = 0
    comic_id = "0"
    comic_name = ""
    chapter_mode = 0  # 0 = all, 1 = chapter only, 2 = volume only
    root_folder = ""
    inclusion_list = None

    root_url = "http://www.mangabz.com"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "__cfduid=d4c03e68367b581a0ec1fec1316e9b8a51598759529; frombot=1; ComicHistoryitem_zh=; MANGABZ_MACHINEKEY=2efd9898-3307-42b9-8393-45852a40d936; SERVERID=node1; UM_distinctid=1743d7e769c0-0f67996b0b3d5b-31607305-13c680-1743d7e769d687; mangabzcookieenabletest=1; mangabz_newsearch=%5b%7b%22Title%22%3a%22%e7%94%b5%e9%94%af%e4%ba%ba%22%2c%22Url%22%3a%22%5c%2fsearch%3ftitle%3d%25E7%2594%25B5%25E9%2594%25AF%25E4%25BA%25BA%22%7d%5d; CNZZDATA1278095942=968942609-1598754941-null%7C1598771142; firsturl=http%3A%2F%2Fwww.mangabz.com%2Fm133935%2F; CNZZDATA1278095929=1341559288-1598755806-null%7C1598772006; CNZZDATA1278515277=1171589980-1598755229-null%7C1598771429; mangabzimgcooke=119988%7C19%2C119177%7C18%2C137361%7C9%2C137361%7C6%2C129957%7C6%2C133658%7C16%2C133935%7C2; readhistory_time=1-577-137361-3; mangabzimgpage=137361|1:1,119988|5:1,119177|4:1,137361|6:1,129957|3:1,133658|2:1,133935|1:1; image_time_cookie=129957|637343967404328629|9,133658|637343966509208508|1,137361|637343983738500918|0,133935|637343982897298023|0;",
        "DNT": "1",
        "Host": "www.mangabz.com",
        "If-Modified-Since": "Sun, 30 Aug 2020 07:32:53 GMT",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
    }

    @classmethod
    def start(cls, book_id, chapter_mode=0, inclusion_list=None):
        cls.book_id = book_id
        cls.comic_id = re.match("(\d+)", book_id).group(1)
        cls.chapter_mode = chapter_mode
        cls.inclusion_list = inclusion_list
        cls.parse_lvl_one()

        return cls.root_folder

    @classmethod
    def init_thread(cls):
        if cls.process_thread is None:
            cls.process_thread = threading.Thread(target=cls.process)
            cls.process_thread.start()

    @classmethod
    def parse_lvl_one(cls):
        if cls.book_id is None:
            print(">>>>> ERROR Cannot Parse Comic ID, QUIT! <<<<<")
            return

        resp = HttpUtils.get_with_retry("%s/%s/" % (cls.root_url, cls.book_id), headers=cls.headers)
        assert resp is not None

        cls.comic_name = HttpUtils.get_content(resp, ".detail-info-title").strip()
        cls.root_folder = os.path.join("output", cls.comic_name)
        links = HttpUtils.get_attrs(resp, "div.detail-list-form-con a", "href")

        titles = HttpUtils.get_contents(resp, "div.detail-list-form-con a")
        image_numbers = HttpUtils.get_contents(resp, "div.detail-list-form-con a span")
        image_numbers = list(map(lambda x: re.search("(\d+)P", x).group(1), image_numbers))

        assert len(titles) == len(image_numbers)
        assert len(titles) == len(links)

        cnt = 0
        for index in range(len(titles)):
            cls.init_thread()

            link = links[index].replace("/", "").replace("m", "")
            title = titles[index].strip()
            image_number = image_numbers[index]
            if (cls.chapter_mode == 1 and "第" not in title and "话" not in title and "話" not in title) or (
                                cls.chapter_mode == 2 and "卷" not in title and "第" not in title):
                print("Skip " + title)
                continue

            is_skip = False
            if cls.inclusion_list is not None:
                for inclusion in cls.inclusion_list:
                    if inclusion not in title:
                        is_skip = True
                        break

            if not is_skip and cls.parse_lvl_two((link, title, image_number)):
                cnt += 1

        if cnt > 0:
            cls.process_thread.join()

        # code below should be useless if everything goes well
        while not cls.task_pool.empty():
            print("pool size = " + str(cls.task_pool.qsize()))
            cls.init_thread()
            cls.process_thread.join()

    @classmethod
    def parse_lvl_two(cls, info):
        chapter_id = info[0]
        title = info[1]
        image_number = int(info[2])

        # create folder once
        folder_name = os.path.join(cls.root_folder, title)
        # folder_name = "output/" + cls.comic_name + "/" + title + "_" + chapter_id
        if not os.path.exists(folder_name):
            os.makedirs(folder_name, exist_ok=True)

        path_file_number = len(glob.glob(pathname=folder_name + '/*'))
        if path_file_number == image_number:
            print("Downloaded：" + title)
            # already downloaded all
            return False

        print("Start downloading: " + title)

        first_url = "http://www.mangabz.com/m%s/" % chapter_id

        headers = cls.headers
        headers["Cookie"] = headers["Cookie"] + urllib.parse.quote(first_url)
        headers["Referer"] = first_url

        index = 0
        while index < image_number:
            index += 1

            query_url = "%s/m%s/chapterimage.ashx?cid=%s&page=%d" % (cls.root_url, chapter_id, chapter_id, index)

            content = HttpUtils.get_with_retry(query_url, headers=headers, return_raw=True)

            if content.text.strip() == "":
                print("url: " + query_url)
                print("get wrong data: \"" + content.text.strip() + "\"")
                print("fail to parse image key, %s-%d" % (title, index))
            else:
                try:
                    image_url_list = execjs.eval(content.text)
                except:
                    print(">>>>>>>>>> fail to parse image: " + str(index))
                    continue

                assert len(image_url_list) > 0

                image_keys = list()
                for image_url in image_url_list:
                    match = re.search("/(\d+_\d{4}).(\w+)\?", image_url)
                    if match is not None:
                        image_key = match.group(1)
                        surfix = match.group(2)
                        image_keys.append(image_key)

                        file_path = folder_name + "/" + image_key + "." + surfix
                        cls.task_pool.put([file_path, image_url, 0])

                assert len(image_keys) > 0, query_url

                # sort & find largest image number
                image_keys.sort(key=lambda x: int(x.split("_")[0]))
                index = max(int(image_keys[-1].split("_")[0]), index)
                print("now index[%d], total[%d]" % (index, image_number))

        return True

    @classmethod
    def process(cls):
        print("#### process thread started")
        with ThreadPoolExecutor(max_workers=50) as executor:
            while True:
                try:
                    # queue timeout should be greater than the download timeout
                    item = cls.task_pool.get(timeout=30)
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
    is_re_org = False
    is_pdf_gen = False
    comic_id = "577bz"
    chapter_mode = 0  # 0=所有，1=话，2=卷
    is_reverse_split = True
    root_folder = "archive/" + comic_id
    inclusion_list = None

    # pdf_root_folder = "/Users/shakazxx/workspace/github/Llama/biz/output/電鋸人/第88話 STAR CHAINSAW"
    # inclusion_list = ["88"]

    root_folder = Crawler.start(comic_id, chapter_mode=chapter_mode, inclusion_list=inclusion_list)
    print("#########################################")
    print("#### Finish download ####")
    print("#########################################")

    if is_re_org:
        root_folder = Reorg.process(root_folder)

        print("#########################################")
        print("#### Finish reorganization ####")
        print("#########################################")

    if is_pdf_gen:
        Image2pdf.merge_all(folder_path=root_folder, reverse=is_reverse_split)
        print("#########################################")
        print("#### Finish PDF generation ####")
        print("#########################################")

        # 511bz 進擊的巨人  131话
        # 157bz 黑执事
        # 135bz 堀與宮村
        # 577bz 电锯人
        # 1631bz blame
        # 992bz 暗杀教室
        # 559bz 死亡笔记
        # 266bz 咒术回战
        # 706bz 迷宫饭
        # 188bz 月刊少女
        # 9bz   家庭教师
        # 610bz 龙珠超
        # 83bz 约定的梦幻岛
