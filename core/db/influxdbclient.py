# -*- coding:utf-8 -*-
from queue import Queue

from influxdb import InfluxDBClient

from core.singleton import singleton


@singleton
class InfluxdbClient:
    clients = Queue()

    worker_num = 10

    database = "llama"

    def __init__(self):

        for i in range(10):
            self.clients.put(InfluxDBClient('localhost', 8086, 'root', '', database=self.database))

        client = self.clients.get(block=True, timeout=5)
        if self.database not in client.get_list_database():
            client.create_database(self.database)
        self.clients.put(client)

        #
        # if database not in self.client.get_list_database():
        #     self.client.create_database(database)

        print("influxDb clients initialized")

    def query(self, sql):

        client = self.clients.get(block=True, timeout=5)
        query_res = list(client.query(sql).get_points())

        self.clients.put(client)
        return query_res

    def write(self, measurement, tags, fields):
        data = [
            {"measurement": measurement,
             "tags": tags,
             "fields": fields}
        ]

        if type(fields) is not dict:
            data[0]["fields"] = {"value": fields}

        client = self.clients.get(block=True, timeout=5)
        write_res = client.write_points(data)
        self.clients.put(client)

        return write_res


if __name__ == "__main__":
    db = InfluxdbClient()
    res = db.write("students", {"gender": "M"}, {"score": 86})

    db.write("test", None, {"value": 1})
    res = db.query("select * from test;")

    print(res)
