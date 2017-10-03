import sys
import time

from biz.mteam import AdultAlert, UploadCheck, UserCrawl
from biz.putao import FreeFeedAlert, MagicPointChecker, UploadMonitor
from biz.rpi import CpuTemperature, Memory
from biz.taobao.SecondHand import SecondHand
from biz.weather import WeatherReport
from core.tts import TextToSpeech

cmd_map = {
    "feed_check": FreeFeedAlert().check,
    "mp_check": MagicPointChecker().check,
    "mp_monitor": MagicPointChecker().monitor,
    "up_monitor": UploadMonitor().monitor,
    "cpu_temp_monitor": CpuTemperature().monitor,
    "memory_monitor": Memory().monitor,
    "weather": WeatherReport.report_shanghai_today,
    "tts": TextToSpeech.convert_and_play,
    "second": SecondHand.crawl,
    "second_reset": SecondHand.clean_up,
    "mt_adult": AdultAlert().check,
    "mt_adult_init": AdultAlert().init,
    "mt_up_check": UploadCheck().check,
    "mt_user_init": UserCrawl().crawl,
    "mt_user_refresh": UserCrawl().refresh
}


def usage():
    print("please choose argument below:")
    for cmd in cmd_map.keys():
        print(" -- " + cmd)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: must have one argument")
        usage()
        quit()

    cmd = sys.argv[1]
    if cmd in cmd_map.keys():
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print("%s Processing %s" % (now, cmd))
        if len(sys.argv) > 2:
            cmd_map[cmd](sys.argv[2])
        else:
            cmd_map[cmd]()
        print("%s Processing %s done" % (now, cmd))
    else:
        usage()
