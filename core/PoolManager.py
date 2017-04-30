import requests

from biz.Site1 import Site1
from biz.Site2 import Site2
from util.ParallelTemplate import ParallelTemplate


class PoolManager:
    sites = []

    WORKER_NUM = 20

    @classmethod
    def initialize(cls):
        if len(cls.sites) == 0:
            cls.sites.append(Site1())
            cls.sites.append(Site2())

    @classmethod
    def refresh(cls):
        proxyInfos = []
        cls.initialize()
        for site in cls.sites:
            proxyInfos.extend(site.parse())

        ret = filter(lambda x: x is not None, cls.validate(proxyInfos))

        # store result into Redis
        for r in ret:
            print(r)

    @classmethod
    def validate(cls, proxyInfos):
        template = ParallelTemplate(cls.WORKER_NUM)
        return template.run(cls.doValidate, proxyInfos)

    @classmethod
    def doValidate(cls, proxyInfo):
        assert proxyInfo is not None
        proxy = {"http": "http://" + proxyInfo.ip + ":" + proxyInfo.port}

        try:
            r = requests.get('http://www.google.com/', proxies=proxy, timeout=5)
            if r.status_code == 200:
                print("YES " + proxyInfo.ip + ":" + proxyInfo.port)
                return proxyInfo
        except:
            print("NO")
            return None


if __name__ == "__main__":
    PoolManager.refresh()
