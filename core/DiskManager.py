import os

from util.config import Config


class DiskManager:
    disk_name_map = dict()
    download_folder_map = dict()

    @classmethod
    def parse_info(cls):
        if len(cls.disk_name_map) == 0:
            all_data = Config.get("disk_info")
            for data in all_data:
                cls.disk_name_map[data["name"]] = data
                cls.download_folder_map[data["location"]] = data

    @classmethod
    def name2location(cls):
        cls.parse_info()
        result = dict()
        for disk_name in cls.disk_name_map:
            result[disk_name] = cls.disk_name_map[disk_name]["location"]
        return result

    @classmethod
    def location2name(cls):
        cls.parse_info()
        result = dict()
        for folder in cls.download_folder_map:
            result[folder] = cls.download_folder_map[folder]["name"]
        return result

    @classmethod
    def get_disk_space_left(cls):
        cls.parse_info()

        disk_space_in_mb = dict()
        for info in os.popen("df -lm|grep \"/dev/v\"|awk '{print $1,$4}'").read().split("\n"):
            if info != "":
                data = info.split(' ')
                disk_name = data[0]
                disk_size = float(data[1])
                disk_space_in_mb[disk_name] = round(disk_size, 1)

        return disk_space_in_mb
