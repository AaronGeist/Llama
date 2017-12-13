import re

from biz.pt.BaseUploader import BaseUploader
from model.seed import SeedInfo
from model.site import Site
from util.utils import HttpUtils


class TTGRSS(BaseUploader):
    def get_site_name(self):
        return "ttg"

    def generate_site(self):
        site = Site()
        site.home_page = "https://totheglory.im/putrss.php?par=dnZ2MTA1LDEwNywxMDQsMTA2LDUxLDUyLDUzLDU0LDEwOCwxMDksNjIsNjMsNjcsNjksNzAsNzMsNzYsNzUsNzQsODcsODgsOTksOTAsODIsODMsNTksNTcsNTgsMTAzLDEwMSw2MCw5MSw4NCw5Mnx8fGI3ODRlNmI0ZjkzMGY3ODJjNjFmMGNhNjZjMGY1NzY0eno=&ssl=yes"
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
                seed.size = HttpUtils.pretty_format(info[1].split(" ")[-2] + info[1].split(" ")[-1], "MB")
                # seed.url = HttpUtils.get_content(item, "link")
                seed.url = item.contents[4]
                seed.id = self.parse_id(seed.url)

                seeds.append(seed)
            except Exception as e:
                pass

        return seeds

    @staticmethod
    def parse_id(url):
        m = re.search("par=(\w+)==&", url)
        assert m is not None
        return m.group(1)

    def easy_strategy(self, data):
        filtered_seeds = list(
            filter(lambda x: (x.title.lower().endswith("wiki") or x.title.lower().endswith("ttg")), data))

        filtered_seeds = self.sort_seed(filtered_seeds)

        return filtered_seeds

    def download_seed_file(self, seed_id):

        res = HttpUtils.get("https://totheglory.im/rssdd.php?par=%s==&amp;ssl=yes" % seed_id,
                            headers=self.site.login_headers,
                            return_raw=True)

        try:
            with open("%s.torrent" % seed_id, "wb") as f:
                f.write(res.content)
        except Exception as e:
            print("Cannot download seed file: " + seed_id, e)


if __name__ == "__main__":
    TTGRSS().check()
