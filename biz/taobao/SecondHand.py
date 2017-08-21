import json

import re

from core.db import Cache
from util.utils import HttpUtils


class SecondHand:
    base_url = "https://s.2.taobao.com/list/waterfall/waterfall.htm?stype=1&st_trust=1&page={pageNum}&q=wcf&ist=1"

    bucket_name = "XIAN_YU"

    db = Cache()

    def crawl_single_page(self, page_num):
        url = self.base_url.replace("{pageNum}", str(page_num))

        response = HttpUtils.get(url, return_raw=True)
        assert response.status_code == 200
        print(response.text)
        data = response.text.replace("({", "{").replace("})", "}")
        json_data = json.loads(data)

        items = json_data['idle']
        self.parse_items(items)

    def parse_items(self, json_data):
        for data in json_data:
            item = self.parse_item(data)
            self.db.set(item.item_id, item)
            self.db.append(self.bucket_name, item.item_id)

    def parse_item(self, raw_data):
        data = raw_data['item']
        item = Item()
        item.img_url = data['imageUrl']
        item.item_url = data['itemUrl']
        item.price = data['price']
        item.provcity = data['provcity']
        item.describe = data['describe']
        item.title = data['title']
        item.user = self.parse_user(raw_data)

        m = re.search("id=(\d+)&", item.item_url)
        assert m is not None and m
        item.item_id = m.group(1)

        return item

    def parse_user(self, data):
        data = data['user']
        user = User()
        user.nick_name = data['userNick']
        user.vip_lvl = data['vipLevel']
        user.yellow_seller = data['yellowSeller']

        return user


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
