from enum import Enum

class Pools(Enum):
    def __new__(cls, *args, **kwds):
          value = len(cls.__members__) + 1
          obj = object.__new__(cls)
          obj._value_ = value
          return obj
    def __init__(self, pool, endpoint):
        self.pool = pool
        self.endpoint = endpoint

    FLEXPOOL = ('flexpool', 'https://api.flexpool.io/v2/miner/workers?worker={}&address={}&coin={}')
    ETHERMINE = ('ethermine', 'https://api.ethermine.org/miner/{}/worker/{}/currentStats')