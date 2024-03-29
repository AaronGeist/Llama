import os

from core.emailsender import EmailSender
from util.config import Config


class IpNotifier:
    storage_file = Config.get("ip_history_file")

    @classmethod
    def check_change(cls):
        previous_ip = ""

        if os.path.exists(cls.storage_file):
            with open(cls.storage_file, "r") as fp:
                previous_ip = fp.readline().strip()

        output = os.popen("curl ip.sb")
        current_ip = output.read().strip()

        if previous_ip != current_ip:
            with open(cls.storage_file, "w") as fp:
                fp.writelines(current_ip)

            print("old[%s], new[%s]" % (previous_ip, current_ip))
            EmailSender.send(u"IP变更", "最新IP: " + str(current_ip))


if __name__ == "__main__":
    IpNotifier.check_change()
