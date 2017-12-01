# -*- coding:utf-8 -*-
import json
import re

from core.db import Cache
from core.emailSender import EmailSender
from core.login import Login
from core.monitor import Monitor
from core.seedManager import SeedManager
from model.seed import SeedInfo
from model.site import Site
from util.ParallelTemplate import ParallelTemplate
from util.config import Config
from util.utils import HttpUtils


class HDH(Login):
    site = None

    def generate_site(self):
        site = Site()
        site.home_page = "http://hdhome.org/torrents.php"
        site.login_page = "http://hdhome.org/takelogin.php"
        site.login_headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "hdhome.org",
            "Referer": "http://hdhome.org/index.php",
            "Upgrade-Insecure-Requests": "1",
            "Cookie": "__cfduid=d485315600280be35365e84ee5ec16d651512109005; c_secure_uid=ODU1MzM%3D; c_secure_pass=847ef9da672b8f7ef43c2952b06473b7; c_secure_ssl=bm9wZQ%3D%3D; c_secure_tracker_ssl=bm9wZQ%3D%3D; c_secure_login=bm9wZQ%3D%3D"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#nav_block a.User_Name b"
        site.login_verify_str = Config.get("hdh_username")

        self.site = site

        return site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password

        return data

    def crawl(self):
        site = self.generate_site()
        assert self.login(site)

        for i in range(107, 164):
            soup_obj = HttpUtils.get(site.home_page + "?page=" + str(i), headers=site.login_headers)
            ids = self.parse(soup_obj)
            ParallelTemplate(150).run(func=self.say_thank, inputs=ids)
            print(">>>>>> finish page " + str(i))

    def parse(self, soup_obj):
        assert soup_obj is not None

        tr_list = soup_obj.select("table.torrents tr")

        ids = []
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

            url = tr.select("table.torrentname tr td:nth-of-type(1) a")[0]['href']
            id = self.parse_id(url)

            ids.append(id)

        return ids

    @staticmethod
    def parse_size(soup_obj):
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

    @staticmethod
    def clean_tag(soup_obj):
        assert soup_obj is not None
        html = str(soup_obj.contents[0])
        html = html.replace(',', '')
        m = re.search(">(\d+\.*\d?)<", html)
        if m:
            ret = m.group(1)
        else:
            ret = html
        return ret

    @staticmethod
    def parse_id(url):
        m = re.search("id=(\d+)&", url)
        assert m is not None
        return m.group(1)

    def filter(self, data):
        # common strategy
        # 1. hasn't been found before
        # 2. not exceed max size
        max_size = Config.get("seed_max_size_mb")
        data = list(filter(lambda x: x.size < max_size, data))

        # sticky
        filtered_seeds = set(filter(lambda x: x.sticky and (x.free or x.discount <= 50), data))

        # white list
        white_lists = Config.get("putao_white_list").split("|")
        for seed in data:
            for white_list in white_lists:
                if re.search(white_list, seed.title):
                    filtered_seeds.add(seed)
                    break

        for seed in filtered_seeds:
            print("Add seed: " + str(seed))

        return filtered_seeds

    def say_thank(self, id):
        site = self.generate_site()
        assert self.login(site)

        url = "http://hdhome.org/thanks.php"

        form_data = {"id": id}
        HttpUtils.post(url, data=form_data, headers=self.site.login_headers, returnRaw=True)
        print("Say thanks to " + str(id))

    def check(self):
        data = self.crawl()
        # self.action(self.filter(data))


if __name__ == "__main__":
    HDH().crawl()