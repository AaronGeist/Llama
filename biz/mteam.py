# -*- coding:utf-8 -*-
import json
import re

from core.db import Cache
from core.emailSender import EmailSender
from core.login import Login
from core.monitor import Monitor
from core.seedManager import SeedManager
from model.ptUser import User
from model.seed import SeedInfo
from model.site import Site
from util.ParallelTemplate import ParallelTemplate
from util.config import Config
from util.utils import HttpUtils


class NormalAlert(Login):
    site = Site()
    size_factor = 1.074  # the shown size on web page is not accurate

    def __init__(self):
        self.site.home_page = "https://tp.m-team.cc/torrents.php"
        self.site.login_page = "https://tp.m-team.cc/takelogin.php"
        self.site.login_headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "DNT": "1",
            "Host": "tp.m-team.cc",
            "Origin": "https://tp.m-team.cc",
            "Referer": "https://tp.m-team.cc/login.php",
            "Upgrade-Insecure-Requests": "1",
            # "Cookie": "tp=Yzc1NDY4MTU3MDcyNjcyOTEyNmU3OTJjNTVjOTgxNTIzOWE4NDdjYQ%3D%3D"
        }

        self.site.login_needed = True
        self.site.login_verify_css_selector = "#info_block span.nowrap a b"
        self.site.login_verify_str = Config.get("mteam_username")
        self.site.login_username = Config.get("mteam_username")
        self.site.login_password = Config.get("mteam_password")

    def generate_site(self):
        return self.site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password

        return data

    def crawl(self):
        site = self.generate_site()
        assert self.login(site)

        soup_obj = HttpUtils.get(site.home_page, headers=site.login_headers)
        return self.parse(soup_obj)

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

            seed.since = HttpUtils.get_content(td_list[2], "span")
            seed.size = float(self.parse_size(td_list[3]))
            seed.upload_num = int(self.clean_tag(td_list[4]))
            seed.download_num = int(self.clean_tag(td_list[5]))
            seed.finish_num = int(self.clean_tag(td_list[6]))

            td_title = tr.select("td.torrenttr tr td")
            seed.sticky = len(td_title[0].select("img[alt=\"Sticky\"]")) > 0
            seed.title = td_title[0].select("a")[0]["title"]
            seed.url = td_title[0].select("a")[0]['href']
            seed.free = len(td_title[0].select("img[alt=\"Free\"]")) > 0
            seed.hot = len(td_title[0].select("font.hot")) > 0
            if len(td_title[0].select("img[alt=\"50%\"]")) > 0:
                seed.discount = 50
            elif len(td_title[0].select("img[alt=\"30%\"]")) > 0:
                seed.discount = 30
            seed.id = self.parse_id(seed.url)

            seeds.append(seed)

        return seeds

    def parse_size(self, soup_obj):
        assert soup_obj is not None
        assert len(soup_obj.contents) == 3

        size_num = round(float(soup_obj.contents[0]) * self.size_factor, 2)
        size_unit = soup_obj.contents[2]

        return HttpUtils.pretty_format(str(size_num) + str(size_unit), "MB")

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

        # customized strategy
        filtered_seeds = set(filter(
            lambda x: (x.upload_num != 0 and round(x.download_num / x.upload_num, 1) >= 1.5) and
                      (x.free or (x.sticky and x.discount <= 50) or (
                          x.discount <= 50 and round(x.download_num / x.upload_num) >= 2) or ((
                          x.discount > 50 and round(x.download_num / x.upload_num) >= 3 and x.upload_num <= 10))),
            data))

        # white list
        white_lists = Config.get("putao_white_list").split("|")
        for seed in data:
            for white_list in white_lists:
                if re.search(white_list, seed.title):
                    filtered_seeds.add(seed)
                    break

        for seed in filtered_seeds:
            print("Find valuable seed: " + str(seed))

        return filtered_seeds

    def action(self, data):
        if len(data) == 0:
            return

            # send email
        for seed in data:
            EmailSender.send(u"种子", str(seed))

        success_seeds = SeedManager.try_add_seeds(data)

        for success_seed in success_seeds:
            Cache().set_with_expire(success_seed.id, str(success_seed), 5 * 864000)

    def check(self):
        self.action(self.filter(self.crawl()))


class AdultAlert(NormalAlert):
    def generate_site(self):
        self.site.home_page = "https://tp.m-team.cc/adult.php"
        return self.site


class MagicPointChecker(NormalAlert, Monitor):
    def get_bucket(self):
        return "mteam_mp"

    def generate_site(self):
        site = super().generate_site()
        site.home_page = "https://tp.m-team.cc/mybonus.php"
        return site

    def parse(self, soup_obj):
        assert soup_obj is not None

        div_list = soup_obj.select("#outer table:nth-of-type(3) table tr:nth-of-type(2) td:nth-of-type(4)")
        assert len(div_list) == 1

        content = div_list[0].contents[0]
        m = re.search(u"可獲得(\d+.\d+)魔力值", content)
        assert m
        return float(m.group(1))

    def action(self, data):
        threshold = Config.get("mteam_mp_threshold")
        if data <= threshold:
            EmailSender.send("魔力值警告: %s <= %s" % (str(data), threshold), "")

    def filter(self, data):
        return data

    def generate_data(self):
        return self.crawl()


class UploadMonitor(MagicPointChecker):
    def get_bucket(self):
        return "mteam_upload"

    def parse(self, soup_obj):
        assert soup_obj is not None

        span_list = soup_obj.select("#usermsglink span")
        return span_list[1].contents[2].replace("TB", "").strip()


class UserCrawl(Login):
    site = None

    buffer = []
    errors = []

    def generate_site(self):
        site = Site()
        site.home_page = "https://tp.m-team.cc/userdetails.php?id="
        site.login_page = "https://tp.m-team.cc/takelogin.php"
        site.login_headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "DNT": "1",
            "Host": "tp.m-team.cc",
            "Origin": "https://tp.m-team.cc",
            "Referer": "https://tp.m-team.cc/login.php",
            "Upgrade-Insecure-Requests": "1",
            "Cookie": "tp=NjM1NmNkODExODNlMjQ5YTAyOTAwYmJlMjdkMGRjMGUwMWI2ZjE0Nw%3D%3D"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#info_block span.nowrap a b"
        site.login_verify_str = Config.get("mteam_username")
        site.login_username = Config.get("mteam_username")
        site.login_password = Config.get("mteam_password")

        self.site = site

        return site

    def single(self, i):
        try:
            url = self.site.home_page + str(i)
            soup_obj = HttpUtils.get(url, headers=self.site.login_headers, return_raw=False)
            assert soup_obj is not None

            user = User()
            user.id = i
            user.name = HttpUtils.get_content(soup_obj, "#outer h1 span b")

            if user.name is None:
                return

            try:
                user.is_ban = len(soup_obj.select("#outer h1 span img[alt='Disabled']")) > 0

                if len(soup_obj.select("#outer table tr")) <= 5:
                    user.is_secret = True
                    print("secret user: id=" + str(i))
                else:

                    tr_list = soup_obj.select("#outer table tr")
                    for tr in tr_list:
                        td_name = HttpUtils.get_content(tr, "td:nth-of-type(1)")
                        if td_name == "加入日期":
                            user.create_time = HttpUtils.get_content(tr, "td:nth-of-type(2)").replace(" (", "")
                        elif td_name == "最近動向":
                            user.last_time = HttpUtils.get_content(tr, "td:nth-of-type(2)").replace(" (", "")
                        elif td_name == "傳送":
                            user.ratio = HttpUtils.get_content(tr, "td:nth-of-type(2) table tr td font")
                            if user.ratio is None:
                                # seems that no download is made and ratio is infinite
                                user.ratio = -1
                                user.up = self.parse_size_in_gb(
                                    HttpUtils.get_content(tr,
                                                          "td:nth-of-type(2) table tr:nth-of-type(1) td:nth-of-type(1)",
                                                          1))
                                user.down = self.parse_size_in_gb(
                                    HttpUtils.get_content(tr,
                                                          "td:nth-of-type(2) table tr:nth-of-type(1) td:nth-of-type(2)",
                                                          2))
                            else:
                                user.up = self.parse_size_in_gb(
                                    HttpUtils.get_content(tr,
                                                          "td:nth-of-type(2) table tr:nth-of-type(2) td:nth-of-type(1)",
                                                          1))
                                user.down = self.parse_size_in_gb(
                                    HttpUtils.get_content(tr,
                                                          "td:nth-of-type(2) table tr:nth-of-type(2) td:nth-of-type(2)",
                                                          2))
                        elif td_name == "魔力值":
                            user.mp = HttpUtils.get_content(tr, "td:nth-of-type(2)")

                    # parse rank
                    user.rank = "secret"
                    imgs = soup_obj.select("table.main table tr > td > img[title!='']")
                    for img in imgs:
                        if not img.has_attr("class"):
                            user.rank = img["title"]

                            # if "Peasant" in user.rank:
                            #     print("###### find user=" + user.name + " id=" + str(i) + " rank=" + user.rank)
                    print("###### find user=" + user.name + " id=" + str(i) + " rank=" + user.rank)
            except Exception as e:
                print(str(i) + "\n" + str(e) + "\n")

            # print(str(user))
            self.buffer.append(user)
        except Exception as e:
            print(">>>>> fail to parse " + str(i))
            self.errors.append(i)

    def parse_size_in_gb(self, sizeStr):
        assert sizeStr is not None
        if str.endswith(sizeStr, "TB"):
            return float(sizeStr.replace(" TB", "").replace(": ", "")) * 1024
        if str.endswith(sizeStr, "GB"):
            return float(sizeStr.replace(" GB", "").replace(": ", ""))
        elif str.endswith(sizeStr, "MB"):
            return 0.001
        elif str.endswith(sizeStr, "KB"):
            return 0.001
        else:
            return -1

    def write(self):
        if len(self.buffer) == 0:
            return

        print("########### start writing ###########")
        with open("user.txt", "a") as f:
            for data in self.buffer:
                f.write(str(data) + "\r")
        print("########### finish writing ###########")
        self.buffer.clear()

    def crawl(self, ids=None):
        site = self.generate_site()
        assert self.login(site)

        if ids is None:
            start = 0
            end = 200000
            step = 2000

            current = start
            while current < end:
                ParallelTemplate(500).run(func=self.single, inputs=range(current, current + step))
                current += step

                if len(self.errors) > 0:
                    print(">>>>>>>>>>>>>>>>> retry >>>>>>>>>>>>>>>>>>>>>>")
                    ParallelTemplate(100).run(func=self.single, inputs=self.errors)
                    self.errors.clear()
                    print(">>>>>>>>>>>>>>>>> retry finished >>>>>>>>>>>>>>>>>>>>>>")

                if len(self.buffer) > 300:
                    self.write()
            self.write()
        else:
            start = 0
            end = len(ids)
            step = 2000

            current = start
            while current < end:
                ParallelTemplate(500).run(func=self.single, inputs=ids[current: min(current + step, end)])
                current += step

                if len(self.errors) > 0:
                    print(">>>>>>>>>>>>>>>>> retry >>>>>>>>>>>>>>>>>>>>>>")
                    ParallelTemplate(100).run(func=self.single, inputs=self.errors)
                    self.errors.clear()
                    print(">>>>>>>>>>>>>>>>> retry finished >>>>>>>>>>>>>>>>>>>>>>")

                if len(self.buffer) > 300:
                    self.write()
            self.write()

    def refresh(self):
        userIds = []
        with open("user_origin.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                user = User.parse(line)
                userIds.append(user.id)
        self.crawl(userIds)

    def filter(self):
        users = []
        with open("user.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                user = User.parse(line)
                if user.is_ban or user.is_secret or "VIP" in user.rank or "職人" in user.rank:
                    continue
                if user.ratio < 0.8 and user.ratio > 0:
                    if "Peasant" in user.rank:
                        if user.ratio < 0.5:
                            print(">>>>>>>>>> " + str(user))
                        else:
                            print("**********" + str(user))


if __name__ == "__main__":
    # if len(sys.argv) >= 2:
    #     target = sys.argv[1]
    #     if target == "feed_check":
    #         FreeFeedAlert().check()
    #     elif target == "mp_check":
    #         MagicPointChecker().check()
    #     elif target == "mp_monitor":
    #         MagicPointChecker().monitor()

    # NormalAlert().check()
    # AdultAlert().check()
    # UserCrawl().crawl()
    UserCrawl().refresh()
    # UserCrawl().filter()
    # MagicPointChecker().check()
    # Exchanger().exchange_mp()
    # UploadMonitor().crawl()
