import json
import os

import pickle

from core.db import Cache
from util.config import Config
from util.utils import HttpUtils


class SeedManager:
    BUCKET_NAME_TRANSMISSION = "transmission_list"

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
        os.popen("transmission-remote -a %s.torrent && rm %s" % (seed.id, torrent_file))
        # transmission_id = os.popen("transmission-remote -l|tail -n 2| grep -v Sum|awk '{print $1}'").read()

    @classmethod
    def try_add_seeds(cls, seeds):

        max_retry = 3
        max_seed_size_mb = Config.get("seed_max_size_mb")
        for seed in seeds:
            if seed.size <= max_seed_size_mb:

                retry = 0
                while retry < max_retry:
                    space_in_mb = cls.check_disk_space()
                    space_in_mb -= seed.size
                    if space_in_mb <= 0:
                        cls.remove_oldest_seed()
                        retry += 1
                    else:
                        cls.add_seed(seed)
                        break

    @classmethod
    def remove_oldest_seed(cls):
        # remove the oldest seed which is idle
        transmission_id = os.popen("transmission-remote -l|grep Idle| head -n 1|awk '{print $1}'").read()
        if transmission_id != "":
            os.popen("transmission-remote -t %s -rad" % transmission_id)
