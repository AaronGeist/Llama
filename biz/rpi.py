import os

from core.emailSender import EmailSender
from core.monitor import Monitor
from util.config import Config


class CpuTemperature(Monitor):
    def get_bucket(self):
        return "cpu_temperature"

    def generate_data(self):
        res = ""
        with open("/sys/class/thermal/thermal_zone0/temp") as tempFile:
            res = tempFile.read()
            res = str(float(res) / 1000)

        return res

    def alert(self, data):
        if data >= Config.get("cpu_temperature_threshold"):
            EmailSender.send(u"CPU 发烧啦: " + str(data), "")


class Memory(Monitor):
    def get_bucket(self):
        return "memory"

    def generate_data(self):
        return os.popen("free -m | grep buffers/cache | awk '{print $3}'").read()
