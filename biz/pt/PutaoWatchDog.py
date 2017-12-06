import re

from biz.pt.BaseUploader import BaseUploader
from core.emailSender import EmailSender
from core.monitor import Monitor
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class PuTaoWatchDog(BaseUploader):
    def get_site_name(self):
        return "putao"

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
        site.login_verify_str = Config.get(self.get_site_name() + "_username")
        site.login_username = site.login_verify_str
        site.login_password = Config.get(self.get_site_name() + "_password")
        site.stat_page = "https://pt.sjtu.edu.cn/mybonus.php"

        self.site = site

    def build_post_data(self, site):
        data = super().build_post_data(site)
        data['checkcode'] = "XxXx"
        return data

    def parse_page(self, soup_obj):
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

            seed.sticky = len(td_list[1].select("table td img[alt=\"Sticky\"]"))
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

            # parse discount
            if len(td_list[1].select("table td font.halfdown")) > 0:
                seed.discount = 50
            elif len(td_list[1].select("table td font.d30down")) > 0:
                seed.discount = 30
            else:
                seed.discount = 100

            seeds.append(seed)

        return seeds

    def download_seed_file(self, seed_id):
        self.login_if_not()

        res = HttpUtils.get("https://pt.sjtu.edu.cn/download.php?id=" + str(seed_id), headers=self.site.login_headers,
                            return_raw=True)
        try:
            with open("%s.torrent" % seed_id, "wb") as f:
                f.write(res.content)
        except Exception as e:
            print("Cannot download seed file: " + seed_id, e)

    def hell_strategy(self, data):
        # 1. free
        # 2. sticky
        # 3. down/up > 5
        filtered_seeds = list(filter(
            lambda x: (x.upload_num != 0 and (x.free or x.sticky or (round(x.download_num / x.upload_num, 1) >= 5))),
            data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        final_seeds = self.limit_total_size(filtered_seeds, 20 * 1024)

        return final_seeds


class MagicPointChecker(PuTaoWatchDog, Monitor):
    def get_bucket(self):
        return self.get_site_name() + "_mp"

    def generate_site(self):
        super().generate_site()
        self.site.home_page = "https://pt.sjtu.edu.cn/mybonus.php"

    def parse_page(self, soup_obj):
        assert soup_obj is not None

        div_list = soup_obj.select("table.mainouter tr td table tr td div[align='center']")
        assert len(div_list) == 1

        content = div_list[0].contents[0]
        m = re.search(u"获取(\d+.\d+)个魔力", content)
        assert m
        return float(m.group(1))

    def alert(self, data):
        threshold = Config.get(self.get_site_name() + "_mp_threshold")
        if data <= threshold:
            EmailSender.send("魔力值警告: %s <= %s" % (str(data), threshold), "")

    def generate_data(self):
        return self.crawl()


class UploadMonitor(MagicPointChecker):
    def get_bucket(self):
        return self.get_site_name() + "_upload"

    def parse_page(self, soup_obj):
        assert soup_obj is not None

        span_list = soup_obj.select("#usermsglink span")
        return float(span_list[1].contents[2].replace("TB", "").strip())


class BbsMonitor(PuTaoWatchDog):
    def generate_site(self):
        super().generate_site()
        self.site.home_page = "https://pt.sjtu.edu.cn/forums.php?action=viewtopic&forumid=27&topicid=84712"

    def parse_page(self, soup_obj):
        assert soup_obj is not None

        floor_list = soup_obj.select("table td nobr font b")

        user_list = soup_obj.select("table td.embedded span.nobr a b")

        return floor_list, user_list

    def filter(self, data):
        return data

    def action(self, data):
        floor_list, user_list = data
        cnt = 0
        for user in user_list:
            user_name = user.contents[0]
            cnt += 1
            if cnt > 32 and user_name == "69589606feng":
                EmailSender.send(u"TTG邀请回帖啦", "")


if __name__ == "__main__":
    PuTaoWatchDog().check()
    # MagicPointChecker().monitor()
    # BbsMonitor().check()
    # PuTaoWatchDog().stat()
