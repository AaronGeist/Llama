import json
import os
import time

from core.tts import TextToSpeech
from util.utils import HttpUtils


class WeatherReport:
    @classmethod
    def load_shanghai_today(cls):
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "d1.weather.com.cn",
            "Referer": "http://www.weather.com.cn/weather1d/101020100.shtml"
        }

        res = HttpUtils.get("http://d1.weather.com.cn/sk_2d/101020100.html?_=%d" % round(time.time() * 1000),
                            headers=headers,
                            return_raw=True)
        html = res.content.decode("utf-8")
        data = json.loads(html.replace("var dataSK = ", ""))

        return "今天%s，当前气温%s摄氏度，%s%s, aqi指数%s" % (
            data.get("weather"), data.get("temp"), data.get("WD"), data.get("WS"),
            data.get("aqi"))

    @classmethod
    def report_shanghai_today(cls):
        weather = cls.load_shanghai_today()
        os.popen("rm tts.mp3")
        TextToSpeech.convert(weather, "tts.mp3")
        os.popen("mplayer tts.mp3")


if __name__ == "__main__":
    WeatherReport.load_shanghai_today()
