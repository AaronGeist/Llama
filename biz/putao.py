# -*- coding:utf-8 -*-

import re
from concurrent.futures import ThreadPoolExecutor

from core.db import Cache
from core.email import EmailSender
from core.login import Login
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class FreeFeedAlert:
    cache = None

    @classmethod
    def init(cls):
        if cls.cache is None:
            cls.cache = Cache()

    @classmethod
    def generate_site(cls):
        site = Site()
        site.home_page = "https://pt.sjtu.edu.cn/torrents.php"
        site.login_page = "https://pt.sjtu.edu.cn/takelogin.php"
        site.login_headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#userbar span.nobr a b"
        site.login_verify_str = Config.get("putao_username")
        site.login_username = Config.get("putao_username")
        site.login_password = Config.get("putao_password")

        return site

    @classmethod
    def crawl(cls):
        site = cls.generate_site()
        assert Login.login(site)

        soup_obj = HttpUtils.get(site.home_page)
        return cls.parse(soup_obj)

    @classmethod
    def parse(cls, soup_obj):
        assert soup_obj is not None

        tr_list = soup_obj.select("table.torrents tr")

        seeds = []
        cnt = 0
        for tr in tr_list:
            cnt += 1
            if cnt == 1:
                # skip the caption tr
                continue

            seed = SeedInfo()
            td_list = tr.select("td.rowfollow")
            if len(td_list) < 9:
                # skip embedded contents
                continue

            seed.title = td_list[1].select("table td a")[0]["title"]
            seed.url = td_list[1].select("table td a")[0]['href']
            seed.free = len(td_list[1].select("table font.free")) > 0
            seed.hot = len(td_list[1].select("table font.hot")) > 0
            seed.since = HttpUtils.get_content(td_list[3], "span")
            seed.size = float(cls.parse_size(td_list[4]))
            seed.upload_num = int(cls.clean_tag(td_list[5]))
            seed.download_num = int(cls.clean_tag(td_list[6]))
            seed.finish_num = int(cls.clean_tag(td_list[7]))
            seed.id = cls.parse_id(seed.url)

            seeds.append(seed)

        return seeds

    @classmethod
    def parse_size(cls, soup_obj):
        assert soup_obj is not None
        assert len(soup_obj.contents) == 3

        size_num = float(soup_obj.contents[0])
        size_unit = soup_obj.contents[2]

        if size_unit == "GB":
            return size_num * 1024
        if size_unit == "MB":
            return size_num
        if size_unit == "KB":
            return 0.01

    @classmethod
    def clean_tag(cls, soup_obj):
        assert soup_obj is not None
        html = str(soup_obj.contents[0])
        html = html.replace(',', '')
        m = re.search(">(\d+\.*\d?)<", html)
        if m:
            ret = m.group(1)
        else:
            ret = html
        return ret

    @classmethod
    def parse_id(cls, url):
        m = re.search("id=(\d+)&", url)
        assert m is not None
        return m.group(1)

    @classmethod
    def filter(cls, data):
        # strategies:
        # 1. free seed
        # 2. hasn't been found before
        filtered_seeds = list(filter(lambda x: x.free and cls.cache.get(x.id) is None, data))
        for seed in filtered_seeds:
            # keep in cache for 2 days
            cls.cache.set_with_expire(seed.id, str(seed), 172800)

        return filtered_seeds

    @classmethod
    def notify(cls, data):
        if len(data) == 0:
            return

        msg = ""
        for seed in data:
            msg += str(seed)

        EmailSender.send(u"种子", msg)

    @classmethod
    def check(cls):
        cls.init()
        cls.notify(cls.filter(cls.crawl()))


class MagicPointChecker(FreeFeedAlert):
    @classmethod
    def generate_site(cls):
        site = super().generate_site()
        site.home_page = "https://pt.sjtu.edu.cn/mybonus.php"
        return site

    @classmethod
    def parse(cls, soup_obj):
        assert soup_obj is not None

        div_list = soup_obj.select("table.mainouter tr td table tr td div[align='center']")
        assert len(div_list) == 1

        content = div_list[0].contents[0]
        m = re.search(u"获取(\d+.\d+)个魔力", content)
        assert m
        return float(m.group(1))

    @classmethod
    def filter(cls, data):
        if data <= Config.get("putao_mp_threshold"):
            return data
        else:
            return None

    @classmethod
    def notify(cls, data):
        if data is not None:
            EmailSender.send("魔力值警告: " + str(data), "")


class Exchanger(FreeFeedAlert):
    @classmethod
    def generate_site(cls):
        site = super().generate_site()
        site.home_page = "https://pt.sjtu.edu.cn/mybonus.php"
        return site

    @classmethod
    def exchange_mp(cls, times=1):
        site = cls.generate_site()
        is_login = Login.login(site)
        assert is_login

        data = dict()
        data['option'] = 3  # 1=1GB 2=5GB 3=10GB
        data['art'] = "traffic"

        with ThreadPoolExecutor(max_workers=times) as executor:
            var = {executor.submit(HttpUtils.post("https://pt.sjtu.edu.cn/mybonus.php?action=exchange", data=data,
                                                  headers=site.login_headers, returnRaw=True)): item for item in
                   range(1, times + 1)}


if __name__ == "__main__":
    FreeFeedAlert.check()
    # MagicPointChecker.check()
    # Exchanger.exchange_mp()
