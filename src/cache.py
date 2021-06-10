from time import sleep

import redis as redis

from src.config import OCD_DTL_REDIS_HOST, OCD_DTL_REDIS_PORT, OCD_DTL_REDIS_PASSWORD
from src.logger import logger


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Cache(metaclass=Singleton):
    DEFAULT_VALUE = int(True)
    DEFAULT_DB = 'db0'

    def __init__(self):
        # Initialize a single redis connection
        self.con = redis.Redis(host=OCD_DTL_REDIS_HOST, port=OCD_DTL_REDIS_PORT, password=OCD_DTL_REDIS_PASSWORD)
        info = self.con.info()
        keys = info.get(self.DEFAULT_DB, {}).get('keys', -1)
        logger.debug(f'Hashkeys in cache: {keys}')

    def has(self, hashkey):
        return bool(self.con.get(hashkey))

    def set(self, hashkey):
        return self.con.set(hashkey, self.DEFAULT_VALUE)

    def close(self):
        """Should be called once per program since this is a singleton"""
        self.con.close()
