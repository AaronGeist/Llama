import json

import re

from core.db import Cache
from util.utils import HttpUtils


class SecondHand:
    base_url = "https://s.2.taobao.com/list/waterfall/waterfall.htm?stype=1&st_trust=1&page={pageNum}&q=wcf&ist=1"

    bucket_name_item = "XIAN_YU_ITEM"
    bucket_name_id = "XIAN_YU_ID"

    db = Cache()

    @classmethod
    def crawl_single_page(cls, page_num):
        url = cls.base_url.replace("{pageNum}", str(page_num))

        response = HttpUtils.get(url, return_raw=True)
        assert response.status_code == 200

        data = response.text.replace("({", "{").replace("})", "}")
        json_data = json.loads(data)

        items = json_data['idle']
        cls.parse_items(items)

    @classmethod
    def parse_items(cls, json_data):
        for data in json_data:
            item = cls.parse_item(data)
            cls.db.hash_set(cls.bucket_name_item, item.item_id, json.dumps(data))
            cls.db.set_add(cls.bucket_name_id, item.item_id)

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
        cls.crawl_single_page(1)


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
    site.crawl_single_page(1)
