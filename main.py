import sys

from biz.putao import FreeFeedAlert, MagicPointChecker, UploadMonitor

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: must have one argument")
        quit()

    target = sys.argv[1]
    if target == "feed_check":
        FreeFeedAlert().check()
    elif target == "mp_check":
        MagicPointChecker().check()
    elif target == "mp_monitor":
        MagicPointChecker().monitor()
    elif target == "up_monitor":
        UploadMonitor().monitor()

