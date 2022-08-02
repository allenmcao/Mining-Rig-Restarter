import asyncio
import requests
import json

from datetime import datetime
from kasa import SmartStrip, SmartDevice

# NOTES
# flexpool api seems to rate-limit updates when hitting api too often, have to scale back on status checks

# TODO
# move variables to rig_settings.json
# multithread checking/resetting multiple rigs
# better logging (asyncio compatible)
# create file default.json to have default values between different APIs/methods of checking online
    # related to above, find more accurate way of checking if online or not BC API is laggy
# Move API requests and logging to separate packages

# Default Settings
url = 'https://api.flexpool.io/v2/miner/workers?coin={}&address={}&worker={}'
coin = 'ETH'
wallet = ''
kasa_device_ip = "192.168.0.0"  # IP of kasa smart device to connect to.
worker_name = ''
smart_strip_plug_name = ''          # If using smartstrip, denotes the name of plug to power cycle.
smart_strip_plug_number = 0         # If using smartstrip, a nonnegative number will indicate which plug to power cycle.

log_online_deltas = True            # If rig is online, determine whether or not to log (along with last seen time).

power_cycle_on_delay = 3        # Time in seconds to complete power cycle
time_until_offline = 10         # Time in minutes until rig is considered offline and will be reset. If zero, then API online/offline value will be used.
status_check_frequency = 3      # Time in minutes to check rig status
status_check_cooldown = 10      # Time in minutes to wait to check rig status after resetting

# Set Settings Based on Rig File
# Will need to set some settings inside multithreaded loop later
# Add logging and graceful erroring on missing fields
with open('rigs.json') as rigs_file:
    rigs_json = json.load(rigs_file)

    url = rigs_json['url']
    coin = rigs_json['coin']
    wallet = rigs_json['wallet']
    kasa_device_ip = rigs_json['kasa_device_ip']
    worker_name = rigs_json['worker_name']
    smart_strip_plug_name = rigs_json['smart_strip_plug_name']
    smart_strip_plug_number = rigs_json['smart_strip_plug_number']

    log_online_deltas = rigs_json['log_online_deltas']

    power_cycle_on_delay = rigs_json['power_cycle_on_delay']
    time_until_offline = rigs_json['time_until_offline']
    status_check_frequency = rigs_json['status_check_frequency']
    status_check_cooldown = rigs_json['status_check_cooldown']


# Queries API to determine online status. True if online, false if offline.
def is_online():
    response = requests.get(url.format(coin, wallet, worker_name))
    json_response = json.loads(response.content.decode())
    result = json_response['result']

    if type(result) is list:
        for worker in result:
            if (type(worker is dict) and 'name' in worker):
                if (worker['name'] == worker_name):
                    return is_online_calc(time_until_offline, worker)
            log("Malformed worker json.")
        log("Worker not found in list.")
    elif type(result) is dict:
        if ('name' in result and result['name'] == worker_name):
            return is_online_calc(time_until_offline, worker)
        log("Worker not found as result.")
    else:
        log("Response type unknown.")

# Datetime calculation to determine whether rig status is offline depending on given parameters.
def is_online_calc(time_until_offline, worker):
    last_seen_delta_in_minutes = ((datetime.now() - datetime.fromtimestamp(worker['lastSeen'])).total_seconds() / 60)
    passed_online_check = time_until_offline > last_seen_delta_in_minutes if time_until_offline > 0 else worker['isOnline']

    if not passed_online_check:
        exceeds_message = ' This exceeds the allowed offline time of {} minutes.'.format(time_until_offline) if time_until_offline > 0 else ''
        log('Worker is OFFLINE, was last seen {} minutes ago.{}'.format(last_seen_delta_in_minutes, exceeds_message))
        log('Worker JSON:' + str(worker))
        log('Last Seen Time: ' +  datetime.fromtimestamp(worker['lastSeen']).strftime("%Y-%m-%d %H:%M"))
    elif log_online_deltas:
        log('Worker is ONLINE, was last seen {} minutes ago.'.format(last_seen_delta_in_minutes))
    return passed_online_check

def log(message):
    now = datetime.now()
    print('[' + now.strftime("%Y-%m-%d %H:%M") + '] ' + message)



async def main():
    # Correctly set device. Strip needs to update() before getting info about children.
    device_type = SmartStrip if (smart_strip_plug_name or smart_strip_plug_number > -1) else SmartDevice
    device = device_type(kasa_device_ip)
    await device.update()

    # If using strip, grab correct child plug.
    if smart_strip_plug_name:
        device = device.get_plug_by_name(smart_strip_plug_name)
    elif smart_strip_plug_number > -1:
        device = device.get_plug_by_index(smart_strip_plug_number)

    while True:
        if is_online() is False:
            # Reset Smart Device
            # Currently not working to call device.reboot(), api is performing incorrectly. Custom implementation below
            if device.is_on:
                await device.turn_off()
                await asyncio.sleep(power_cycle_on_delay)
            await device.turn_on()             

            # Cooldown between status checks after reboot
            await asyncio.sleep(status_check_cooldown * 60)

        # Ensure status checks follow certain frequency (unless just rebooted)
        await asyncio.sleep(status_check_frequency * 60)

if __name__ == "__main__":
    asyncio.get_event_loop()
    asyncio.run(main())
