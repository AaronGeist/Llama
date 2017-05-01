import sys

from biz.putao import FreeFeedAlert, MagicPointChecker, UploadMonitor
from biz.rpi import CpuTemperature, Memory

cmd_map = {
    "feed_check": FreeFeedAlert().check,
    "mp_check": MagicPointChecker().check,
    "mp_monitor": MagicPointChecker().monitor,
    "up_monitor": UploadMonitor().monitor,
    "cpu_temp_monitor": CpuTemperature().monitor,
    "memory_monitor": Memory().monitor,
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
        cmd_map[cmd]()
    else:
        usage()
