import json
from queue import Queue
import redis

import time

from core.entity import ZhiHuUser
from util.utils import HttpUtils


class Crawler:
    site = None
    cache = None
    users = {}

    to_parse_queue = Queue()

    # constants
    bucket_name = "zhihu_users"

    @classmethod
    def init_cache(cls):
        if cls.cache is None:
            pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
            cls.cache = redis.StrictRedis(connection_pool=pool)

    @classmethod
    def parse_single(cls, url_token):
        if cls.is_parsed(url_token):
            return

        print("parsing user: " + url_token)
        url = "https://www.zhihu.com/people/%s/followers" % url_token
        users = cls.parse_users(url)

        current_user_dict = users[url_token]
        assert current_user_dict is not None
        current_user = cls.dict_to_user(current_user_dict)
        cls.store_user(current_user)

        # 20 followers per page
        page_num = int(current_user.follower_cnt / 20) + 1
        for i in range(1, page_num + 1):
            print("parsing user follower page " + str(i))
            page_url = "https://www.zhihu.com/people/%s/followers?page=%d" % (url_token, i)
            users = cls.parse_users(page_url)
            for user_dict in users.values():
                user = cls.dict_to_user(user_dict)
                cls.store_user(user)
                cls.to_parse_queue.put(user)

        for key in cls.users.keys():
            print(key)

    @classmethod
    def parse(cls, init_url_token):
        cls.init_cache()
        cls.parse_single(init_url_token)
        while True:
            user = cls.to_parse_queue.get(timeout=10)
            cls.parse_single(user.url_token)
            time.sleep(10)
            if len(cls.users) > 10000:
                break

    @classmethod
    def parse_users(cls, url):
        soup_obj = HttpUtils.get(url)
        if soup_obj is None:
            print(">>>>>> Fail to parse " + url)
            return None

        data_state = HttpUtils.get_attr(soup_obj, "#data", "data-state")
        data_map = json.loads(data_state)
        return data_map['entities']['users']

    @classmethod
    def dict_to_user(cls, user_dict):
        assert user_dict is not None
        user = ZhiHuUser()
        user.id = user_dict.get("id")
        user.answer_cnt = user_dict.get('answerCount')
        user.question_cnt = user_dict.get('questionCount')
        user.following_cnt = user_dict.get('followingCount')
        user.follower_cnt = user_dict.get('followerCount')
        user.thank_to_cnt = user_dict.get('thankToCount')
        user.thanked_cnt = user_dict.get('thankedCount')
        user.avatar_url = user_dict.get('avatarUrl')
        user.name = user_dict.get('name')
        user.headline = user_dict.get('headline')
        user.gender = user_dict.get('gender')
        user.url = user_dict.get('url')
        user.locations = user_dict.get('locations')
        user.educations = user_dict.get('educations')
        user.employments = user_dict.get('employments')
        user.url_token = user_dict.get('urlToken')

        return user

    @classmethod
    def store_user(cls, user):
        if user.url_token in cls.users.keys():
            print("Duplicated " + user.name)
        else:
            print("Add user " + user.name)
            cls.users[user.url_token] = user
            cls.cache.hset()

    @classmethod
    def is_parsed(cls, unique_key):
        return unique_key in cls.users.keys()


if __name__ == "__main__":
    Crawler.parse('he-tao-62-44')
