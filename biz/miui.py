# -*- coding:utf-8 -*-
import json
import re
import os
from concurrent.futures import ThreadPoolExecutor

from core.db import Cache
from core.emailSender import EmailSender
from core.login import Login
from core.monitor import Monitor
from core.seedManager import SeedManager
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class Miui(Login):
    def generate_site(self):
        site = Site()

        site.home_page = "http://www.miui.com/forum.php?mod=forumdisplay&fid=773&filter=author&orderby=dateline"
        site.login_headers = {
            "User-agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-encoding": "gzip, deflate",
            "Accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "www.miui.com",
            "Referer": "http://www.miui.com/home.php?mod=space&do=notice&view=interactive",
            "Upgrade-insecure-requests": "1",
            "Cache-control": "max-age=0",
            "Cookie": "UM_distinctid=163dfb3e2ff73d-0a9bc0e1447ce4-336a7706-13c680-163dfb3e3005eb; CNZZDATA5677709=cnzz_eid%3D1297791920-1528461510-http%253A%252F%252Fwww.miui.com%252F%26ntime%3D1528477020; CNZZDATA1270690907=893238151-1528481971-https%253A%252F%252Fwww.baidu.com%252F%7C1528481971; __utmc=230417408; __utmz=230417408.1528538555.3.3.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; Hm_lvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528511334,1528511372,1528511379,1528538555; PHPSESSID=vnc60biqa61d31ih5b930abm41; MIUI_2132_widthauto=-1; CNZZDATA2441309=cnzz_eid%3D1987410948-1528462183-null%26ntime%3D1528586803; CNZZDATA30049650=cnzz_eid%3D1453184979-1528466198-null%26ntime%3D1528585841; __utma=230417408.2038836981.1528511192.1528549122.1528589392.5; CNZZDATA5557939=cnzz_eid%3D1504230810-1528462019-null%26ntime%3D1528586646; MIUI_2132_saltkey=sF6wQsSz; MIUI_2132_lastvisit=1528586043; MIUI_2132_visitedfid=773; MIUI_2132_ulastactivity=426f3zvob00mxZWwQ8FWbaETgRqM07T%2FhlJ%2FdhF%2F34sFvhOFvrFk5fg; MIUI_2132_auth=443fj0wdiMkvdCfJKHGlfDsueGlS1sPWf%2BJ%2BQMa323mysEuk6RBvZHg; lastLoginTime=d9e2yZbafd8tt3%2BIQc55QkmXvFWlG588oMrLYGlAZoyMMlgcAOs7; MIUI_2132_forum_lastvisit=D_773_1528589818; MIUI_2132_noticeTitle=1; MIUI_2132_checkpm=1; MIUI_2132_lastact=1528590043%09home.php%09misc; MIUI_2132_sendmail=1; __utmb=230417408.13.10.1528589392; Hm_lpvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528589985"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#hd_u_name"
        site.login_verify_str = "\n                            胡迪君                        "
        site.login_username = Config.get("putao_username")
        site.login_password = Config.get("putao_password")

        return site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password
        data['checkcode'] = "XxXx"

        return data

    def crawl(self):
        site = self.generate_site()
        assert self.login(site)

        print("Login success!")

        # soup_obj = HttpUtils.get(site.home_page)
        # return self.parse(soup_obj)

    def parse(self, soup_obj):
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

            seed.sticky = len(td_list[1].select("table td img[alt=\"Sticky\"]")) > 0
            seed.title = td_list[1].select("table td a")[0]["title"]
            seed.url = td_list[1].select("table td a")[0]['href']
            seed.free = len(td_list[1].select("table font.free")) > 0
            seed.hot = len(td_list[1].select("table font.hot")) > 0
            seed.since = HttpUtils.get_content(td_list[3], "span")
            seed.size = float(self.parse_size(td_list[4]))
            seed.upload_num = int(self.clean_tag(td_list[5]))
            seed.download_num = int(self.clean_tag(td_list[6]))
            seed.finish_num = int(self.clean_tag(td_list[7]))
            seed.id = self.parse_id(seed.url)

            seeds.append(seed)

        return seeds

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
        data = list(filter(lambda x: x.size < max_size and Cache().get(x.id) is None, data))

        # sticky
        filtered_seeds = set(filter(lambda x: x.sticky, data))

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

    def action(self, data):
        if len(data) == 0:
            return

        # send email
        for seed in data:
            EmailSender.send(u"种子", str(seed))
            Cache().set_with_expire(seed.id, str(seed), 864000)

        SeedManager.try_add_seeds(data)

    def check(self):
        data = self.crawl()
        self.action(self.filter(data))


if __name__ == '__main__':
    miui = Miui()
    miui.crawl()