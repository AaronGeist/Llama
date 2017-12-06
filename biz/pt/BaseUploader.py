# -*- coding:utf-8 -*-
import abc
import re
import time

from core.db import Cache
from core.login import Login
from core.seedManager import SeedManager
from util.config import Config
from util.utils import HttpUtils


class BaseUploader(Login):
    site = None
    size_factor = 1  # the shown size on web page is not accurate
    is_login = False
    ttl = 60 * 86400

    @abc.abstractmethod
    def get_site_name(self):
        return ""

    def login_if_not(self):
        if not self.is_login:
            self.generate_site()
            self.is_login = self.login(self.site)
            assert self.is_login

    @abc.abstractmethod
    def generate_site(self):
        pass

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password

        return data

    def crawl(self, print_log=True):
        self.login_if_not()

        soup_obj = HttpUtils.get(self.site.home_page, headers=self.site.login_headers)
        assert soup_obj is not None
        data = self.parse_page(soup_obj)

        if print_log:
            if type(data) is list:
                for item in data:
                    print(item)
            else:
                print(data)

        return data

    @abc.abstractmethod
    def parse_page(self, soup_obj):
        return list()

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

        # choose customized strategy
        strategy_map = {"easy": self.easy_strategy, "medium": self.medium_strategy, "hard": self.hard_strategy,
                        "hell": self.hell_strategy}
        strategy = strategy_map[Config.get(self.get_site_name() + "_strategy")]
        assert strategy is not None

        # execute customized strategy
        final_seeds = strategy(data)

        # white list
        white_lists = Config.get(self.get_site_name() + "_white_list").split("|")
        for seed in data:
            for white_list in white_lists:
                if re.search(white_list, seed.title):
                    final_seeds.append(seed)
                    break

        for seed in final_seeds:
            print("Find valuable seed: " + str(seed))

        return final_seeds

    def sort_seed(self, seeds):
        # sort seed, sticky and free seed has highest weight, the less discount,
        # the more download, the less upload, the less size, the better
        for x in seeds:
            print("score=" + str(int(x.sticky) * 50 + int(x.free) * 50 + round(
                (100000 / (x.discount + 10)) * x.download_num / (x.upload_num + 0.01) / (x.size + 5000),
                3)) + "  >>>> " + str(
                x))

        seeds.sort(key=lambda x: int(x.sticky) * 50 + int(x.free) * 50 + round(
            (100000 / (x.discount + 10)) * x.download_num / (x.upload_num + 0.01) / (x.size + 5000), 3), reverse=True)

        return seeds

    # do not add too many seed at one time
    def limit_total_size(self, seeds, limit):
        size_cnt = 0
        filtered_seeds = []
        for seed in seeds:
            if seed.size > limit:
                continue
            size_cnt += seed.size
            if size_cnt < limit:
                filtered_seeds.append(seed)

        return filtered_seeds

    def easy_strategy(self, data):
        filtered_seeds = list(filter(
            lambda x: (x.upload_num != 0 and round(x.download_num / x.upload_num, 1) >= 1.5) and
                      (x.free or x.sticky or (
                          x.discount <= 50 and round(x.download_num / x.upload_num) >= 2) or (
                           x.discount > 50 and round(x.download_num / x.upload_num) >= 3 and x.upload_num <= 10)),
            data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        final_seeds = self.limit_total_size(filtered_seeds, 12 * 1024)

        return final_seeds

    def medium_strategy(self, data):
        filtered_seeds = list(filter(
            lambda x: (x.upload_num != 0 and round(x.download_num / x.upload_num, 1) >= 2) and
                      (x.free or (x.sticky and x.discount <= 50) or (
                          x.discount <= 50 and round(x.download_num / x.upload_num) >= 2) or ((
                          x.discount > 50 and round(x.download_num / x.upload_num) >= 3 and x.upload_num <= 10))),
            data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        # only limited number of no discount seed is allowed
        not_free_limit = 1
        not_free_cnt = 0
        filtered_seeds_lvl2 = []
        for seed in filtered_seeds:
            if not seed.free and not seed.sticky and seed.discount > 50 and not_free_cnt < not_free_limit:
                filtered_seeds_lvl2.append(seed)
            elif seed.free or seed.sticky or seed.discount <= 50:
                filtered_seeds_lvl2.append(seed)

        final_seeds = self.limit_total_size(filtered_seeds_lvl2, 10 * 1024)

        return final_seeds

    def hard_strategy(self, data):
        filtered_seeds = list(filter(
            lambda x: (x.upload_num != 0 and round(x.download_num / x.upload_num, 1) >= 3) and
                      (x.free or (x.sticky and x.discount <= 50) or (
                          x.discount <= 50 and round(x.download_num / x.upload_num) >= 5)),
            data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        final_seeds = self.limit_total_size(filtered_seeds, 9 * 1024)

        return final_seeds

    def hell_strategy(self, data):
        filtered_seeds = list(filter(
            lambda x: (x.upload_num != 0 and round(x.download_num / x.upload_num, 1) >= 3) and
                      x.free,
            data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        final_seeds = self.limit_total_size(filtered_seeds, 9 * 1024)

        return final_seeds

    @abc.abstractmethod
    def download_seed_file(self, seed_id):
        pass

    def action(self, candidate_seeds):
        if len(candidate_seeds) == 0:
            return

        for seed in candidate_seeds:
            self.download_seed_file(seed.id)

        success_seeds, fail_seeds = SeedManager.try_add_seeds(candidate_seeds)

        for success_seed in success_seeds:
            Cache().set_with_expire(success_seed.id, str(success_seed), self.ttl)

        # make the failed seed cool down for some time
        for fail_seed in fail_seeds:
            cool_down_time = 3600  # 1 hour
            if fail_seed.free or fail_seed.sticky:
                cool_down_time = 300  # 5 minutes
            elif fail_seed.discount <= 50:
                cool_down_time = 1800  # 30 minutes

            Cache().set_with_expire(fail_seed.id, str(fail_seed), cool_down_time)

    def check(self):
        self.action(self.filter(self.crawl(False)))

    def manual_add_seed(self, seed_id):
        self.login_if_not()

        self.download_seed_file(seed_id)
        seeds = list(filter(lambda x: x.id == seed_id, self.crawl(False)))
        assert len(seeds) == 1

        SeedManager.try_add_seeds(seeds)
        Cache().set_with_expire(seeds[0].id, str(seeds[0]), self.ttl)

    def ignore(self, seed_id=None):
        if seed_id is None:
            # ignore all seeds @ home page
            seeds = self.crawl()

            # skip if already in cache
            seeds = list(filter(lambda x: Cache().get(x.id) is None, seeds))

            for seed in seeds:
                print("Ignore seed: " + str(seed))
                Cache().set_with_expire(seed.id, str(seed), self.ttl)
        else:
            print("Ignore seed ID: " + str(seed_id))
            Cache().set_with_expire(seed_id, "", self.ttl)

    def stat(self, unit="GB", update_cache=True):
        self.login_if_not()

        soup_obj = HttpUtils.get(self.site.stat_page, headers=self.site.login_headers)
        assert soup_obj is not None

        div_list = soup_obj.select("table.mainouter tr td table tr td div[align='center']")
        assert len(div_list) == 1

        content = div_list[0].contents[0]
        m = re.search(u"获取(\d+.\d+)个魔力", content)
        assert m
        mp = float(m.group(1))

        span_list = soup_obj.select("#usermsglink span")
        up = HttpUtils.pretty_format(span_list[1].contents[2], unit)
        down = HttpUtils.pretty_format(span_list[1].contents[4], unit)

        prev_up = Cache().get(self.get_site_name() + "_up")
        prev_down = Cache().get(self.get_site_name() + "_down")

        if prev_up is None:
            prev_up = 0
        else:
            prev_up = float(prev_up.decode())

        if prev_down is None:
            prev_down = 0
        else:
            prev_down = float(prev_down.decode())

        delta_up = round(up - prev_up, 2)
        delta_down = round(down - prev_down, 2)
        if delta_down == 0:
            delta_ratio = "Inf"
        else:
            delta_ratio = round(delta_up / delta_down, 2)

        current_upload = round(up - down, 2)
        print("%s, mp=%s, up=%s, down=%s, current=%s, delta_up=%s, delta_down=%s, delta_ratio=%s" % (
            str(time.strftime("%Y-%m-%d %H:%M:%S")), mp, up, down, current_upload, delta_up, delta_down, delta_ratio))

        if update_cache:
            Cache().set(self.get_site_name() + "_up", up)
            Cache().set(self.get_site_name() + "_down", down)

        return mp, up, down
