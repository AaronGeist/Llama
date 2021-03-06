# -*- coding:utf-8 -*-
import re
from concurrent.futures import ThreadPoolExecutor

from biz.ocr.putao import PuTaoCaptchaParser
from core.cache import Cache
from core.emailsender import EmailSender
from core.enigma import Enigma
from core.login import Login
from core.monitor import Monitor
from core.seedmanager import SeedManager
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class FreeFeedAlert(Login):
    def generate_site(self):
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
        site.login_password = Enigma.decrypt(Config.get("putao_password"))

        return site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password
        data['checkcode'] = site.check_code
        return data

    def crawl(self):
        site = self.generate_site()
        assert self.login(site)

        soup_obj = HttpUtils.get(site.home_page)
        return self.parse(soup_obj)

    def login(self, site):
        if not self.isLogin and site.login_needed and not self.check_login(site):

            soup_obj = HttpUtils.get("https://pt.sjtu.edu.cn/login.php", headers=site.login_headers)

            # parse captcha image and return result
            image_url = "https://pt.sjtu.edu.cn/" + soup_obj.select("form img")[0]["src"]
            HttpUtils.download_file(image_url, "/tmp/cap.png", over_write=True)
            site.check_code = PuTaoCaptchaParser.analyze("/tmp/cap.png")

            resp = HttpUtils.post(site.login_page, data=self.build_post_data(site),
                                  headers=site.login_headers, returnRaw=True)

            self.isLogin = self.check_login(site)
            return self.isLogin
        else:
            self.isLogin = True
            return True

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


class MagicPointChecker(FreeFeedAlert, Monitor):
    def get_bucket(self):
        return "putao_mp"

    def generate_site(self):
        site = super().generate_site()
        site.home_page = "https://pt.sjtu.edu.cn/mybonus.php"
        return site

    def parse(self, soup_obj):
        assert soup_obj is not None

        div_list = soup_obj.select("table.mainouter tr td table tr td div[align='center']")
        assert len(div_list) == 1

        content = div_list[0].contents[0]
        m = re.search(u"获取(\d+.\d+)个魔力", content)
        assert m
        return float(m.group(1))

    def alert(self, data):
        threshold = Config.get("putao_mp_threshold")
        if data <= threshold:
            EmailSender.send("魔力值警告: %s <= %s" % (str(data), threshold), "")

    def generate_data(self):
        return self.crawl()


class UploadMonitor(MagicPointChecker):
    def get_bucket(self):
        return "putao_upload"

    def parse(self, soup_obj):
        assert soup_obj is not None

        span_list = soup_obj.select("#usermsglink span")
        return span_list[1].contents[2].replace("TB", "").strip()


class Exchanger(FreeFeedAlert):
    def generate_site(self):
        site = super().generate_site()
        site.home_page = "https://pt.sjtu.edu.cn/mybonus.php"
        return site

    def exchange_mp(self, times=1):
        site = self.generate_site()
        assert self.login(site)

        data = dict()
        data['option'] = 3  # 1=1GB 2=5GB 3=10GB
        data['art'] = "traffic"

        with ThreadPoolExecutor(max_workers=times) as executor:
            {executor.submit(HttpUtils.post("https://pt.sjtu.edu.cn/mybonus.php?action=exchange", data=data,
                                            headers=site.login_headers, returnRaw=True)): item for item in
             range(1, times + 1)}


if __name__ == "__main__":
    # if len(sys.argv) >= 2:
    #     target = sys.argv[1]
    #     if target == "feed_check":
    #         FreeFeedAlert().check()
    #     elif target == "mp_check":
    #         MagicPointChecker().check()
    #     elif target == "mp_monitor":
    #         MagicPointChecker().monitor()

    FreeFeedAlert().check()
    # MagicPointChecker().check()
    # Exchanger().exchange_mp()
    # UploadMonitor().crawl()
