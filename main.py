import sys

from biz.putao import FreeFeedAlert, MagicPointChecker
from core.emailSender import EmailSender

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        if target == "feed_check":
            FreeFeedAlert().check()
        elif target == "mp_check":
            MagicPointChecker().check()
        elif target == "mp_monitor":
            MagicPointChecker().monitor()
