import abc
import datetime

from core.db import Cache


class Monitor(object):
    bucket = ""

    # max size per fetch
    LIMIT = 200
    DELIMITER = "_"

    def history(self):
        res = dict()
        data = list()
        title = list()
        for single in Cache().get_by_range(self.bucket, start=0, end=self.LIMIT):
            item = single.split(self.DELIMITER)
            title.append(item[0])
            data.append(float(item[1]))
        data.reverse()
        title.reverse()
        res['data'] = data
        res['title'] = title
        return res

    def latest(self):
        res = dict()
        for single in Cache().get_by_range(self.bucket, start=0, end=0):
            item = single.split(self.DELIMITER)
            res['title'] = item[0]
            res['data'] = float(item[1])
            break
        return res

    def monitor(self):
        data = self.generate_data()
        now = datetime.datetime.now()
        Cache().append(self.bucket, now.strftime('%H:%M:%S') + self.DELIMITER + str(data))

    @abc.abstractmethod
    def generate_data(self):
        pass
