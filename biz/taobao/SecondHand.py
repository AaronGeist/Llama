import json

import re
from time import sleep

from core.db import Cache
from util.utils import HttpUtils


class SecondHand:
    base_url = "https://s.2.taobao.com/list/waterfall/waterfall.htm?stype=1&st_trust=1&page={pageNum}&q=wcf&ist=1"

    bucket_name_item = "XIAN_YU_ITEM"
    bucket_name_id = "XIAN_YU_ID"

    bucket_name_new_id = "XIAN_YU_NEW_ID"
    bucket_name_diff_id = "XIAN_YU_DIFF_ID"
    bucket_name_diff_item = "XIAN_YU_DIFF_ITEM"

    db = Cache()

    @classmethod
    def init(cls):
        # clean up
        data = cls.db.set_get_all(cls.bucket_name_new_id)
        if data is not None:
            for i in data:
                cls.db.set_delete(cls.bucket_name_new_id, i)

        data = cls.db.set_get_all(cls.bucket_name_diff_id)
        if data is not None:
            for i in data:
                cls.db.set_delete(cls.bucket_name_diff_id, i)

        keys = cls.db.hash_get_all_key(cls.bucket_name_diff_item)
        if keys is not None:
            for i in keys:
                cls.db.hash_delete(cls.bucket_name_diff_item, i)

    @classmethod
    def crawl_single_page(cls, page_num):
        url = cls.base_url.replace("{pageNum}", str(page_num))

        response = HttpUtils.get(url, return_raw=True)
        assert response.status_code == 200

        # to make formatting valid for JSON
        data = response.text.replace("({", "{").replace("})", "}")
        json_data = json.loads(data)

        items = json_data['idle']
        cls.parse_items(items)

        return json_data['currPage'], json_data['totalPage']

    @classmethod
    def parse_items(cls, json_data):
        for data in json_data:
            item = cls.parse_item(data)

            # find new item and figure out different item
            cls.compare(item)

            # store item
            cls.db.hash_set(cls.bucket_name_item, item.item_id, json.dumps(data))
            cls.db.set_add(cls.bucket_name_id, item.item_id)

    @classmethod
    def compare(cls, item):
        if not cls.db.set_contains(cls.bucket_name_id, item.item_id):
            cls.db.set_add(cls.bucket_name_new_id, item.item_id)
        else:
            old_item_str = cls.db.hash_get(cls.bucket_name_item, item.item_id)
            old_item = cls.parse_item(json.loads(old_item_str))

            if old_item.price != item.price:
                old_item.price = str(old_item.price) + " -> " + str(item.price)
                cls.db.set_add(cls.bucket_name_diff_id, item.item_id)
                cls.db.hash_set(cls.bucket_name_diff_item, item.item_id, json.dumps(old_item))

    @classmethod
    def parse_item(cls, raw_data):
        data = raw_data['item']
        item = Item()
        item.img_url = data['imageUrl']
        item.item_url = data['itemUrl']
        item.price = data['price']
        item.provcity = data['provcity']
        item.describe = data['describe']
        item.title = data['title']
        item.user = cls.parse_user(raw_data)

        m = re.search("id=(\d+)&", item.item_url)
        assert m is not None and m
        item.item_id = m.group(1)

        return item

    @classmethod
    def parse_user(cls, data):
        data = data['user']
        user = User()
        user.nick_name = data['userNick']
        user.vip_lvl = data['vipLevel']
        user.yellow_seller = data['yellowSeller']

        return user

    @classmethod
    def crawl(cls):
        cls.init()
        cls.crawl_pages()

    @classmethod
    def crawl_pages(cls):
        page_num = 1
        previous_page = -1
        current_page = 0

        # when returned page doesn't increase, then stop
        while previous_page != current_page:
            print("######## parsing page " + str(page_num) + " ########")
            previous_page = current_page
            current_page, total_page = cls.crawl_single_page(page_num)
            page_num += 1
            sleep(15)

    @classmethod
    def clean_up(cls):
        cls.init()
        # clean up
        data = cls.db.set_get_all(cls.bucket_name_id)
        if data is not None:
            for i in data:
                cls.db.set_delete(cls.bucket_name_id, i)

        keys = cls.db.hash_get_all_key(cls.bucket_name_item)
        if keys is not None:
            for i in keys:
                cls.db.hash_delete(cls.bucket_name_item, i)


class User:
    nick_name = ""
    vip_lvl = 0
    yellow_seller = False


class Item:
    item_id = ""
    img_url = ""
    item_url = ""
    price = 0
    provcity = ""
    describe = ""
    title = ""


if __name__ == "__main__":
    site = SecondHand()
    site.crawl()
