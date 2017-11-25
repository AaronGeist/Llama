import os

from core.seedManager import SeedManager
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
        size_of_seeds = SeedManager.load_seeds_total_size_per_location()
        for info in os.popen("df -lm|grep \"/dev/v\"|awk '{print $1,$4}'").read().split("\n"):
            if info != "":
                data = info.split(' ')
                disk_name = data[0]
                disk_size = float(data[1])
                download_folder = cls.disk_name_map[disk_name]["location"]
                # in some cases, seed just get started to download and disk space hasn't been allocated yet
                # so need to fix it
                if download_folder in size_of_seeds:
                    disk_size = min(disk_size, cls.disk_name_map[disk_name]["size"] - size_of_seeds[download_folder])
                disk_space_in_mb[disk_name] = round(disk_size, 1)

        print("space left: " + str(disk_space_in_mb))

        return disk_space_in_mb
