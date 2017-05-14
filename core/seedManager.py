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

        resp = os.popen(
            "curl -H 'API-Key: %s' https://api.vultr.com/v1/server/list" % Config.get("vultr_api_key")).read()
        json_data = json.loads(resp)
        info_dict = list(json_data.values())[0]
        current_bandwidth_gb = info_dict['current_bandwidth_gb']
        allowed_bandwidth_gb = info_dict['allowed_bandwidth_gb']

        print("space=%s,current_bw=%s,allowed_bw=%s",
              (str(space_in_mb), str(current_bandwidth_gb), str(allowed_bandwidth_gb)))

        return space_in_mb, current_bandwidth_gb, allowed_bandwidth_gb

    @classmethod
    def add_seed(cls, seed):
        torrent_file = "%s.torrent" % seed.id
        HttpUtils.download_file("https://pt.sjtu.edu.cn/download.php?id=%s" % seed.id, torrent_file)
        os.popen("transmission-remote -a %s.torrent && rm %s" % (seed.id, torrent_file))
        transmission_id = os.popen("transmission-remote -l|tail -n 2| grep -v Sum|awk '{print $1}'").read()
        Cache().set(transmission_id, pickle.dumps(seed))
        Cache().append(cls.BUCKET_NAME_TRANSMISSION, transmission_id)

    @classmethod
    def try_add_seeds(cls, seeds):
        status = cls.check_disk_space()
        space_in_mb = status[0]
        current_bandwidth_gb = status[1]
        allowed_bandwidth_gb = status[2]

        max_seed_size_mb = Config.get("seed_max_size_mb")
        for seed in seeds:
            if seed.size <= max_seed_size_mb:
                space_in_mb -= seed.size
                current_bandwidth_gb += seed.size / 1024
                if current_bandwidth_gb >= allowed_bandwidth_gb:
                    break
                if space_in_mb <= 0:
                    cls.remove_seeds()

    @classmethod
    def update_seeds_status(cls):
        ids = Cache().get_by_range(cls.BUCKET_NAME_TRANSMISSION)
        print(ids)
        for transmission_id in ids:
            pickle_data = Cache().get(transmission_id)
            assert pickle_data is not None
            seed = pickle.loads(pickle_data)
            cls.reload_seed(seed)

    @classmethod
    def reload_seed(cls, seed):
        print(seed)
        pass

    @classmethod
    def remove_seeds(cls):
        pass
