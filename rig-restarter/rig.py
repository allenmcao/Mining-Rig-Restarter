from pydantic import BaseModel, ValidationError, validator
from pools_enum import Pools
import exceptions

from kasa import SmartStrip, SmartDevice

class Rig(BaseModel):
    status_api: str
    wallet: str
    kasa_device_ip: str
    worker_name: str
    endpoint: str

    coin: str = None
    smart_strip_plug_name: str = None
    smart_strip_plug_number: int = None

    power_cycle_on_delay: int
    time_until_offline: int
    status_check_frequency: int
    status_check_cooldown: int
    max_consecutive_restarts: int
    current_consecutive_restarts: int = 0

    def __init__(self, rig_json):
        self.status_api = rig_json['status_api']
        self.coin = rig_json['coin']
        self.endpoint = rig_json['endpoint']
        self.wallet = rig_json['wallet']
        self.kasa_device_ip = rig_json["kasa_device_ip"]
        self.worker_name = rig_json['worker_name']
        self.smart_strip_plug_name = rig_json['smart_strip_plug_name']
        self.smart_strip_plug_number = rig_json['smart_strip_plug_number']
        
        self.power_cycle_on_delay = rig_json['power_cycle_on_delay']
        self.time_until_offline = rig_json['time_until_offline']
        self.status_check_frequency = rig_json['status_check_frequency']
        self.status_check_cooldown = rig_json['status_check_cooldown']
        self.max_consecutive_restarts = rig_json['max_consecutive_restarts']
        self.current_consecutive_restarts = rig_json['current_consecutive_restarts']

    def get_device(self):
        device_type = SmartStrip if (self.smart_strip_plug_name or self.smart_strip_plug_number) else SmartDevice
        return device_type(self.kasa_device_ip)
    
    @validator('status_api')
    def status_api_in_enum(self):
        if self.status_api not in set(p.poolname for p in Pools):
            raise exceptions.RRWrongStatusApiException(self.status_api)

    @validator('coin')
    def flexpool_has_coin(self):
        if self.coin == 'ETH' and self.status_api == Pools.Flexpool.poolname:
            raise exceptions.RRFlexpoolWrongCoinException()

    def to_json(self):
        return self.__str__()
    
    @staticmethod
    def from_json(json_dct):
      return Rig(json_dct)