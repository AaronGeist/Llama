import json
import os
import time

from core.emailSender import EmailSender
from model.seed import TransmissionSeed
from util.config import Config
from util.utils import HttpUtils


class SeedManager:
    @classmethod
    def check_disk_space(cls):
        space_in_mb = float(os.popen("df -lm|grep vda1|awk '{print $4}'").read())
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
    def add_seed(cls, seed):
        torrent_file = "%s.torrent" % seed.id
        HttpUtils.download_file("https://pt.sjtu.edu.cn/download.php?id=%s" % seed.id, torrent_file)
        os.popen("transmission-remote -a %s" % torrent_file)
        time.sleep(2)
        os.popen("rm %s" % torrent_file)
        print("Add seed to transmission: " + str(seed))

    @classmethod
    def parse_current_seeds(cls):
        seeds = []
        cmdResults = os.popen("transmission-remote -l").read()
        lines = cmdResults.split("\n")[1: -2]  # remove first and last line
        for line in lines:
            data = line.split()
            seed = TransmissionSeed()
            seed.id = data[0]
            seed.done = data[1]
            seed.size = data[2] + data[3]
            seed.ETA = data[4]
            seed.up = data[5]
            seed.down = data[6]
            seed.ratio = data[7]
            seed.status = data[8]
            seed.name = data[9]
            seeds.append(seed)

        return seeds

    @classmethod
    def try_add_seeds(cls, seeds):

        max_retry = 3

        new_added_space_in_mb = 0
        for seed in seeds:
            retry = 0
            while retry < max_retry:
                space_in_mb = cls.check_disk_space() - new_added_space_in_mb
                space_in_mb -= seed.size
                print("space left: " + str(space_in_mb))
                if space_in_mb <= 0:
                    cls.remove_oldest_seed()
                    retry += 1
                else:
                    cls.add_seed(seed)
                    new_added_space_in_mb += seed.size
                    break

                print("Retry %d adding seed: %s" % (retry, str(seed)))
                if retry == max_retry:
                    EmailSender.send(u"添加失败", str(seed))

    @classmethod
    def remove_oldest_seed(cls):
        # remove the oldest seed which is idle and GB size
        transmission_id = os.popen("transmission-remote -l| grep Idle| head -n 1|awk '{print $1}'").read()
        info = os.popen("transmission-remote -l|grep Idle| head -n 1").read()
        if transmission_id != "":
            os.popen("transmission-remote -t %s -rad" % transmission_id.strip())
            print("Remove transmission seed: " + str(info))
        else:
            print("No idle transmission seed found")
