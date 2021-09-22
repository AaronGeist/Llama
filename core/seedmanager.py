import datetime
import json
import os
import time
from dateutil import parser

from core.diskmanager import DiskManager
from core.emailsender import EmailSender
from core.enigma import Enigma
from model.seed import TransmissionSeed
from util.config import Config
from util.utils import HttpUtils


class SeedManager:
    # index indicates the percentage of download, 0 -> 0%, 1 -> 10%
    up_speed_threshold = [0, 0, 0, 100, 100, 300, 300, 400, 400, 400, 400]

    # index indicates the size in GB, 0 -> 0GB
    size_factor = [1, 1, 1.1, 1.2, 1.3, 1.3, 1.4, 1.6, 2, 2, 2, 2.5, 2.5, 2.5, 2.5, 3.0, 3.0, 3.0, 3.0]

    # index indicates the percentage of download, 0 -> 0%, 1 -> 10%
    down_avg_speed_threshold = [0, 100, 200, 300, 400, 500, 500, 500, 500, 500, 500]

    init_disk_space = 23 * 1024

    @classmethod
    def check_disks_space(cls):
        cls.seed_file_clean_up()
        disk_space_map = DiskManager.get_disk_space_left()
        print("original space left: " + str(disk_space_map))
        disk_name_map = DiskManager.disk_name_map
        size_of_seeds = cls.load_seeds_total_size_per_location()
        for disk_name in disk_space_map:
            location = disk_name_map[disk_name]["location"]
            if location in size_of_seeds:
                # in some cases, seed just get started to download and disk space hasn't been allocated yet
                # so need to fix it
                disk_space_map[disk_name] = round(min(disk_space_map[disk_name],
                                                      disk_name_map[disk_name]["size"] - size_of_seeds[location]),
                                                  1)

        print("fixed space left: " + str(disk_space_map))

        return disk_space_map

    @classmethod
    def seed_file_clean_up(cls):
        files = DiskManager.find_all_files()
        seeds = cls.parse_current_seeds(True)

        seeds_path = list(map(lambda seed: DiskManager.append_delimiter_if_miss(seed.location) + seed.name, seeds))

        file_to_be_removed = list(
            filter(lambda file: len(list(filter(lambda seed_path: file.startswith(seed_path), seeds_path))) == 0,
                   files))

        print("remove " + str(file_to_be_removed))
        for file in file_to_be_removed:
            os.popen("rm -rf '{0}'".format(file))

    @classmethod
    def check_bandwidth(cls):
        resp = os.popen(
            "curl -H 'API-Key: %s' https://api.vultr.com/v1/server/list" % Enigma.decrypt(Config.get("vultr_api_key"))).read()
        json_data = json.loads(resp)
        info_dict = list(json_data.values())[0]
        current_bandwidth_gb = info_dict['current_bandwidth_gb']
        allowed_bandwidth_gb = info_dict['allowed_bandwidth_gb']

        print("current_bw=%s,allowed_bw=%s", str(current_bandwidth_gb), str(allowed_bandwidth_gb))

        return current_bandwidth_gb, allowed_bandwidth_gb

    @classmethod
    def add_seed(cls, seed, location=None):
        torrent_file = "%s.torrent" % seed.id
        if not os.path.exists(torrent_file):
            print("Add seed fail, cannot find seed file: " + str(seed))
            return
        if location is None:
            os.popen("transmission-remote -a %s" % torrent_file)
        else:
            os.popen("transmission-remote -a %s -w %s" % (torrent_file, location))
        time.sleep(2)
        os.popen("rm -f %s" % torrent_file)
        print("Add seed to transmission: %s @ %s" % (str(seed), location))

    @classmethod
    def load_avg_speed(cls):
        print("Start load avg speed\n")
        times = 30
        interval = 1

        statistics = {}
        for i in range(times):
            seeds = cls.fast_parse_current_seeds(False)
            for seed in seeds:
                if seed.id not in statistics.keys():
                    statistics[seed.id] = seed
                else:
                    item = statistics[seed.id]
                    item.up += seed.up
                    item.down += seed.down
            time.sleep(interval)

        for key in statistics.keys():
            statistics[key].up = round(statistics[key].up / times, 2)
            statistics[key].down = round(statistics[key].down / times, 2)

        print("Finish load avg speed\n")
        return statistics.values()

    @classmethod
    def parse_current_seeds(cls, print_log=True):
        seeds = []
        cmd_result = os.popen("transmission-remote -l").read()
        lines = cmd_result.split("\n")[1: -2]  # remove first and last line

        now = datetime.datetime.now()
        for line in lines:
            seed = TransmissionSeed()
            seeds.append(seed)

            data = line.split()
            seed.id = data[0].replace("*", "")
            cmd_result = os.popen("transmission-remote -t {0} -i".format(seed.id)).read()
            seed_details = cmd_result.split("\n")

            for detail in seed_details:
                if detail.startswith("  Name: "):
                    seed.name = detail.replace("  Name: ", "")
                elif detail.startswith("  State: "):
                    seed.status = detail.replace("  State: ", "")
                elif detail.startswith("  Percent Done:"):
                    seed.done = float(detail.replace("  Percent Done: ", "").replace('%', ''))
                elif detail.startswith("  ETA: "):
                    seed.ETA = detail.replace("  ETA: ", "").replace(" ", "").split("(")[0]
                elif detail.startswith("  Download Speed: "):
                    seed.down = HttpUtils.pretty_format(
                        detail.replace("  Download Speed: ", "").replace(" ", "").split("/s")[0], "KB")
                elif detail.startswith("  Upload Speed: "):
                    seed.up = HttpUtils.pretty_format(
                        detail.replace("  Upload Speed: ", "").replace(" ", "").split("/s")[0], "KB")
                elif detail.startswith("  Total size: "):
                    seed.size = HttpUtils.pretty_format(
                        detail.replace("  Total size: ", "").replace(" ", "").split("(")[0], "MB")
                elif detail.startswith("  Ratio: "):
                    ratio_str = detail.replace("  Ratio: ", "")
                    if ratio_str == "None":
                        seed.ratio = 0.0
                    else:
                        seed.ratio = float(ratio_str)
                elif detail.startswith("  Date added: "):
                    start_time = parser.parse(detail.replace("  Date added: ", "").strip())
                    seed.since = (now - start_time).seconds
                elif detail.startswith("  Downloaded: "):
                    seed.done_size = HttpUtils.pretty_format(
                        detail.replace("  Downloaded: ", ""), "KB")
                elif detail.startswith("  Location: "):
                    seed.location = detail.replace("  Location: ", "")

        if print_log:
            for seed in seeds:
                print(seed)

        return seeds

    @classmethod
    def fast_parse_current_seeds(cls, print_log=True):
        seeds = []
        cmd_result = os.popen("transmission-remote -l").read()
        lines = cmd_result.split("\n")[1: -2]  # remove first and last line

        for line in lines:
            seed = TransmissionSeed()
            seeds.append(seed)

            data = line.split()
            seed.id = data[0].replace("*", "")
            seed.name = "N/A"
            if data[2] == "None":
                seed.status = "Idle"
                seed.done = 0
                seed.down = 0
                seed.up = 0
                seed.ratio = 0
            else:
                seed.status = data[8]
                seed.done = float(data[1].replace('%', ''))
                seed.down = float(data[6])
                seed.up = float(data[5])
                seed.ratio = float(data[7])

        if print_log:
            for seed in seeds:
                print(seed)

        return seeds

    @classmethod
    def load_seeds_total_size_per_location(cls):
        seeds = cls.parse_current_seeds()
        total_size = dict()
        for seed in seeds:
            if seed.location not in total_size:
                total_size[seed.location] = 0
            total_size[seed.location] += seed.size
        return total_size

    @classmethod
    def try_add_seeds(cls, new_seeds):
        print("-" * 20)
        print("\nstart try add seeds\n")

        success_seeds = []
        fail_seeds = []
        max_retry = 1

        cls.fast_remove_bad_seeds()

        disk_location_to_name_map = DiskManager.location2name()
        disk_space_map = cls.check_disks_space()

        for new_seed in new_seeds:
            disk_space_map_temp = disk_space_map.copy()
            retry = 0
            while retry < max_retry:
                target_disk = None
                for disk_name in disk_space_map_temp.keys():
                    disk_space_map_temp[disk_name] = round(disk_space_map_temp[disk_name] - new_seed.size, 1)
                    print(
                        "%s space left after adding new seed: %sMB" % (disk_name, str(disk_space_map_temp[disk_name])))

                    if disk_space_map_temp[disk_name] > 100:
                        target_disk = disk_name
                        print("find disk without removing seed: " + target_disk)
                        break

                removal_list = dict()
                if target_disk is None:
                    # try to remove seed
                    total_size, bad_seeds = cls.find_bad_seeds()
                    for bad_seed in bad_seeds:
                        disk_name = disk_location_to_name_map[bad_seed.location]
                        if disk_name not in removal_list:
                            removal_list[disk_name] = list()
                        removal_list[disk_name].append(bad_seed)
                        disk_space_map_temp[disk_name] += bad_seed.size
                        print("if remove seed %s @ %s, then space=%s" % (
                            str(bad_seed.id), bad_seed.location, str(disk_space_map_temp[disk_name])))
                        if disk_space_map_temp[disk_name] > 100:
                            break

                    for disk_name in disk_space_map_temp.keys():
                        if disk_space_map_temp[disk_name] > 0:
                            target_disk = disk_name
                            print("find disk with removing seed: " + target_disk)

                if target_disk is not None:
                    if target_disk in removal_list:
                        for seed in removal_list[target_disk]:
                            cls.remove_seed(seed)

                    # only the disk to add new seed should be updated
                    disk_space_map[target_disk] = disk_space_map_temp[target_disk]

                    target_location = None
                    for disk_location in disk_location_to_name_map:
                        if disk_location_to_name_map[disk_location] == target_disk:
                            target_location = disk_location
                    cls.add_seed(new_seed, target_location)
                    success_seeds.append(new_seed)
                    if Config.get("enable_email"):
                        EmailSender.send(u"种子", str(new_seed))
                    break

                retry += 1
                print("Try %d adding seed failed: %s" % (retry, str(new_seed)))
                if retry == max_retry:
                    fail_seeds.append(new_seed)
                    if Config.get("enable_email"):
                        EmailSender.send(u"添加失败", str(new_seed))

        return success_seeds, fail_seeds

    @classmethod
    def fast_remove_bad_seeds(cls):
        print("Start fast remove bad seeds\n")

        seeds = cls.parse_current_seeds(False)
        for seed in seeds:
            if seed.status == "Stopped":
                print("Fast remove stopped: " + str(seed))
                cls.remove_seed(seed)
                continue
            if seed.status == "Idle" and seed.since > 600 and seed.done == 0.0:
                print("Fast remove new idle: " + str(seed))
                cls.remove_seed(seed)

    @classmethod
    def remove_seed(cls, seed):
        assert seed.id is not None
        os.popen("transmission-remote -t %s -rad" % seed.id.strip())

        # remove file if still exists
        os.popen("rm -rf '" + DiskManager.append_delimiter_if_miss(seed.location) + seed.name + "'")

        print("Remove transmission seed: " + seed.id)

    @classmethod
    def find_bad_seeds(cls):
        seeds = cls.load_avg_speed()
        for seed in seeds:
            print(seed)

        bad_seeds = []
        total_bad_seed_size = 0
        for seed in seeds:
            if (str(seed.status).upper() == "IDLE" and seed.done > 0 and seed.since > 600) or str(
                    seed.status).upper() == "STOPPED":
                print("IDLE|STOP: >>>>>>>>> " + str(seed))
                total_bad_seed_size += seed.size
                bad_seeds.append(seed)
                continue

            # let new seed live for N minutes
            if seed.done < 100 or seed.since <= 4 * 60 * 60:
                continue

            # check upload speed
            size_index = min(round(seed.size / 1024), len(cls.size_factor) - 1)
            up_speed_threshold = cls.up_speed_threshold[round(seed.done / 10)] * cls.size_factor[size_index]
            print(
                "check up speed up={0}, threshold={1}, factor={2}, final_threshold={3}".format(seed.up, str(
                    cls.up_speed_threshold[round(seed.done / 10)]),
                                                                                               str(cls.size_factor[
                                                                                                       size_index]),
                                                                                               up_speed_threshold))
            if seed.up < up_speed_threshold:
                print("SLOW UP: >>>>>>>>> " + str(seed))
                total_bad_seed_size += seed.size
                bad_seeds.append(seed)
                continue

            # check average download speed
            down_speed_threshold = cls.down_avg_speed_threshold[round(seed.done / 10)]
            print(
                "check down avg speed done={0}, down_avg={1}, threshold={2}, ratio={3}".format(seed.done,
                                                                                               round(
                                                                                                   seed.done_size / seed.since),
                                                                                               down_speed_threshold,
                                                                                               seed.ratio))
            if round(seed.done_size / seed.since) < down_speed_threshold and seed.ratio < 1:
                print("SLOW DOWN: >>>>>>>>> " + str(seed))
                total_bad_seed_size += seed.size
                bad_seeds.append(seed)
                continue

        # the more larger size and the less upload speed, the first to be removed
        # up is added 0.01 to avoid dividing zero
        bad_seeds.sort(key=lambda x: int(x.status == "STOPPED") * 100 + int(x.status == "IDLE") * 30 + round(
            x.size / (x.up + 0.01)), reverse=True)

        for seed in bad_seeds:
            print("bad seed: " + str(seed))

        return total_bad_seed_size, bad_seeds


if __name__ == "__main__":
    a = [1, 2, 9, 4, 5]
    for i in a:
        print(i)
        if i == 2 or i == 4:
            a.remove(i)
            print("remove " + str(i))

    print(a)
