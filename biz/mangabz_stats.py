# -*- coding:utf-8 -*-

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from core.login import Login
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    output_pool = Queue()
    process_thread = None
    output_thread = None
    book_id = 0
    comic_id = "0"
    comic_name = ""
    chapter_mode = 0  # 0 = all, 1 = chapter only, 2 = volume only
    root_folder = ""
    inclusion_list = None

    fp = None

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
    def start(cls):

        root_url = "http://www.mangabz.com/manga-list-p%d/"
        page_num = 0


        while True:
            cls.init_thread()

            page_num += 1
            print("Now page " + str(page_num))
            url = root_url % page_num
            resp = HttpUtils.get_with_retry(url, headers=cls.headers)
            if resp is None:
                break

            links = HttpUtils.get_attrs(resp, ".mh-item-detali > .title > a", "href")
            if len(links) == 0:
                break

            for link in links:
                cls.task_pool.put(link)

        cls.process_thread.join()
        cls.fp.close()

    @classmethod
    def init_thread(cls):
        if cls.process_thread is None:
            cls.process_thread = threading.Thread(target=cls.process)
            cls.process_thread.start()
        if cls.output_thread is None:
            cls.output_thread = threading.Thread(target=cls.output_process)
            cls.output_thread.start()

        if cls.fp is None:
            cls.fp = open("output/mangabz.csv", "w", encoding="utf-8")

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
    def output_process(cls):
        print("#### output thread started")
        with ThreadPoolExecutor(max_workers=1) as executor:
            while True:
                try:
                    # queue timeout should be greater than the download timeout
                    item = cls.output_pool.get(timeout=30)
                    executor.submit(cls.do_output_process, item)
                except Empty as e:
                    print("#### output queue timeout")
                    break
        cls.output_thread = None
        print("#### output thread stopped")

    @classmethod
    def do_output_process(cls, item):
        (comic_name, comic_author, comic_status, max_chap, max_vol, link) = item
        print(comic_name, comic_author, comic_status, max_chap, max_vol, link)

        cls.fp.writelines(",".join([comic_name, comic_author, comic_status, str(max_chap), str(max_vol), link]))
        cls.fp.writelines("\n")

        cls.fp.flush()

    @classmethod
    def do_process(cls, link):
        resp = HttpUtils.get_with_retry(cls.root_url + link, headers=cls.headers)
        assert resp is not None

        cls.comic_name = HttpUtils.get_content(resp, ".detail-info-title").strip()
        comic_author = HttpUtils.get_content(resp, ".detail-info-tip span a").strip()
        comic_status = HttpUtils.get_content(resp, ".detail-info-tip span:nth-of-type(2) span").strip()
        titles = HttpUtils.get_contents(resp, "div.detail-list-form-con a")

        # validation
        titles = list(map(lambda x: x.strip(), titles))
        if len(titles) == 0:
            return

        chap_ids = list()
        vol_ids = list()
        for title in titles:
            id = re.search(".+?(\d*).+?", title).group(1)
            if id == "":
                # print("Cannot parse: " + title)
                pass
            else:
                if "話" in title:
                    chap_ids.append(int(id))
                elif "卷" in title:
                    vol_ids.append(int(id))

        max_chap = -1
        max_vol = -1
        is_missed = False
        if len(chap_ids) > 0:
            missing_ids = list()
            chap_ids.sort()
            max_chap = chap_ids[-1]

            for i in range(1, max_chap + 1):
                if i not in chap_ids:
                    missing_ids.append(i)
            if len(missing_ids) > 0:
                # print("Missing chapters: " + str(missing_ids))
                is_missed = True

        if len(vol_ids) > 0:
            missing_ids = list()
            vol_ids.sort()
            max_vol = vol_ids[-1]

            for i in range(1, max_vol + 1):
                if i not in vol_ids:
                    missing_ids.append(i)
            if len(missing_ids) > 0:
                # print("Missing volumes: " + str(missing_ids))
                is_missed = True

        if not is_missed:
            # print(">>>>>>>>>>>> WOW! FULL SET: %s <<<<<<<<<<<<" % cls.comic_name)
            cls.output_pool.put((cls.comic_name, comic_author, comic_status, max_chap, max_vol, link))


if __name__ == "__main__":
    Crawler.start()

    # Crawler.do_process("/369bz")
