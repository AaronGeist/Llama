# -*- coding:utf-8 -*-
import json
import re
import os
from concurrent.futures import ThreadPoolExecutor

from core.db import Cache
from core.emailSender import EmailSender
from core.login import Login
from core.monitor import Monitor
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

        soup_obj = HttpUtils.get(site.home_page)
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
        # strategies:
        # 1. free seed
        # 2. hasn't been found before
        filtered_seeds = list(filter(lambda x: x.free and Cache().get(x.id) is None, data))
        for seed in filtered_seeds:
            # keep in cache for 2 days
            Cache().set_with_expire(seed.id, str(seed), 172800)

        return filtered_seeds

    def action(self, data):
        if len(data) == 0:
            return

        # send email
        msg = ""
        for seed in data:
            msg += str(seed)

        EmailSender.send(u"种子", msg)

        # check current disk space
        space = float(os.popen("df -lm|grep vda1|awk '{print $4}'").read())

        # check vps bankwidth
        resp = os.popen("curl -H 'API-Key: %s' https://api.vultr.com/v1/server/list" % Config.get("vultr_api_key")).read()
        jsonData = json.loads(resp)
        info_dict = list(jsonData.values())[0]
        current_bandwidth_gb = info_dict['current_bandwidth_gb']
        allowed_bandwidth_gb = info_dict['allowed_bandwidth_gb']

        print("space=%s,current_bw=%s,allowed_bw=%s", (str(space), str(current_bandwidth_gb), str(allowed_bandwidth_gb)))

        # download if still enough space
        for seed in data:
            if seed.size <= 10000:
                space -= seed.size
                current_bandwidth_gb += seed.size/1024
                if space <= 0 or current_bandwidth_gb >= allowed_bandwidth_gb:
                    break
                HttpUtils.download_file("https://pt.sjtu.edu.cn/download.php?id=%s" % seed.id,
                                        "%s.torrent" % seed.id)
                print("remaining %s" % str(space))
                os.popen("transmission-remote -a %s.torrent && rm %s.torrent" % (seed.id, seed.id))

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

    # FreeFeedAlert().check()
    # MagicPointChecker().check()
    # Exchanger().exchange_mp()
    UploadMonitor().crawl()
