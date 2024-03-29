# -*- coding:utf-8 -*-

import os

from core.emailsender import EmailSender
from core.monitor import Monitor
from util.config import Config


class CpuTemperature(Monitor):
    def get_bucket(self):
        return "cpu_temperature"

    def generate_data(self):
        with open("/sys/class/thermal/thermal_zone0/temp") as tempFile:
            res = tempFile.read()
            res = float(res) / 1000

        return res

    def alert(self, data):
        if data >= Config.get("cpu_temperature_threshold"):
            EmailSender.send(u"CPU 发烧啦: " + str(data), "")


class Memory(Monitor):
    def get_bucket(self):
        return "memory"

    def generate_data(self):
        return os.popen("free -m | grep buffers/cache | awk '{print $3}'").read().strip()


class Thread(Monitor):
    def get_bucket(self):
        return "thread"

    def generate_data(self):
        return os.popen("top|head -1|awk '{print $8}'").read().strip()
