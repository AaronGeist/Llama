import json
import time

from core.tts import TextToSpeech
from util.utils import HttpUtils


class WeatherReport:
    city_code = "101020100"  # shanghai

    @classmethod
    def load_weather_data(cls):
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "d1.weather.com.cn",
            "Referer": "http://www.weather.com.cn/weather1d/%s.shtml" % cls.city_code
        }

        res = HttpUtils.get("http://d1.weather.com.cn/sk_2d/%s.html?_=%d" % (cls.city_code, round(time.time() * 1000)),
                            headers=headers,
                            return_raw=True)
        html = res.content.decode("utf-8")
        data = json.loads(html.replace("var dataSK = ", ""))

        res = HttpUtils.get(
            "http://d1.weather.com.cn/dingzhi/%s.html?_=%d" % (cls.city_code, round(time.time() * 1000)),
            headers=headers,
            return_raw=True)

        html = res.content.decode("utf-8")
        html2 = html.replace("var cityDZ101020100 =", "").replace(";var alarmDZ101020100 ={\"w\":[]}", "")
        data2 = json.loads(html2).get("weatherinfo")

        return "今天%s，最高气温%s，最低气温%s，%s%s, 当前气温%s，aqi指数%s，相对湿度%s" % (
            data2.get("weather"), data2.get("temp"), data2.get("tempn"), data2.get("wd"), data2.get("ws"),
            data.get("temp"), data.get("aqi"), data.get("sd"))

    @classmethod
    def report_weather(cls):
        weather = cls.load_weather_data()
        TextToSpeech.convert_and_play(weather)


if __name__ == "__main__":
    print(WeatherReport.load_weather_data())
