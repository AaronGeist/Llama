import datetime
import json
import os
import re

import requests
import time

from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from util.config import Config

# disable warning for skip check SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HttpUtils:
    session = None
    cookie = None

    KEY_COOKIE_LOCATION = "cookie_location"
    DEFAULT_HEADER = {
        "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36"
    }

    @classmethod
    def create_session_if_absent(cls):
        try:
            if cls.session is None:
                cls.session = requests.Session()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def load_cookie(cls):
        if cls.session is not None:
            cookie_file = Config.get(cls.KEY_COOKIE_LOCATION)
            if os.path.exists(cookie_file):
                with open(cookie_file, "r") as f:
                    try:
                        data = f.read()
                        if data != "":
                            cls.session.cookies = requests.utils.cookiejar_from_dict(json.loads(data),
                                                                                     cookiejar=None,
                                                                                     overwrite=True)
                    except Exception as e:
                        pass

    @classmethod
    def save_cookie(cls):
        if cls.session is not None:
            with open(Config.get(cls.KEY_COOKIE_LOCATION), "w") as f:
                f.write(json.dumps(requests.utils.dict_from_cookiejar(cls.session.cookies)))

    @classmethod
    def clear_cookie(cls):
        if cls.session is not None:
            cls.session.cookies.clear()

        with open(Config.get(cls.KEY_COOKIE_LOCATION), "w") as f:
            f.write("")

    @classmethod
    def get_crazy(cls, url, session=None, headers=None, proxy=None, times=0):
        if session is not None:
            cls.session = session
        cls.create_session_if_absent()

        if headers is None:
            headers = cls.DEFAULT_HEADER

        time_start = time.time()
        for i in range(times):
            try:
                cls.session.get(url, timeout=1, headers=headers, proxies=proxy, verify=False)
            except Exception as e:
                pass
        time_end = time.time()
        print('time cost', time_end - time_start, 's')

    @classmethod
    def get_with_retry(cls, url, retry=5, session=None, headers=None, proxy=None, timeout=60, return_raw=False,
                       allow_redirects=True):
        retry_cnt = 0
        while True:
            resp = HttpUtils.get(url=url, session=session, headers=headers, proxy=proxy, timeout=timeout,
                                 return_raw=return_raw, allow_redirects=allow_redirects)
            if resp is not None:
                break
            else:
                retry_cnt += 1

            assert retry_cnt < retry, "fail to query %s" % url

        return resp

    @classmethod
    def get(cls, url, session=None, headers=None, proxy=None, timeout=60, return_raw=False, allow_redirects=True):
        if session is not None:
            cls.session = session
        cls.create_session_if_absent()

        if headers is None:
            headers = cls.DEFAULT_HEADER

        try:
            response = cls.session.get(url, timeout=timeout, headers=headers, proxies=proxy, verify=False,
                                       allow_redirects=allow_redirects)
            if response.status_code != 200 and response.status_code != 301:
                # print("Wrong response status: " + str(response.status_code))
                return None

            if return_raw:
                return response
            else:
                return BeautifulSoup(response.text.encode(response.encoding, 'ignore'), 'html.parser')
        except Exception as e:
            print(e)
            return None

    @classmethod
    def post(cls, url, session=None, data=None, headers=None, proxy=None, returnRaw=False):
        if session is not None:
            cls.session = session
        cls.create_session_if_absent()

        try:
            response = cls.session.post(url, headers=headers, proxies=proxy, verify=False, data=data)
            if response.status_code != 200:
                print("Wrong response status: " + str(response.status_code))
            if returnRaw:
                return response
            else:
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_attr(cls, soup_obj, match_exp, attr):
        assert soup_obj is not None
        assert match_exp is not None

        tags = soup_obj.select(match_exp)
        if tags is not None and len(tags) > 0:
            return tags[0][attr]
        else:
            return None

    @classmethod
    def get_attrs(cls, soupObj, matchExp, attr):
        assert (soupObj is not None)
        assert (matchExp is not None)

        tags = soupObj.select(matchExp)

        attrs = list()
        for tag in tags:
            attrs.append(tag[attr])

        return attrs

    @classmethod
    def get_content(cls, soupObj, matchExp, index=0):
        assert (soupObj is not None)
        assert (matchExp is not None)

        items = soupObj.select(matchExp)
        if items is None or len(items) <= 0:
            return None
        else:
            if len(items[0].contents) > index:
                return items[0].contents[index]
            else:
                return None

    @classmethod
    def get_contents(cls, soupObj, matchExp, index=0):
        assert (soupObj is not None)
        assert (matchExp is not None)

        items = soupObj.select(matchExp)

        contents = list()
        for item in items:
            if len(item.contents) > index:
                contents.append(item.contents[index])
            else:
                contents.append(None)

        return contents

    @classmethod
    def download_file(cls, url, dest_path, headers=None, over_write=False):
        if os.path.exists(dest_path) and not over_write:
            print("Existing " + dest_path)
            return True
        res = cls.get(url, timeout=30, return_raw=True)
        if res is None:
            print("####### ERROR: empty content from: " + url)
            return False

        try:
            with open(dest_path, "wb") as f:
                f.write(res.content)
        except Exception as e:
            print("Cannot write file: " + dest_path, e)
            return False
        print("Downloaded " + url)
        return True

    @classmethod
    def parseImageName(cls, url):
        assert (url is not None)

        if url.endswith("png") or url.endswith("jgp") or url.endswith("gif"):
            subUrl = url.split("/")
            return subUrl[len(subUrl) - 1]
        else:
            res = re.findall("/([^/]*?\.(jpg|png|gif))", url)
            if len(res) > 0:
                return res[0][0]
            print("Cannot parser image name")
            return "NA.jpg"

    factor_map = {
        "TB": 1 / (1024 * 1024),
        "GB": 1 / 1024,
        "MB": 1,
        "KB": 1024
    }

    @classmethod
    def pretty_format(cls, data, unit):
        assert data is not None

        factor = cls.factor_map[str(unit).upper()]
        data = str(data).replace(" ", "").upper().strip()

        if data.endswith("TB"):
            res = float(data.replace("TB", "")) * (1024 * 1024 * factor)
        elif data.endswith("GB"):
            res = float(data.replace("GB", "")) * (1024 * factor)
        elif data.endswith("MB"):
            res = float(data.replace("MB", "")) * factor
        elif data.endswith("KB"):
            res = float(data.replace("KB", "")) * (factor / 1024)
        else:
            res = 0.001

        return res

    @classmethod
    def get_time_stamp(cls):
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        data_secs = datetime.datetime.now().microsecond / 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)
        return time_stamp


if __name__ == "__main__":
    print(HttpUtils.get("https://www.jd.com"))
