# -*- coding:utf-8 -*-
import json
import re
import os
import time
from random import random

from core.login import Login
from model.site import Site
from util.config import Config
from util.utils import HttpUtils


class Miui(Login):
    page_url_template = "http://www.miui.com/thread-{0}-1-1.html"

    def generate_site(self):
        site = Site()

        site.home_page = "http://www.miui.com/forum.php?mod=forumdisplay&fid=5&filter=author&orderby=dateline"
        site.login_headers = {
            "User-agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-encoding": "gzip, deflate",
            "Accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6,ja;q=0.5",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "www.miui.com",
            "Upgrade-insecure-requests": "1",
            "Cache-control": "max-age=0",
            "Cookie": "UM_distinctid=163dfb3e2ff73d-0a9bc0e1447ce4-336a7706-13c680-163dfb3e3005eb; CNZZDATA5677709=cnzz_eid%3D1297791920-1528461510-http%253A%252F%252Fwww.miui.com%252F%26ntime%3D1528477020; CNZZDATA1270690907=893238151-1528481971-https%253A%252F%252Fwww.baidu.com%252F%7C1528481971; __utmc=230417408; __utmz=230417408.1528538555.3.3.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; Hm_lvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528511334,1528511372,1528511379,1528538555; PHPSESSID=vnc60biqa61d31ih5b930abm41; MIUI_2132_widthauto=-1; CNZZDATA2441309=cnzz_eid%3D1987410948-1528462183-null%26ntime%3D1528586803; CNZZDATA30049650=cnzz_eid%3D1453184979-1528466198-null%26ntime%3D1528585841; __utma=230417408.2038836981.1528511192.1528549122.1528589392.5; CNZZDATA5557939=cnzz_eid%3D1504230810-1528462019-null%26ntime%3D1528586646; MIUI_2132_saltkey=sF6wQsSz; MIUI_2132_lastvisit=1528586043; MIUI_2132_visitedfid=773; MIUI_2132_ulastactivity=426f3zvob00mxZWwQ8FWbaETgRqM07T%2FhlJ%2FdhF%2F34sFvhOFvrFk5fg; MIUI_2132_auth=443fj0wdiMkvdCfJKHGlfDsueGlS1sPWf%2BJ%2BQMa323mysEuk6RBvZHg; lastLoginTime=d9e2yZbafd8tt3%2BIQc55QkmXvFWlG588oMrLYGlAZoyMMlgcAOs7; MIUI_2132_forum_lastvisit=D_773_1528589818; MIUI_2132_noticeTitle=1; MIUI_2132_checkpm=1; MIUI_2132_lastact=1528590043%09home.php%09misc; MIUI_2132_sendmail=1; __utmb=230417408.13.10.1528589392; Hm_lpvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528589985"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#hd_u_name"
        site.login_verify_str = "\n                            胡迪君                        "
        site.login_username = Config.get("putao_username")
        site.login_password = Config.get("putao_password")

        return site

    def build_post_data(self, site):
        data = dict()
        data['username'] = site.login_username
        data['password'] = site.login_password
        data['checkcode'] = "XxXx"

        return data

    def check_in(self):
        self.site = self.generate_site()
        assert self.login(self.site)

        print("Login success!")

    def crawl(self):
        self.check_in()

        return self.water()

    def water(self):

        url_prefix = "http://www.miui.com/forum.php?mod=forumdisplay&fid=5&orderby=dateline&filter=author&orderby=dateline&page="
        page = 1
        cnt = 1
        max_cnt = 50
        chinese_char = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]

        id_list = []
        while True:
            soup_obj = HttpUtils.get(url_prefix + str(page))
            print("new page: " + str(page))
            id_list.extend(HttpUtils.get_attrs(soup_obj, "tbody", "id"))

            page += 1

            if len(id_list) > max_cnt:
                break

        id_list = id_list[:max_cnt]
        for id in id_list:
            if not id.startswith("normalthread"):
                continue

            id = id[13:]
            page_url = self.page_url_template.format(id)

            page_soup_obj = HttpUtils.get(page_url)
            assert page_soup_obj is not None

            i = str(cnt)
            length = len(i)
            num = ""
            for index in range(length):
                num += chinese_char[int(i[index])]

            id_num = ""
            for index in range(len(id)):
                id_num += chinese_char[int(id[index])]

            random_id = str(int(random() * 1000000000000000))
            chinese_char = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]

            random_id_num = ""
            for index in range(len(random_id)):
                random_id_num += chinese_char[int(random_id[index])]

            title = HttpUtils.get_content(page_soup_obj, "title").strip().replace("_灌者为王_MIUI论坛", "")

            message = "时间{0}，帖子ID{1}，标题\"{2}\"，随机数{3}，第{4}个积分，打扰".format(
                time.strftime("%b %d %Y %H:%M:%S", time.localtime()), id_num, title, random_id_num,
                num)
            print(message)  # form_hash = page_soup_obj.select("input[name='formhash']")[0]["value"]
            form_hash = "c086a030"
            form_hash_mirror = form_hash + ":" + form_hash[::-1]
            post_data = dict()
            post_data["posttime"] = str(int(time.time()))
            post_data["formhash"] = form_hash_mirror
            post_data["usesig"] = "1"
            post_data["subject"] = "  "
            post_data["message"] = message

            form_submit_url = "http://www.miui.com/forum.php?mod=post&action=reply&fid=5&tid={0}&extra=page=1&replysubmit=yes&infloat=yes&handlekey=fastpost".format(
                id)

            # print(post_data)

            post_result = HttpUtils.post(form_submit_url, headers=self.site.login_headers, data=post_data,
                                         returnRaw=False)
            assert post_result is not None
            time.sleep(int(random() * 60) + 90)
            cnt += 1

    def zz(self):
        # self.check_in()

        # get article of jd
        soup = HttpUtils.get("http://jandan.net/")
        article_urls = HttpUtils.get_attrs(soup, "#content div.post div.indexs h2 a", "href")
        print(len(article_urls))

        for article_url in article_urls:
            # if Cache().get(article_url) is not None:
            #     continue

            article_soup = HttpUtils.get(article_url)
            title = HttpUtils.get_content(article_soup, "title").strip()
            # Cache().set(article_url, article_url)
            break

        print(article_urls[0])


if __name__ == '__main__':
    miui = Miui()
    miui.water()
