import json
import urllib
from queue import Queue
from random import random
from time import sleep

from core.login import Login
from util.asyncRequests import HttpReq, AsyncHttpHelper
from util.parallel_template import ParallelTemplate
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()

    amazon_base_url = "https://www.amazon.cn"

    amazon_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
        "Host": "www.amazon.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 YaBrowser/19.9.0.1768 Yowser/2.5 Safari/537.36"
    }

    douban_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "api.douban.com",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": 'll="108296"; bid=jZE5oUOtVG0; douban-fav-remind=1; _vwo_uuid_v2=DB520FAE5F335803B4D7DA63CA4B7F750|fcf1817daa7794b0fcd6364066b1e200; __utmv=30149280.314; gr_user_id=d4b56119-c588-46d4-be1d-0fe640e32f30; __utmc=30149280; __utmc=81379588; viewed="26389900_26389895_7065521_1962641"; push_noty_num=0; push_doumail_num=0; dbcl2="3141710:v8sWwrEAw2Y"; ck=r5OF; gr_session_id_22c937bbd8ebd703f2d8e9445f7dfd03=224c858d-4d43-4d29-8982-02f4d45e7fb5; gr_cs1_224c858d-4d43-4d29-8982-02f4d45e7fb5=user_id%3A1; gr_session_id_22c937bbd8ebd703f2d8e9445f7dfd03_224c858d-4d43-4d29-8982-02f4d45e7fb5=true; _pk_ref.100001.3ac3=%5B%22%22%2C%22%22%2C1572698641%2C%22https%3A%2F%2Fsearch.douban.com%2Fbook%2Fsubject_search%3Fsearch_text%3D%25E6%2588%2591%25E4%25BB%25AC%25E4%25BB%25A8%26cat%3D1001%22%5D; _pk_id.100001.3ac3=ac5d8546a4cc3dc1.1571111753.7.1572698641.1572694781.; _pk_ses.100001.3ac3=*; __utma=30149280.35535565.1562393937.1572694179.1572698641.33; __utmz=30149280.1572698641.33.17.utmcsr=search.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/book/subject_search; __utmt_douban=1; __utmb=30149280.1.10.1572698641; __utma=81379588.1514131154.1571993271.1572694182.1572698641.6; __utmz=81379588.1572698641.6.5.utmcsr=search.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/book/subject_search; __utmt=1; __utmb=81379588.1.10.1572698641; ap_v=0,6.0',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 YaBrowser/19.9.0.1768 Yowser/2.5 Safari/537.36"
    }

    category_black_list = ["考试", "教材教辅与参考书", "少儿", "孕产育儿", "时尚", "娱乐", "烹饪美食与酒", "英语与其他外语", "法律", "政治与军事", "杂志新阅",
                           "进口原版"]

    @classmethod
    def start(cls):
        cls.fetch_meta_data()
        cls.crawl_book()
        # cls.crawl_book_rank()
        cls.sort_book()

    @classmethod
    def fetch_meta_data(cls):
        with open("ku_meta.txt", "r", encoding="utf-8") as fp:
            if fp.readline():
                # already exist, skip
                return

        home_url = "https://www.amazon.cn/s?i=digital-text&rh=n%3A116087071%2Cn%3A116089071%2Cn%3A116176071%2Cn%3A1337022071&page=1"

        # find all category, sub-category and page number
        soup_obj = HttpUtils.get(home_url, headers=cls.amazon_headers)
        if soup_obj is None:
            print("ERROR: Cannot find category")
            return

        category_text_list = HttpUtils.get_contents(soup_obj,
                                                    "#leftNav ul:nth-of-type(3) div li span a.s-ref-text-link span")
        category_link_list = HttpUtils.get_attrs(soup_obj, "#leftNav ul:nth-of-type(3) div li span a.s-ref-text-link",
                                                 "href")

        if len(category_text_list) != len(category_link_list):
            print("ERROR: Category number not correct")
            return

        print("find lvl 1 categories:")
        print(category_text_list)

        category_list = list()
        for index in range(0, len(category_link_list)):
            category_list.append((category_text_list[index], category_link_list[index]))

        parallel_template = ParallelTemplate(5)
        sub_category_data_list = parallel_template.run(cls.fetch_sub_category, category_list)

        with open("ku_meta.txt", "w", encoding="utf-8") as fp:
            fp.write(json.dumps(sub_category_data_list))

    @classmethod
    def fetch_sub_category(cls, category):
        # go into category to find sub-category info
        category_link = category[1]
        category_text = category[0]

        sub_category_data_list = list()

        if category_text in cls.category_black_list:
            return []

        soup_obj = HttpUtils.get(cls.amazon_base_url + category_link, headers=cls.amazon_headers)

        sub_category_text_list = HttpUtils.get_contents(soup_obj,
                                                        "div.sg-col-inner li.s-navigation-indent-2 span a span")
        sub_category_link_list = HttpUtils.get_attrs(soup_obj,
                                                     "div.sg-col-inner li.s-navigation-indent-2 span a",
                                                     "href")

        if len(sub_category_link_list) != len(sub_category_text_list):
            print("ERROR: Sub-category number not correct")
            return []

        # no sub-category
        if len(sub_category_link_list) == 0:
            sub_category_text_list = [category_text]
            sub_category_link_list = [category_link]

        print("find lvl 2 categories for %s" % category_text)
        print(sub_category_text_list)

        # find sub-category page number
        for sub_index in range(0, len(sub_category_link_list)):
            sub_category_link = sub_category_link_list[sub_index]
            sub_category_text = sub_category_text_list[sub_index]
            soup_obj = HttpUtils.get(cls.amazon_base_url + sub_category_link, headers=cls.amazon_headers)
            page_info = HttpUtils.get_contents(soup_obj, "ul.a-pagination li.a-disabled")
            if len(page_info) == 2:
                max_page_num = page_info[1]
            elif len(page_info) == 0:
                # 没有分页
                max_page_num = 1
            else:
                # 5页以内
                max_page_num = HttpUtils.get_contents(soup_obj, "ul.a-pagination li.a-normal a")[-1]

            print("cat=%s, sub-cat=%s, page=%s" % (category_text, sub_category_text, max_page_num))
            sub_category_data_list.append((category_text, sub_category_text, sub_category_link, max_page_num))

        return sub_category_data_list

    @classmethod
    def crawl_book(cls):
        with open("ku_book.txt", "r", encoding="utf-8") as fp:
            if fp.readline():
                # already has data, skip
                return

        with open("ku_meta.txt", "r", encoding="utf-8") as fp:
            line = fp.readline()
            meta_info = json.loads(line)

        sub_category_meta_list = list()
        # loop and remove empty list
        for meta in meta_info:
            for sub_meta in meta:
                sub_category_meta_list.append(sub_meta)

        parallel_template = ParallelTemplate(20)
        ku_book_title_list = parallel_template.run(cls.crawl_sub_category_book, sub_category_meta_list)

        with open("ku_book.txt", "w", encoding="utf-8") as fp:
            fp.write(json.dumps(ku_book_title_list))

    @classmethod
    def crawl_sub_category_book(cls, sub_category_meta):
        ku_book_title_list = list()

        category_name = sub_category_meta[0]
        sub_category_name = sub_category_meta[1]
        sub_category_link = cls.amazon_base_url + sub_category_meta[2]
        page_num = int(sub_category_meta[3])

        for page in range(1, page_num + 1):
            print("reading cat=%s,sub-cat=%s,page=%s" % (category_name, sub_category_name, page))
            url = sub_category_link.split("%page=")[0] + "&page=" + str(page)
            soup_obj = HttpUtils.get(url, headers=cls.amazon_headers)

            if soup_obj is None:
                print("blocked?")
                break

            title_list = HttpUtils.get_contents(soup_obj,
                                                "div.s-result-list div.sg-col-inner h2.a-size-mini span.a-size-medium")
            current_page_title_list = list()
            for title in title_list:
                # remove meta info
                title = title.split("(")[0].split("（")[0].split("【")[0]
                ku_book_title_list.append(title)
                current_page_title_list.append(title)

            print(current_page_title_list)
            sleep(random() * 0.5 + 0.5)

        return ku_book_title_list

    @classmethod
    def crawl_book_rank(cls):

        existing_book_titles = list()
        with open("ku_book_rank.txt", "r", encoding="utf-8") as fp:
            line = fp.readline()
            book_rank_json = json.loads(line)
            for titles in book_rank_json.keys():
                existing_book_titles.append(titles)

        existing_book_titles = list(set(existing_book_titles))

        book_titles = list()
        with open("ku_book.txt", "r", encoding="utf-8") as fp:
            line = fp.readline()
            book_titles_list = json.loads(line)
            for titles in book_titles_list:
                book_titles.extend(list(set(titles).difference(set(existing_book_titles))))

            # de-duplicate
            book_titles = list(set(book_titles))

        # batch mode, 1000 per batch
        batch = list()
        size = len(book_titles)
        batch_size = 100
        round = int(size / batch_size)
        for i in range(0, round):
            batch.append(book_titles[i * batch_size: (i + 1) * batch_size])
        batch.append(book_titles[round * batch_size: size - 1])

        douban_base_url = "https://api.douban.com/v2/book/search?q=%s&start=0&count=5&apikey=0b2bdeda43b5688921839c8ecb20399b"

        round_cnt = 0
        for single_batch in batch:
            round_cnt += 1
            requests = list()
            for book_title in single_batch:
                requests.append(
                    HttpReq(douban_base_url % urllib.parse.quote(book_title), cls.douban_headers, raw=True,
                            post_func=cls.crawl_book_rank_batch_post, extra_info=book_title))
            books_rank = AsyncHttpHelper.get(requests)
            cnt = 0
            for book_rank in books_rank:
                if book_rank == ():
                    cnt += 1
                else:
                    book_rank_json[book_rank[0]] = (book_rank[1], book_rank[2])

            if cnt == batch_size:
                print("Looped " + str(round_cnt * batch_size))
                # nothing found, ip blocked
                print("blocked")
                break

        with open("ku_book_rank.txt", "w", encoding="utf-8") as fp:
            fp.write(json.dumps(book_rank_json))

    @classmethod
    def crawl_book_rank_batch_post(cls, *data):
        book_title = data[0].extra_info
        json_obj = data[1]
        if not json_obj:
            return ()

        data = json.loads(json_obj)
        cnt = data["count"]
        if cnt == 0:
            # cannot find any book with this title
            return ()

        num_rater = 0
        rating_avg = 0
        for book in data["books"]:
            if book["rating"]["numRaters"] > num_rater:
                num_rater = book["rating"]["numRaters"]
                rating_avg = data["books"][0]["rating"]["average"]

        print("%s - %s -%s" % (book_title, num_rater, rating_avg))
        return book_title, num_rater, rating_avg

    @classmethod
    def sort_book(cls):
        books_list = list()
        with open("ku_book_rank.txt", "r", encoding="utf-8") as fp:
            line = fp.readline()
            books = json.loads(line)
            for (k, v) in books.items():
                books_list.append(Book(title=k, people=v[0], rating=float(v[1])))
                # books = json.loads(line, object_hook=Book.revert)

        books_list.sort(key=lambda x: (5 ** x.rating) * (x.people ** 0.7), reverse=True)

        for book in books_list[:500]:
            print(book)


class Book:
    title = ""
    rating = 0
    people = 0

    def __init__(self, title, rating, people):
        self.title = title
        self.rating = rating
        self.people = people

    def convert(std):
        return {'title': std.title,
                'rating': std.rating,
                'people': std.people,
                }

    def revert(std):
        return Book(std['title'], std['rating'], std['people'])

    def __str__(self):
        return "%s - %s - %s" % (self.title, self.people, self.rating)


if __name__ == "__main__":
    Crawler.start()
