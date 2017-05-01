import abc
import datetime

from core.db import Cache


class Monitor(object):
    # max size per fetch
    LIMIT = 200
    DELIMITER = "_"

    def history(self):
        res = dict()
        data = list()
        title = list()
        for single in Cache().get_by_range(self.get_bucket(), start=0, end=self.LIMIT - 1):
            item = single.decode("utf-8").split(self.DELIMITER)
            title.append(item[0])
            data.append(float(item[1]))
        data.reverse()
        title.reverse()
        res['data'] = data
        res['title'] = title
        return res

    def latest(self):
        res = dict()
        for single in Cache().get_by_range(self.get_bucket(), start=0, end=0):
            item = single.split(self.DELIMITER)
            res['title'] = item[0]
            res['data'] = float(item[1])
            break
        return res

    def monitor(self):
        data = self.generate_data()
        now = datetime.datetime.now()
        Cache().append(self.get_bucket(), now.strftime('%H:%M:%S') + self.DELIMITER + str(data))

        # if data is below/above threshold, send alert
        self.alert(data)

    def alert(self, data):
        pass

    @abc.abstractmethod
    def generate_data(self):
        pass

    @abc.abstractmethod
    def get_bucket(self):
        pass
