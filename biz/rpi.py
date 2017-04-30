import os

from core.monitor import Monitor


class CpuTemperature(Monitor):
    bucket = "cpu_temperature"

    def generate_data(self):
        res = ""
        with open("/sys/class/thermal/thermal_zone0/temp") as tempFile:
            res = tempFile.read()
            res = str(float(res) / 1000)

        return res


class Memory(Monitor):
    bucket = "memory"

    def generate_data(self):
        return os.popen("free -m | grep buffers/cache | awk '{print $3}'").read()
