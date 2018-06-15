# -*- coding:utf-8 -*-
import json
import re
import os
import time
from random import random

from bs4 import Tag

from core.db import Cache
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
            "Cookie": "UM_distinctid=163dfb3e2ff73d-0a9bc0e1447ce4-336a7706-13c680-163dfb3e3005eb; __utmc=230417408; __utmz=230417408.1528538555.3.3.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; Hm_lvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528511334,1528511372,1528511379,1528538555; PHPSESSID=vnc60biqa61d31ih5b930abm41; MIUI_2132_widthauto=-1; CNZZDATA5677709=cnzz_eid%3D1297791920-1528461510-http%253A%252F%252Fwww.miui.com%252F%26ntime%3D1528801426; CNZZDATA1270690907=893238151-1528481971-https%253A%252F%252Fwww.baidu.com%252F%7C1528807405; CNZZDATA1270691464=1221855440-1528592121-%7C1528807818; __utma=230417408.2038836981.1528511192.1528948475.1529018798.24; MIUI_2132_saltkey=Dq25112M; MIUI_2132_lastvisit=1529015245; MIUI_2132_ulastactivity=ea4aWC6qjF726cp14stuTP38lm5%2Fz1U8KY4yFHUvbP24ahpFdgOCXE0; MIUI_2132_auth=4b02CoTQT5q2tpsUdjzpS9HF2DtTQnq6AMZYKCILTY8Y%2F%2F83kA39sQ; lastLoginTime=7acaYS1hE%2B2Q74w3%2BvqcMrmn0iQGS%2FnaSlI4t7NM0YtvqlbAQ70Q; MIUI_2132_noticeTitle=1; MIUI_2132_home_diymode=1; CNZZDATA30049650=cnzz_eid%3D1453184979-1528466198-null%26ntime%3D1529015956; MIUI_2132_nofavfid=1; CNZZDATA5557939=cnzz_eid%3D1504230810-1528462019-null%26ntime%3D1529017909; MIUI_2132_smile=3D1; MIUI_2132_viewid=tid_15212628; CNZZDATA2441309=cnzz_eid%3D1987410948-1528462183-null%26ntime%3D1529016417; MIUI_2132_forum_lastvisit=D_40_1529019167D_772_1529019395; MIUI_2132_clearUserdata=forum; MIUI_2132_seccodeS00=783dKdaY3bkLwO0BrfTvBubeflSwHQFV7Do%2F6GbCNTvNarru9KvxpguJH7TSapSAgQJUewp0BQbY; MIUI_2132_checkpm=1; MIUI_2132_sendmail=1; __utmt=1; MIUI_2132_visitedfid=3D37D772D48D773D40D5; MIUI_2132_lastact=1529019546%09forum.php%09; __utmb=230417408.49.10.1529018798; Hm_lpvt_3c5ef0d4b3098aba138e8ff4e86f1329=1529019509"
            # "Cookie": "UM_distinctid=163dfb3e2ff73d-0a9bc0e1447ce4-336a7706-13c680-163dfb3e3005eb; CNZZDATA5677709=cnzz_eid%3D1297791920-1528461510-http%253A%252F%252Fwww.miui.com%252F%26ntime%3D1528477020; CNZZDATA1270690907=893238151-1528481971-https%253A%252F%252Fwww.baidu.com%252F%7C1528481971; __utmc=230417408; __utmz=230417408.1528538555.3.3.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; Hm_lvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528511334,1528511372,1528511379,1528538555; PHPSESSID=vnc60biqa61d31ih5b930abm41; MIUI_2132_widthauto=-1; CNZZDATA2441309=cnzz_eid%3D1987410948-1528462183-null%26ntime%3D1528586803; CNZZDATA30049650=cnzz_eid%3D1453184979-1528466198-null%26ntime%3D1528585841; __utma=230417408.2038836981.1528511192.1528549122.1528589392.5; CNZZDATA5557939=cnzz_eid%3D1504230810-1528462019-null%26ntime%3D1528586646; MIUI_2132_saltkey=sF6wQsSz; MIUI_2132_lastvisit=1528586043; MIUI_2132_visitedfid=773; MIUI_2132_ulastactivity=426f3zvob00mxZWwQ8FWbaETgRqM07T%2FhlJ%2FdhF%2F34sFvhOFvrFk5fg; MIUI_2132_auth=443fj0wdiMkvdCfJKHGlfDsueGlS1sPWf%2BJ%2BQMa323mysEuk6RBvZHg; lastLoginTime=d9e2yZbafd8tt3%2BIQc55QkmXvFWlG588oMrLYGlAZoyMMlgcAOs7; MIUI_2132_forum_lastvisit=D_773_1528589818; MIUI_2132_noticeTitle=1; MIUI_2132_checkpm=1; MIUI_2132_lastact=1528590043%09home.php%09misc; MIUI_2132_sendmail=1; __utmb=230417408.13.10.1528589392; Hm_lpvt_3c5ef0d4b3098aba138e8ff4e86f1329=1528589985"
        }

        site.login_needed = True
        site.login_verify_css_selector = "#hd_u_name"
        site.login_verify_str = "\n                            薛定谔的小仓鼠                        "

        return site

    def check_in(self):
        self.site = self.generate_site()
        assert self.login(self.site)

    def get_score(self):
        self.check_in()

        soup = HttpUtils.get("http://www.miui.com/space-uid-2248502469.html")
        assert soup is not None
        score = HttpUtils.get_content(soup, "#statistic_content li:nth-of-type(1) a")
        return int(score)

    def water(self):
        self.check_in()

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
            # form_hash = page_soup_obj.select("input[name='formhash']")[0]["value"]
            form_hash = "0d4c71ae"
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

    def sign(self):
        self.check_in()

        soup = HttpUtils.get("http://www.miui.com/extra.php?mod=sign/index&op=sign", headers=self.site.login_headers,
                             return_raw=True)

        assert soup is not None

    def zz(self):
        source_url_template = "https://bh.sb/post/category/main/page/{0}/"
        post_url = "http://www.miui.com/forum.php?mod=post&action=newthread&fid=5&extra=&topicsubmit=yes"

        self.check_in()

        max_cnt = 50
        cnt = 0
        page_num = 1
        articles = list()
        stop_flag = False
        while not stop_flag:
            # get article of bhsb
            soup = HttpUtils.get(source_url_template.format(page_num))
            article_urls = HttpUtils.get_attrs(soup, "h2 a", "href")
            page_num += 1

            for article_index in range(len(article_urls)):
                article_url = article_urls[article_index]
                if Cache().get(article_url) is not None:
                    continue

                article_soup = HttpUtils.get(article_url)
                titles = HttpUtils.get_contents(article_soup, ".article-content p")

                title_cnt = int(len(titles) / 2)

                for title_index in range(0, title_cnt):
                    try:
                        title = titles[title_index * 2].split("】")[1]
                        image = titles[title_index * 2 + 1]

                        if type(image) != Tag:
                            continue

                        src = image.attrs["src"]
                        if src.endswith("jpg"):
                            continue

                        message = "[img]{0}[/img]".format(src)

                        if Cache().get(title) is not None:
                            continue
                        Cache().set(title, message)

                        articles.append((title, message))

                        cnt += 1

                        if cnt >= max_cnt:
                            stop_flag = True
                            break
                    except:
                        pass

                if stop_flag:
                    break

                # only if all articles are included, then mark this url
                Cache().set(article_url, article_url)

        for (title, message) in articles:
            print((title, message))

            form_hash = "0d4c71ae"
            form_hash_mirror = form_hash + ":" + form_hash[::-1]
            post_data = dict()
            post_data["posttime"] = str(int(time.time()))
            post_data["formhash"] = form_hash_mirror
            post_data["wysiwyg"] = "1"
            post_data["typeid"] = "1631"
            post_data["allownoticeauthor"] = "1"
            post_data["addfeed"] = "1"
            post_data["usesig"] = "1"
            post_data["save"] = ""
            post_data["uploadalbum"] = "-2"
            post_data["newalbum"] = "请输入相册名称"
            post_data["subject"] = title
            post_data["message"] = message

            post_result = HttpUtils.post(post_url, headers=self.site.login_headers, data=post_data,
                                         returnRaw=False)
            assert post_result is not None

            # 1小时只能发5篇
            time.sleep(int(random() * 30) + 750)

    def vote(self):
        self.check_in()

        source_list_url_template = "http://www.miui.com/home.php?mod=space&uid=133153462&do=thread&view=me&order=dateline&from=space&page={0}"
        soup = HttpUtils.get(source_list_url_template.format(1), headers=self.site.login_headers)
        assert soup is not None

        article_urls = HttpUtils.get_attrs(soup, "div.tl th > a", "href")
        for article_url in article_urls:
            try:
                article_url = "http://www.miui.com/" + article_url
                article_soup = HttpUtils.get(article_url, headers=self.site.login_headers)
                assert article_soup is not None
                title = HttpUtils.get_content(article_soup, "title")
                form = article_soup.select("#poll", limit=1)
                option = article_soup.select("#option_1", limit=1)
                if form is None or len(form) == 0:
                    continue
                if option is None or len(option) == 0:
                    continue
                print(title)
            except:
                pass



if __name__ == '__main__':
    miui = Miui()
    miui.zz()


# forum.php?mod=misc&action=votepoll&fid=464&tid=15078723&pollsubmit=yes&quickforward=yes
#
# 195826
#
# pollanswers[]: 195826