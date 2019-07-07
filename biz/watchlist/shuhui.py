import json

from core.db import Cache
from core.emailSender import EmailSender
from util.utils import HttpUtils


class ShuHuiWatchDog:
    BUCKET_NAME_PREFIX = "SHU_HUI_COMIC_"

    INVALID_CHAPTER_NUM = -1

    @staticmethod
    def check_and_notify(animation_id):
        bucket_name = ShuHuiWatchDog.BUCKET_NAME_PREFIX + str(animation_id)
        previous_chapter_num = Cache().get(bucket_name)
        if previous_chapter_num is None:
            previous_chapter_num = -1
        comic_name, current_chapter_num = ShuHuiWatchDog.get_max_chapter_num(animation_id)

        if current_chapter_num == ShuHuiWatchDog.INVALID_CHAPTER_NUM:
            EmailSender.send("错误：鼠绘-" + comic_name, "无法抓取最新章节号")
        elif current_chapter_num > previous_chapter_num:
            EmailSender.send("鼠绘-{0}更新啦".format(comic_name), "最新章节号是" + str(current_chapter_num))
            Cache().set(bucket_name, current_chapter_num)

    @staticmethod
    def get_max_chapter_num(animation_id):
        # not sure what this ver means, could be any value and still works
        verification = "3b230956"

        response = HttpUtils.get(
            "https://prod-api.ishuhui.com/ver/{0}/anime/detail?id={1}&type=comics&.json".format(verification,
                                                                                                animation_id),
            return_raw=True)
        if response.status_code != 200 and response.status_code != 301:
            return ShuHuiWatchDog.INVALID_CHAPTER_NUM
        else:
            comic_data = json.loads(response.text)
            max_chapter_num = int(comic_data["data"]["comicsIndexes"]["1"]["maxNum"])
            comic_name = comic_data["data"]["name"]
            return comic_name, max_chapter_num


if __name__ == "__main__":
    ShuHuiWatchDog.check_and_notify(1)
