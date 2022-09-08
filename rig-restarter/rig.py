import exceptions

class Rig():
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
    
    def has_mandatory_fields(self):
        mandatory_fields = [
            self.status_api,
            self.wallet, 
            self.kasa_device_ip, 
            self.worker_name, 
        ]

        for mand in mandatory_fields:
            if not self.mand:
                raise exceptions.RRMissingFieldException('Rig', mand)

    def to_json(self):
        return self.__str__()
    
    @staticmethod
    def from_json(json_dct):
      return Rig(json_dct)