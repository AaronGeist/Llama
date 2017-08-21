import redis

from core.singleton import singleton


@singleton
class Cache:
    instance = None
    MAX_SIZE = 2000

    def __init__(self):
        pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
        self.instance = redis.StrictRedis(connection_pool=pool)

    def append(self, bucket_name, value):
        if self.instance.llen(bucket_name) >= self.MAX_SIZE * 2:
            self.instance.ltrim(bucket_name, 0, self.MAX_SIZE - 1)
        self.instance.lpush(bucket_name, value)

    def set(self, key, value):
        self.instance.set(key, value)

    def get(self, key):
        return self.instance.get(key)

    def get_by_range(self, bucket_name, start=0, end=-1):
        return self.instance.lrange(bucket_name, start, end)

    def show(self, bucket_name):
        print(self.instance.lrange(bucket_name, 0, -1))

    def set_with_expire(self, key, value, expire):
        self.instance.set(name=key, value=value, ex=expire)

    def set_add(self, bucket_name, value):
        self.instance.sadd(bucket_name, value)

    def set_get_all(self, bucket_name):
        self.instance.smembers(bucket_name)

    def set_contains(self, bucket_name, value):
        return self.instance.sismember(bucket_name, value)

    def set_delete(self, bucket_name, value):
        self.instance.srem(bucket_name, value)

    def hash_set(self, bucket_name, key, value):
        self.instance.hset(bucket_name, key, value)

    def hash_get(self, bucket_name, key):
        return self.instance.hget(bucket_name, key)
