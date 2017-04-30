import os
import re

import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# disable warning for skip check SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HttpUtils:
    session = None
    cookie = None

    KEY_COOKIE_LOCATION = "cookei_location"
    DEFAULT_HEADER = {
        "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36"
    }

    @classmethod
    def create_session(cls):
        try:
            return requests.Session()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get(cls, url, session=None, headers=None, proxy=None, timeout=60, return_raw=False):
        if cls.session is None:
            cls.session = cls.create_session()
        if headers is None:
            headers = cls.DEFAULT_HEADER

        try:
            response = cls.session.get(url, timeout=timeout, headers=headers, proxies=proxy, verify=False)
            if response.status_code != 200:
                print("Wrong response status: " + str(response.status_code))
                return None

            if return_raw:
                return response
            else:
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(e)
            return None

    @classmethod
    def post(cls, url, session=None, data=None, headers=None, proxy=None, returnRaw=False):
        if cls.session is None:
            print("create session")
            cls.session = cls.create_session()

        try:
            response = cls.session.post(url, headers=headers, proxies=proxy, verify=False, data=data)
            if response.status_code != 200:
                print("Wrong response status: " + str(response.status_code))
            if returnRaw:
                return response.text
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
            return items[0].contents[index]

    @classmethod
    def download_file(cls, url, dest_path, headers=None):
        if os.path.exists(dest_path):
            print("Existing " + dest_path)
            return True
        res = cls.get(url, timeout=30, return_raw=True)
        if res is None:
            print("####### ERROR: empty content from: " + url)
            return False

        try:
            f = open(dest_path, "wb")
            f.write(res.content)
            f.close()
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


if __name__ == "__main__":
    print(HttpUtils.get("https://www.jd.com"))
