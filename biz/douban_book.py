import json
from queue import Queue
from random import random
from time import sleep

from core.login import Login
from util.utils import HttpUtils


class Crawler(Login):
    task_pool = Queue()
    process_thread = None
    tag = "小说"

    people_threshold = 1000

    @classmethod
    def start(cls):
        cls.crawl_book()
        cls.sort_book()

    @classmethod
    def crawl_book(cls):

        tag_source_url = "https://book.douban.com/tag/"
        soup_obj = HttpUtils.get(tag_source_url)

        tags = HttpUtils.get_contents(soup_obj, "div.article tr td a")

        tags = ['小说', '外国文学', '文学', '中国文学', '经典', '日本文学', '古典文学', '王小波', '当代文学',
                '钱钟书', '外国名著', '推理', '绘本', '青春', '东野圭吾', '科幻', '言情', '悬疑',
                '奇幻', '韩寒', '推理小说', '阿加莎·克里斯蒂', '科幻小说', '魔幻', '历史', '心理学', '哲学', '传记', '文化', '社会学', '艺术', '设计', '社会',
                '政治', '建筑', '宗教', '电影',
                '政治学', '数学', '中国历史', '回忆录', '思想', '国学', '人物传记', '人文', '音乐', '艺术史', '绘画', '戏剧', '西方哲学', '二战', '军事', '佛教',
                '近代史', '考古', '自由主义', '美术', '爱情', '旅行', '成长', '生活', '心理', '励志', '摄影', '教育', '游记', '灵修',
                '健康', '情感', '两性', '人际关系', '手工', '养生', '家居', '自助游', '经济学', '管理', '经济', '商业', '金融', '投资', '营销', '理财',
                '创业', '广告', '股票', '企业史', '策划', '科普', '互联网', '编程', '科学', '交互设计', '用户体验', '算法', '科技', 'web', 'UE', '交互',
                '通信', 'UCD', '神经网络', '程序']
        print(tags)

        book_shelf = dict()
        for tag in tags:
            for page in range(0, 10):
                url = "https://book.douban.com/tag/%s?start=%d&type=T" % (tag, page * 20)
                soup_obj = HttpUtils.get(url)

                if soup_obj is None:
                    print("blocked?")
                    break

                print(tag, page)
                books_obj = soup_obj.select("#subject_list ul > li")

                if len(books_obj) == 0:
                    break

                for book_obj in books_obj:
                    try:
                        title = HttpUtils.get_attr(book_obj, "h2 a", "title")
                        rating = float(HttpUtils.get_content(book_obj, "span.rating_nums"))
                        people = int(
                            HttpUtils.get_content(book_obj, "span.pl").strip().replace("人评价", "").replace("(",
                                                                                                          "").replace(
                                ")",
                                ""))

                        if people > cls.people_threshold:
                            if title in book_shelf:
                                book_shelf[title].tag.append(tag)
                            else:
                                book_shelf[title] = Book(title, rating, people, [tag])
                    except Exception as e:
                        pass

                sleep(random() * 0.5 + 0.5)

        books = list(book_shelf.values())

        with open("douban_book_raw.txt", "w") as fp:
            fp.write(json.dumps(books, default=Book.convert))

    @classmethod
    def sort_book(cls):
        with open("douban_book_raw.txt", "r") as fp:
            line = fp.read()

        books = json.loads(line, object_hook=Book.revert)

        books.sort(key=lambda x: (5 ** x.rating) * (x.people ** 0.7), reverse=True)

        with open("douban_book_rating.txt", "w") as fp:
            for book in books:
                fp.write("%s\t%s\t%s\t%s\n" % (book.title, book.rating, book.people, book.tag))


class Book:
    title = ""
    rating = 0
    people = 0
    tag = []

    def __init__(self, title, rating, people, tag):
        self.title = title
        self.rating = rating
        self.people = people
        self.tag = tag

    def convert(std):
        return {'title': std.title,
                'rating': std.rating,
                'people': std.people,
                'tag': std.tag
                }

    def revert(std):
        return Book(std['title'], std['rating'], std['people'], std['tag'])


if __name__ == "__main__":
    Crawler.start()
