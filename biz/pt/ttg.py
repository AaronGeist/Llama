from biz.pt.baseuploader import BaseUploader
from model.seed import SeedInfo
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class TTG(BaseUploader):
    def get_site_name(self):
        return "ttg"

    def generate_site(self):
        site = Site()
        site.home_page = "https://totheglory.im/browse.php?c=M"
        site.login_page = "https://totheglory.im/takelogin.php"

        # encoding/compression is disabled
        site.login_headers = {
            "user-agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            # "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
            "dnt": "1",
            "origin": "https://totheglory.im",
            "referer": "https://totheglory.im/login.php?returnto=",
            "upgrade-insecure-requests": "1",
            "cache-control": "max-age=0",
            "cookie": "__cfduid=d38205529894764cfe4019d151d9c5ba41512649384; cf_clearance=df03bb3d6d563412e8c8fc778a67f4725aa522e1-1512649390-7200"
        }

        site.login_needed = True
        site.login_verify_css_selector = "table td span.smallfont b a"
        site.login_verify_str = Config.get(self.get_site_name() + "_username")
        site.login_username = site.login_verify_str
        site.login_password = Config.get(self.get_site_name() + "_password")
        site.stat_page = "https://totheglory.im/mybonus.php"

        self.site = site

    def build_post_data(self, site):
        data = super().build_post_data(site)
        data["otp"] = ""
        data["passan"] = "putao"
        data["passid"] = "2"
        data["lang"] = "0"
        data["rememberme"] = "no"
        return data

    def parse_page(self, soup_obj):
        tr_list = soup_obj.select("#torrent_table tr")

        seeds = []
        cnt = 0
        for tr in tr_list:
            cnt += 1
            if cnt == 1:
                # skip the caption tr
                continue

            seed = SeedInfo()
            td_list = tr.select("td")
            if len(td_list) < 10:
                continue

            seed.sticky = len(td_list[1].select("div img[alt=\"置顶\"]"))
            seed.title = HttpUtils.get_content(td_list[1].select("div a b"))
            seed.url = td_list[1].select("div a")[0]['href']
            seed.free = len(td_list[1].select("div a img[alt=\"free\"]")) > 0
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


if __name__ == "__main__":
    TTG().crawl()
