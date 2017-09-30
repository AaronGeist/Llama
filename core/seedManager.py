import json
import os
import time

from core.emailSender import EmailSender
from model.seed import TransmissionSeed
from util.config import Config
from util.utils import HttpUtils


class SeedManager:
    # index indicates the percentage of download, 0 -> 0%, 1 -> 10%
    up_speed_threshold = [0, 0, 0, 100, 100, 300, 300, 400, 500, 500, 500]

    # index indicates the size in GB, 0 -> 0GB
    size_factor = [1, 1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.5, 2, 2, 2, 2.5, 2.5, 2.5]

    # index indicates the percentage of download, 0 -> 0%, 1 -> 10%
    down_avg_speed_threshold = [0, 100, 200, 300, 400, 500, 500, 500, 500, 500, 500]

    init_disk_space = 23 * 1024

    @classmethod
    def check_disk_space(cls):
        space_in_mb = float(os.popen("df -lm|grep vda1|awk '{print $4}'").read())
        space_in_mb = min(space_in_mb, cls.init_disk_space - cls.total_size())
        print("disk_space=%sMB" % str(space_in_mb))
        return space_in_mb

    @classmethod
    def check_bandwidth(cls):
        resp = os.popen(
            "curl -H 'API-Key: %s' https://api.vultr.com/v1/server/list" % Config.get("vultr_api_key")).read()
        json_data = json.loads(resp)
        info_dict = list(json_data.values())[0]
        current_bandwidth_gb = info_dict['current_bandwidth_gb']
        allowed_bandwidth_gb = info_dict['allowed_bandwidth_gb']

        print("current_bw=%s,allowed_bw=%s", str(current_bandwidth_gb), str(allowed_bandwidth_gb))

        return current_bandwidth_gb, allowed_bandwidth_gb

    @classmethod
    def add_seed(cls, seed, download_link):
        torrent_file = "%s.torrent" % seed.id
        HttpUtils.download_file(download_link % seed.id, torrent_file)
        os.popen("transmission-remote -a %s" % torrent_file)
        time.sleep(2)
        os.popen("rm %s" % torrent_file)
        print("Add seed to transmission: " + str(seed))

    @classmethod
    def load_avg_speed(cls):
        times = 60
        interval = 1

        statistics = {}
        for i in range(times):
            seeds = cls.parse_current_seeds()
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

        for seed in statistics.values():
            print(seed)

        return statistics.values()

    @classmethod
    def parse_current_seeds(cls):
        seeds = []
        cmd_result = os.popen("transmission-remote -l").read()
        lines = cmd_result.split("\n")[1: -2]  # remove first and last line

        for line in lines:
            seed = TransmissionSeed()
            seeds.append(seed)

            data = line.split()
            seed.id = data[0]
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
                elif detail.startswith("  Downloading Time: "):
                    seed.since = int(
                        detail.replace("  Downloading Time: ", "").replace(" ", "").split("(")[1].split("sec")[
                            0])
                elif detail.startswith("  Downloaded: "):
                    seed.done_size = HttpUtils.pretty_format(
                        detail.replace("  Downloaded: ", ""), "KB")

        return seeds

    @classmethod
    def total_size(cls):
        seeds = cls.parse_current_seeds()
        total_size = 0
        for seed in seeds:
            total_size += seed.size
        return total_size

    @classmethod
    def try_add_seeds(cls, new_seeds, download_link):
        success_seeds = []
        max_retry = 1

        init_disk_space = cls.check_disk_space()
        new_added_space_in_mb = 0
        for new_seed in new_seeds:
            retry = 0
            while retry < max_retry:
                space_in_mb = round(init_disk_space - new_added_space_in_mb - new_seed.size, 1)
                print("disk space left: %sMB" % str(space_in_mb))

                # not enough space left, try to remove existing bad seeds
                if space_in_mb <= 0:
                    total_size, bad_seeds = cls.find_bad_seeds()

                    for bad_seed in bad_seeds:
                        cls.remove_seed(bad_seed.id)
                        space_in_mb += bad_seed.size
                        print("remove bad seed and space left: %sMB" % str(space_in_mb))
                        if space_in_mb > 100:
                            break

                if space_in_mb > 0:
                    cls.add_seed(new_seed, download_link)
                    success_seeds.append(new_seed)
                    new_added_space_in_mb += new_seed.size
                    EmailSender.send(u"种子", str(new_seed))
                    break

                retry += 1
                print("Try %d adding seed failed: %s" % (retry, str(new_seed)))
                if retry == max_retry:
                    EmailSender.send(u"添加失败", str(new_seed))

        return success_seeds

    @classmethod
    def remove_seed(cls, seed_id):
        assert seed_id is not None
        os.popen("transmission-remote -t %s -rad" % seed_id.strip())
        print("Remove transmission seed: " + seed_id)

    @classmethod
    def find_bad_seeds(cls):
        seeds = cls.load_avg_speed()

        bad_seeds = []
        total_bad_seed_size = 0
        for seed in seeds:
            # let new seed live for N minutes
            if seed.since <= 60 * 30:
                continue

            if str(seed.status).upper() == "IDLE":
                print("IDLE: >>>>>>>>> " + str(seed))
                total_bad_seed_size += seed.size
                bad_seeds.append(seed)
                continue

            # check upload speed
            up_speed_threshold = cls.up_speed_threshold[round(seed.done / 10)] * cls.size_factor[
                round(seed.size / 1024)]
            print(
                "check up speed up={0}, threshold={1}, factor={2}, final_threshold={3}".format(seed.up, str(
                    cls.up_speed_threshold[round(seed.done / 10)]),
                                                                                               str(cls.size_factor[
                                                                                                       round(
                                                                                                           seed.size / 1024)]),
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
        bad_seeds.sort(key=lambda x: round(x.size / (x.up + 0.01)), reverse=True)

        for seed in bad_seeds:
            print("bad seed: " + str(seed))

        return total_bad_seed_size, bad_seeds
