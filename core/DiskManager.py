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
        print(cls.disk_name_map)
        print(cls.download_folder_map)

    @classmethod
    def get_unused_space_size(cls):
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
                if disk_name in size_of_seeds:
                    disk_size = min(disk_size, cls.disk_name_map[disk_name]["size"] - size_of_seeds[download_folder])
                disk_space_in_mb[disk_name] = disk_size

        print(disk_space_in_mb)

        return disk_space_in_mb
