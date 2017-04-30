from model.ProxyInfo import ProxyInfo
from util.utils import HttpUtils


class BaseCrawler(object):
    PAGE_NUM_PLACEHOLDER = "--PAGE_NUM--"
    MAX_FAILURE_NUM = 3

    navigation_url = None
    line_css_selector = None
    ip_css_selector = None
    port_css_selector = None
    skip_first_line = False

    def parse(self):
        ret = []
        cnt = 1
        fail_cnt = 0
        while True:
            url = self.navigation_url.replace(self.PAGE_NUM_PLACEHOLDER, str(cnt))
            print(url)
            soup_obj = HttpUtils.get(url=url)
            if soup_obj is None:
                print("Fail " + url)

                fail_cnt += 1
                if fail_cnt >= self.MAX_FAILURE_NUM:
                    break

                continue
            ret.extend(self.parse_line(soup_obj))
            cnt += 1
        return ret

    def parse_line(self, soup_obj):
        lines = soup_obj.select(self.line_css_selector)
        if self.skip_first_line:
            lines.pop(0)

        ret = []
        for line in lines:
            ip = line.select(self.ip_css_selector)[0].get_text()
            port = line.select(self.port_css_selector)[0].get_text()
            print("Find %s %s" % (ip, port))
            proxyInfo = ProxyInfo()
            proxyInfo.ip = ip
            proxyInfo.port = port
            ret.append(proxyInfo)

        return ret
