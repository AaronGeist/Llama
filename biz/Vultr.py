import json
import os

from util.config import Config


class Vultr:
    @classmethod
    def get_machines(cls):
        pass

    @classmethod
    def check_bandwidth(cls):
        resp = os.popen(
            "curl -H 'API-Key: %s' https://api.vultr.com/v1/server/list" % Config.get("vultr_api_key")).read()
        json_data = json.loads(resp)
        info_dict = list(json_data.values())[0]
        current_bandwidth_gb = info_dict['current_bandwidth_gb']
        allowed_bandwidth_gb = info_dict['allowed_bandwidth_gb']
        main_ip = info_dict["main_ip"]
        status = info_dict["active"]
        label = info_dict["label"]
        sub_id = info_dict["SUBID"]
        print("current_bw=%s,allowed_bw=%s" % (str(current_bandwidth_gb), str(allowed_bandwidth_gb)))

        return current_bandwidth_gb, allowed_bandwidth_gb


if __name__ == "__main__":
    Vultr.check_bandwidth()
