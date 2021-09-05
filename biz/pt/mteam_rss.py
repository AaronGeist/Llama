# -*- coding:utf-8 -*-

import re

from biz.pt.baseuploader import BaseUploader
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class MT_RSS(BaseUploader):


    def get_site_name(self):
        return "mteam"

    def generate_site(self):
        self.passKey = Config.get("mteam_passkey")

        site = Site()
        site.home_page = "https://kp.m-team.cc/torrentrss.php?https=1&rows=50&cat410=1&cat429=1&cat424=1&cat430=1&cat426=1&cat437=1&cat431=1&cat432=1&cat436=1&cat425=1&cat433=1&cat411=1&cat412=1&cat413=1&cat440=1&isize=1&passkey=" + self.passKey
        site.login_needed = False
        site.login_headers = {
            "user-agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
            "upgrade-insecure-requests": "1",
        }
        self.site = site

    def parse_page(self, soup_obj):
        items = soup_obj.select("item")
        assert len(items) != 0

        seeds = []
        for item in items:
            try:
                info = HttpUtils.get_content(item, "title").split("[")

                seed = SeedInfo()

                seed.title = info[0].strip()
                seed.size = HttpUtils.pretty_format(info[1].split("]")[0], "MB")
                seed.url = HttpUtils.get_content(item, "link")
                seed.id = self.parse_id(seed.url)

                seeds.append(seed)
            except Exception as e:
                pass

        return seeds

    @staticmethod
    def parse_id(url):
        m = re.search("id=(\w+)", url)
        assert m is not None
        return m.group(1)

    def easy_strategy(self, data):
        group_name = ["wiki", "ttg", "ngb", "npuer", "avs", "dimension"]

        filtered_seeds = list(
            filter(lambda seed: len(list(filter(lambda name: "-" + name in seed.title.lower(), group_name))), data))

        filtered_seeds = list(
            filter(lambda seed: seed.id <= "509337", data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        return filtered_seeds

    def sort_seed(self, seeds):
        # sort seed by id, descend
        seeds.sort(key=lambda x: x.id, reverse=True)

        for seed in seeds:
            print(seed.id)

        return seeds

    def download_seed_file(self, seed_id):

        res = HttpUtils.get(
            "https://kp.m-team.cc/download.php?id=%s&passkey=%s&https=1" % (seed_id, self.passKey),
            headers=self.site.login_headers,
            return_raw=True)

        try:
            with open("%s.torrent" % seed_id, "wb") as f:
                f.write(res.content)
        except Exception as e:
            print("Cannot download seed file: " + seed_id, e)


if __name__ == "__main__":
    MT_RSS().check()
