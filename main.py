import sys
import time

from biz.PTMaster import PTMaster
from biz.mteam import AdultAlert, UploadCheck, UserCrawl, CandidateVote, MessageReader, NormalAlert
from biz.pt.PutaoWatchDog import PuTaoWatchDog, BbsMonitor
from biz.putao import FreeFeedAlert, MagicPointChecker, UploadMonitor
from biz.rpi import CpuTemperature, Memory
from biz.taobao.SecondHand import SecondHand
from biz.weather import WeatherReport
from core.seedManager import SeedManager
from core.tts import TextToSpeech

cmd_map = {
    "pt_seed_check": PuTaoWatchDog().check,
    "pt_seed_add": PuTaoWatchDog().manual_add_seed,
    "bbs_monitor": BbsMonitor().check,
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
    "mt_normal": NormalAlert().check,
    "mt_adult": AdultAlert().check,
    "mt_adult_init": AdultAlert().init,
    "mt_add_normal": NormalAlert().add_seed,
    "mt_add": AdultAlert().add_seed,
    "mt_up_init": UploadCheck().init,
    "mt_up_check": UploadCheck().check,
    "mt_up_check_not_store": UploadCheck().check_not_store,
    "mt_user_init": UserCrawl().crawl,
    "mt_user_refresh": UserCrawl().refresh,
    "mt_user_warn": UserCrawl().warn,
    "mt_id": UserCrawl().load_by_id,
    "mt_name": UserCrawl().load_by_name,
    "mt_order": UserCrawl().order,
    "mt_vote": CandidateVote().check,
    "mt_clean": SeedManager.seed_file_clean_up,
    "mt_seed_ls": SeedManager.parse_current_seeds,
    "mt_page_ls": AdultAlert().crawl,
    "mt_msg": MessageReader().get_cmd,
    "test": PTMaster().gogogo
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
        if len(sys.argv) > 3:
            cmd_map[cmd](sys.argv[2], sys.argv[3])
        elif len(sys.argv) > 2:
            cmd_map[cmd](sys.argv[2])
        else:
            cmd_map[cmd]()
    else:
        usage()
