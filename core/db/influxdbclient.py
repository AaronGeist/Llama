# -*- coding:utf-8 -*-
from influxdb import InfluxDBClient


class InfluxdbClient:
    client = None

    def __init__(self, database):
        self.client = InfluxDBClient('localhost', 8086, 'root', '', database)

        if database not in self.client.get_list_database():
            self.client.create_database(database)

    def query(self, sql):
        return list(self.client.query(sql).get_points())

    def write(self, measurement, tags, fields):
        data = [
            {"measurement": measurement,
             "tags": tags,
             "fields": fields}
        ]

        if type(fields) is not dict:
            data[0]["fields"] = {"value": fields}

        return self.client.write_points(data)


if __name__ == "__main__":
    db = InfluxdbClient("test")
    res = db.write("students", {"gender": "M"}, {"score": 86})

    db.write("test", None, {"value": 1})
    res = db.query("select * from test;")

    print(res)
