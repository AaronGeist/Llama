from biz.mteam import NormalAlert, AdultAlert
from util.config import Config


class PTMaster:
    watch_list = [
        NormalAlert,  # mteam normal torrents
        AdultAlert  # mteam adult torrents
    ]

    @classmethod
    def get_machines(cls):
        machines = Config.get("machines")
        assert machines is not None
        return machines

    @classmethod
    def gogogo(cls):
        seeds = cls.find_new_seeds()
        stats = cls.check_machines_stat()
        new_stats = cls.remove_if_necessary()
        success = cls.add_new_seeds()

    @classmethod
    def find_new_seeds(cls):
        seeds = list()
        for site in cls.watch_list:
            site = site()
            seeds.extend(site.filter(site.crawl()))

        for seed in seeds:
            print(seed)

        return seeds

    @classmethod
    def check_machines_stat(cls):
        pass

    @classmethod
    def remove_if_necessary(cls):
        pass

    @classmethod
    def add_new_seeds(cls):
        pass
