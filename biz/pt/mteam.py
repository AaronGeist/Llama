# -*- coding:utf-8 -*-
import random
import re

import time
from datetime import datetime

from core.cache import Cache
from core.emailsender import EmailSender
from core.login import Login
from core.seedmanager import SeedManager
from model.message import Message
from model.ptuser import User
from model.seed import SeedInfo
from model.site import Site
from util.parallel_template import ParallelTemplate
from util.config import Config
from util.utils import HttpUtils


class NormalAlert(Login):
    site = Site()
    size_factor = 1.074  # the shown size on web page is not accurate
    is_login = False

    download_link = "https://kp.m-team.cc/download.php?id=%s&https=1"

    def __init__(self):
        self.site.home_page = "https://kp.m-team.cc/torrents.php"
        self.site.login_page = "https://kp.m-team.cc/takelogin.php"
        self.site.login_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
            "cookie": "c_lang_folder=cht; tp=ZTNiZTE4ZDYwYmZiOTI1ZjQzNGRmMDhlOTY4NTJmODExZjYwODIxZQ%3D%3D; cf_chl_prog=a9; cf_clearance=IMq1zdVD.N7tjymYWcRihWCPKFdgOpx65I4YP.VXmcI-1630648319-0-150",
            "dnt": "1",
            "referer": "https://kp.m-team.cc/index.php",
            "sec-ch-ua": "\"Google Chrome\";v=\"93\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"93\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
        }

        self.site.login_needed = True
        self.site.login_verify_css_selector = "#info_block span.nowrap a b"
        self.site.login_verify_str = Config.get("mteam_username")
        self.site.login_username = Config.get("mteam_username")
        self.site.login_password = Config.get("mteam_password")

    def login_if_not(self):
        if not self.is_login:
            self.generate_site()
            self.is_login = self.login(self.site)
            assert self.is_login

    def generate_site(self):
        return self.site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password

        return data

    def crawl(self, print_log=True):
        self.login_if_not()

        soup_obj = HttpUtils.get(self.site.home_page, headers=self.site.login_headers)
        seeds = self.parse(soup_obj)

        if print_log:
            for seed in seeds:
                print(seed)

        return seeds

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
            seed.done = self.clean_tag(td_list[7])
            seed.working = "peer-active" in td_list[7]['class']

            td_title = tr.select("td.torrenttr tr td")
            seed.sticky = len(td_title[0].select("img[alt=\"Sticky\"]"))
            seed.title = td_title[0].select("a")[0]["title"]
            seed.url = td_title[0].select("a")[0]['href']
            seed.free = len(td_title[0].select("img[alt=\"Free\"]")) > 0
            seed.hot = len(td_title[0].select("font.hot")) > 0
            if len(td_title[0].select("img[alt=\"50%\"]")) > 0:
                seed.discount = 50
            elif len(td_title[0].select("img[alt=\"30%\"]")) > 0:
                seed.discount = 30
            elif seed.free:
                seed.discount = 0
            else:
                seed.discount = 100
            seed.id = self.parse_id(seed.url)

            seeds.append(seed)

        print("Crawl: " + str(len(seeds)))
        if len(seeds) < 10:
            EmailSender.send(u"无法解析页面", Config.get("mteam_username"))

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
        final_seeds = []
        if Config.get("mteam_strategy") == "easy":
            final_seeds = self.easy_strategy(data)
        elif Config.get("mteam_strategy") == "medium":
            final_seeds = self.medium_strategy(data)
        elif Config.get("mteam_strategy") == "hard":
            final_seeds = self.hard_strategy(data)

        # white list
        white_lists = Config.get("putao_white_list").split("|")
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

    # general download way for both normal user and warned user
    def download_seed_file(self, seed_id):
        self.login_if_not()

        data = {
            "id": seed_id,
            "type": "ratio",
            "hidenotice": "1",
            "letmedown": "ratio"
        }
        res = HttpUtils.post("https://kp.m-team.cc/downloadnotice.php?", data=data, headers=self.site.login_headers,
                             returnRaw=True)
        try:
            with open("%s.torrent" % seed_id, "wb") as f:
                f.write(res.content)
        except Exception as e:
            print("Cannot download seed file: " + seed_id, e)

    def action(self, candidate_seeds):
        if len(candidate_seeds) == 0:
            return

        for seed in candidate_seeds:
            self.download_seed_file(seed.id)

        success_seeds, fail_seeds = SeedManager.try_add_seeds(candidate_seeds)

        for success_seed in success_seeds:
            Cache().set_with_expire(success_seed.id, str(success_seed), 5 * 864000)

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

    def init(self):
        # enable adult torrent and close pic
        self.init_setting()

        # # crawl and add to cache
        # seeds = self.crawl()
        #
        # # common strategy
        # # 1. hasn't been found before
        # # 2. not exceed max size
        # max_size = Config.get("seed_max_size_mb")
        # seeds = list(filter(lambda x: x.size < max_size and Cache().get(x.id) is None, seeds))
        #
        # for seed in seeds:
        #     print("Add seed: " + str(seed))
        #     Cache().set_with_expire(seed.id, str(seed), 5 * 864000)

    def add_seed(self, seed_id):
        self.login_if_not()

        self.download_seed_file(seed_id)
        seeds = list(filter(lambda x: x.id == seed_id, self.crawl(False)))
        assert len(seeds) == 1

        SeedManager.try_add_seeds(seeds)
        Cache().set_with_expire(seeds[0].id, str(seeds[0]), 5 * 864000)

    def init_setting(self):
        self.login_if_not()

        # enable adult torrent
        setting_url = "https://kp.m-team.cc/usercp.php"
        lab_data = {
            "action": "laboratory",
            "type": "save",
            "laboratory_adult_mode": "0",
            "laboratory_torrent_page_https": "0"
        }
        res = HttpUtils.post(url=setting_url, data=lab_data, headers=self.site.login_headers, returnRaw=True)
        assert res.status_code == 200

        # do not show picture
        tracker_data = {
            "action": "tracker",
            "type": "save",
            "t_look": "1",  # show pic
            "tooltip": "off",
            "timetype": "timealive",
            "appendsticky": "yes",
            "radio": "icon",
            "smalldescr": "yes",
            "dlicon": "yes",
            "bmicon": "yes",
            "show_hot": "yes",
            "showfb": "yes",
            "showdescription": "yes",
            "showimdb": "yes",
            "showcomment": "yes",
            "appendnew": "yes",
            "appendpicked": "yes",
            "showcomnum": "yes"
        }
        res = HttpUtils.post(url=setting_url, data=tracker_data, headers=self.site.login_headers, returnRaw=True)
        assert res.status_code == 200


class AdultAlert(NormalAlert):
    def generate_site(self):
        self.site.home_page = "https://kp.m-team.cc/adult.php"
        return self.site


class UploadCheck(AdultAlert):
    cache = Cache()

    is_store = True

    def parse(self, soup_obj):
        assert soup_obj is not None

        info_block = soup_obj.select("#info_block table tr td:nth-of-type(1) span")[0]

        prev_info = ""
        upload = 0
        download = 0
        for info in info_block.contents:
            if "上傳量" in prev_info:
                upload = HttpUtils.pretty_format(info, "GB")
            elif "下載量" in prev_info:
                download = HttpUtils.pretty_format(info, "GB")
                break
            prev_info = str(info)

        return upload, download

    def filter(self, data):
        return data

    def action(self, data):
        prev_up = self.cache.get("mt_up")
        prev_down = self.cache.get("mt_down")

        if prev_up is None:
            prev_up = 0
        else:
            prev_up = float(prev_up.decode())
        if prev_down is None:
            prev_down = 0
        else:
            prev_down = float(prev_down.decode())

        delta_up = round(data[0] - prev_up, 2)
        delta_down = round(data[1] - prev_down, 2)
        if delta_down == 0:
            delta_ratio = "Inf"
        else:
            delta_ratio = round(delta_up / delta_down, 2)

        upload_target = Config.get("mteam_upload_target")
        current_upload = round(data[0] - data[1], 2)
        print(
                "%s, upload=%s, download=%s, current=%s, delta_up=%s, delta_down=%s, delta_ratio=%s, target=%s" % (
            str(time.strftime("%Y-%m-%d %H:%M:%S")),
            data[0], data[1],
            current_upload, delta_up, delta_down, delta_ratio,
            upload_target))

        if self.is_store:
            self.cache.set("mt_up", data[0])
            self.cache.set("mt_down", data[1])

        if upload_target < current_upload:
            for i in range(5):
                EmailSender.send(u"完成上传", Config.get("mteam_username"))
                time.sleep(10000)

    def init(self):
        self.cache.set("mt_up", 0)
        self.cache.set("mt_down", 0)

    def check_not_store(self):
        # backup current configuration
        is_store = self.is_store
        self.is_store = False
        self.check()
        self.is_store = is_store


class CandidateVote(NormalAlert):
    def generate_site(self):
        self.site.home_page = "https://kp.m-team.cc/offers.php"
        return self.site

    def parse(self, soup_obj):
        assert soup_obj is not None

        id_set = set()
        vote_list = soup_obj.select("#form_torrent table tr td.rowfollow b a")
        for vote_obj in vote_list:
            id_set.add(self.parse_id(vote_obj['href']))

        return id_set

    def filter(self, data):
        return data

    def action(self, data):
        vote_url = "https://kp.m-team.cc/vote.php?tid=%s&type=1"
        success_cnt = 0
        for id in data:
            res_obj = HttpUtils.get(url=vote_url % id, headers=self.site.login_headers)
            msg = HttpUtils.get_content(res_obj, "#outer table h2")
            if msg == "操作成功":
                success_cnt += 1

        print("Vote success: " + str(success_cnt))


class UserCrawl(NormalAlert):
    buffer = []
    errors = []

    id_bucket_name = "mteam_user_id"
    name_bucket_name = "mteam_user_name"
    msg_bucket_name = "mteam_msg"

    min_id = 1
    max_id = 200000
    scan_batch_size = 500
    skip_if_exist = False  # ignore cache and re-crawl all user

    cache = Cache()

    msg_subject = "分享率过低的账户会被警告并封禁，请注意（%s)"
    msg_body = "如需快速增加上传，消除警告，请微信联系 helloword1984（用户名是薛定谔的小仓鼠）\n\n注1：本人非网站工作人员\n注2：如果打扰到了您，表示抱歉，请pm回复'谢谢勿扰'"

    msg_urgent_subject = "注意！注意！注意！分享率低于0.3的账户可能随时会被封号！"
    msg_urgent_body = "如需快速增加上传，消除警告，请微信联系 helloword1984（用户名是薛定谔的小仓鼠）\n\n注1：本人非网站工作人员\n注2：如果打扰到了您，表示抱歉，请pm回复'谢谢勿扰'"

    def generate_site(self):
        self.site.home_page = "https://kp.m-team.cc/userdetails.php?id=%s"
        return self.site

    def crawl_single(self, user_id):

        if self.skip_if_exist and self.cache.hash_get(self.id_bucket_name, user_id) is not None:
            print("Skip " + str(user_id))
            return

        try:
            url = self.site.home_page % str(user_id)
            soup_obj = HttpUtils.get(url, headers=self.site.login_headers, return_raw=False)
            assert soup_obj is not None

            user = User()
            user.id = user_id
            user.name = HttpUtils.get_content(soup_obj, "#outer h1 span b")

            if user.name is None:
                return

            user.is_warn = len(soup_obj.select("#outer h1 span img[alt='Leechwarned']")) > 0
            user.is_ban = len(soup_obj.select("#outer h1 span img[alt='Disabled']")) > 0
            if user.is_warn:
                user.warn_time = str(time.strftime("%Y-%m-%d %H:%M:%S"))

            try:
                if len(soup_obj.select("#outer table tr")) <= 5:
                    user.is_secret = True
                    # print("secret user: name={0} id={1}".format(user.name, str(user_id)))
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
                                user.ratio = user.ratio.replace(",", "")
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

                            if "Peasant" in user.rank:
                                user.warn_time = str(time.strftime("%Y-%m-%d %H:%M:%S"))
                                # print("###### find user=" + user.name + " id=" + str(user_id) + " rank=" + user.rank)
            except Exception as e:
                print(str(user_id) + "\n" + str(e) + "\n")

            self.buffer.append(user)
        except Exception as e:
            print(">>>>> fail to parse " + str(user_id))
            self.errors.append(user_id)

    def parse_size_in_gb(self, size_str):
        assert size_str is not None
        return HttpUtils.pretty_format(size_str.replace(": ", ""), "GB")

    def store_cache(self, data):
        if data is None or len(data) == 0:
            return

        for user in data:
            res = self.cache.hash_get(self.id_bucket_name, user.id)
            if res is not None:
                exist_user = User.parse(res.decode())
                # warned before, do not update warn time
                if user.is_warn and exist_user.is_warn:
                    user.warn_time = exist_user.warn_time

            self.cache.hash_set(self.id_bucket_name, user.id, str(user))
            self.cache.hash_set(self.name_bucket_name, user.name, str(user))

        print("########### finish storing cache ###########")

    def crawl(self, ids=None):
        self.login_if_not()

        if ids is None:
            ids = range(self.min_id, self.max_id)
            self.skip_if_exist = True

        start = 0
        end = len(ids)
        step = self.scan_batch_size

        current = start
        while current < end:
            print(">>>>>>>>>>>> crawl {0} -> {1} >>>>>>>>>>>>>>>>".format(ids[current],
                                                                          ids[min(current + step, end - 1)]))
            ParallelTemplate(500).run(func=self.crawl_single, inputs=ids[current: min(current + step, end)])
            current += step + 1

            if len(self.errors) > 0:
                print(">>>>>>>>>>>>>>>>> retry >>>>>>>>>>>>>>>>>>>>>>")
                ParallelTemplate(100).run(func=self.crawl_single, inputs=self.errors)
                self.errors.clear()
                print(">>>>>>>>>>>>>>>>> retry finished >>>>>>>>>>>>>>>>>>>>>>")

            if len(self.buffer) > 300:
                self.store_cache(self.buffer)
                self.buffer.clear()

        # write all others left
        self.store_cache(self.buffer)
        self.buffer.clear()

    def refresh(self):
        ids = list(sorted(map(lambda x: int(x.decode()), self.cache.hash_get_all_key(self.id_bucket_name))))
        print("max ID=" + str(ids[-1]))
        self.min_id = ids[-1] + 1
        self.max_id = self.min_id + 1000

        print("\n############## refresh user ##############\n")
        # refresh existing user
        self.crawl(ids)

        print("\n############## crawl new user ##############\n")
        # find new user
        self.crawl()

    def warn(self):
        self.refresh()
        warn_white_list = str(Config.get("mt_warn_white_list")).split("|")

        user_ids = self.cache.hash_get_all_key(self.id_bucket_name)
        now = datetime.now()
        for user_id in user_ids:
            user_str = self.cache.hash_get(self.id_bucket_name, user_id).decode()
            user = User.parse(user_str)
            if user.is_ban or not user.is_warn or "VIP" in user.rank or "職人" in user.rank:
                continue
            if user.is_secret or (0.5 > user.ratio > -1 or (0.9 > user.ratio and user.down - user.up > 50)):
                if user.create_time == "":
                    create_since = 999999
                else:
                    create_time = datetime.strptime(user.create_time, "%Y-%m-%d %H:%M:%S")
                    create_since = (now - create_time).days
                warn_time = datetime.strptime(user.warn_time, "%Y-%m-%d %H:%M:%S")
                warn_since = (now - warn_time).days
                print("{0}|{1}|{2}".format(str(user), str(create_since), str(warn_since)))

                # new user and ratio lower than 0.3 will be baned any time
                if create_since < 30 and user.ratio < 0.3 and warn_since in [0, 1]:
                    self.send_msg(user.id, self.msg_urgent_subject, self.msg_urgent_body)
                    continue

                # skip user who has registered for less than 2 days
                if create_since < 2:
                    continue

                if user.name in warn_white_list:
                    continue

                if warn_since in [0, 3, 5]:
                    self.send_msg(user.id, self.msg_subject % (7 - warn_since), self.msg_body)

    def order(self, limit=250):
        user_ids = self.cache.hash_get_all_key(self.id_bucket_name)
        users = []
        for user_id in user_ids:
            user_str = self.cache.hash_get(self.id_bucket_name, user_id).decode()
            user = User.parse(user_str)
            if not user.is_secret and not user.is_ban and user.ratio >= 0 and user.down >= 10 and "VIP" not in user.rank and "職人" not in user.rank:
                users.append(user)

        users.sort(key=lambda x: x.ratio)
        for i in range(0, int(limit)):
            print(users[i])

    def load_by_id(self, user_id):
        res = self.cache.hash_get(self.id_bucket_name, user_id)
        if res is not None:
            print(res.decode())
        else:
            print("Cannot find user by ID: " + user_id)

    def load_by_name(self, user_name):
        res = self.cache.hash_get(self.name_bucket_name, user_name)
        if res is not None:
            print(res.decode())
        else:
            print("Cannot find user by name: " + user_name)

    def send_msg(self, user_id, subject, body):
        if self.cache.get(self.msg_bucket_name + str(user_id)) is not None:
            print("Skip sending msg, user in cache: " + str(user_id))
            return

        self.login_if_not()

        url = "https://kp.m-team.cc/takemessage.php"
        data = {
            "receiver": user_id,
            "subject": subject,
            "body": body,
            "save": "yes"
        }

        HttpUtils.post(url=url, data=data, headers=self.site.login_headers)
        print(">>>>>>>>> Send msg to {0}, subject={1}, body={2} >>>>>>>>>>".format(user_id, subject, body))

        self.cache.set_with_expire(self.msg_bucket_name + str(user_id), "", 86400)

        # sleep 30 ~ 120 seconds before sending next message
        time.sleep(round(30 + random.random() * 90))


class MessageReader(NormalAlert):
    url = "https://kp.m-team.cc/messages.php?action=viewmailbox&box="

    detail_url = "https://kp.m-team.cc/messages.php?action=viewmessage&id="

    box = [
        "0",  # inbox
        "-1",  # send box
        "-2"  # system box
    ]

    step = ["quit", "choose", "read"]
    show_message = ["***** Quit Now! *****",
                    "***** Choose a message box, from 1 to 3 *****\n1: in box\n2: send box\n3: system box\n",
                    "***** Choose a message to read: *****\n"]

    def get_cmd(self):
        curr_step = 1
        messages = []
        while True:
            if curr_step <= 0:
                print("Quit now!")
                break

            cmd = input(self.show_message[curr_step])
            if cmd.upper() == "Q":
                curr_step = 0
                continue
            elif cmd.upper() == "F":
                curr_step += 1
                curr_step = min(len(self.step) - 1, curr_step)
                continue
            elif cmd.upper() == "B":
                curr_step -= 1
                continue

            if curr_step == 1:
                index = min(max(int(cmd) - 1, 0), len(self.box))
                messages = self.read_msg(self.box[index])
            elif curr_step == 2:
                index = min(max(int(cmd) - 1, 0), len(messages))
                self.read_msg_content(messages[index])

    def read_msg(self, index):
        self.login_if_not()

        soup_obj = HttpUtils.get(self.url + index, headers=self.site.login_headers)
        assert soup_obj is not None

        tr_list = soup_obj.select("#outer form table tr")

        messages = []
        cnt = 0
        for tr in tr_list:
            cnt += 1
            if cnt == 1:
                # skip the caption tr
                continue

            td_list = tr.select("td.rowfollow")

            if len(td_list) < 4:
                # skip footer
                continue

            msg = Message()
            msg.read = len(td_list[0].select("img[alt=\"Read\"]")) > 0
            msg.title = HttpUtils.get_content(td_list[1], "a")
            msg.from_user = HttpUtils.get_content(td_list[2], "span a b")
            if msg.from_user is None:
                # for ad.
                msg.from_user = td_list[2].contents[0]
            msg.since = HttpUtils.get_content(td_list[3], "span")
            link = HttpUtils.get_attr(td_list[1], "a", "href")
            msg.id = link.split("id=")[1]
            messages.append(msg)

        print("--------------------------------------")
        index = 1
        for msg in messages:
            print("{:<2}|".format(index) + str(msg))
            index += 1
        print("--------------------------------------")

        return messages

    def read_msg_content(self, msg):
        soup_obj = HttpUtils.get(self.detail_url + msg.id, headers=self.site.login_headers)
        assert soup_obj is not None

        td_list = soup_obj.select("#outer table:nth-of-type(2) tr:nth-of-type(3) td:nth-of-type(1)")

        print("--------------------------------------")
        print(td_list[0].text)
        print("--------------------------------------")

    def clean_up(self):
        self.login_if_not()
        pass


if __name__ == "__main__":
    NormalAlert().check()
    # NormalAlert().download_seed("209094")
    # AdultAlert().check()
    # UserCrawl().crawl([182533])
    # NormalAlert().init_setting()
    # UserCrawl().refresh()
    # UploadCheck().check()
    # CandidateVote().check()
