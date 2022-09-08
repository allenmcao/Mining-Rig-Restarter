class Rig():
    def __init__(self, rig_json):
        self.status_api = rig_json['status_api']
        self.coin = rig_json['coin']
        self.endpoint = 'endpoint'
        self.wallet = 'wallet'
        self.kasa_device_ip = "kasa_device_ip"
        self.worker_name = 'worker_name'
        self.smart_strip_plug_name = 'smart_strip_plug_name'
        self.smart_strip_plug_number = 'smart_strip_plug_number'
        
        self.power_cycle_on_delay = 'power_cycle_on_delay'
        self.time_until_offline = 'time_until_offline'
        self.status_check_frequency = 'status_check_frequency'
        self.status_check_cooldown = 'status_check_cooldown'
        self.max_consecutive_restarts = 'max_consecutive_restarts'
        self.current_consecutive_restarts = 'current_consecutive_restarts'
    
    def has_mandatory_fields(self):
        mandatory_fields = [
            status_api,
            wallet, 
            kasa_device_ip, 
            worker_name, 
        ]