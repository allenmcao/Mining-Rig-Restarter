import asyncio
import requests
import json

import exceptions
import log

from datetime import datetime
from kasa import SmartStrip, SmartDevice

# TODO
# Create a detailed README
# Add more supported APIs (ethermine, hiveOS)
#   Find more accurate way of checking if online or not bc flexpool api seems to rate-limit updates when hitting api too often
#   Add enum for supported APIs
# Move API requests to separate modules
# Add grafana or some other visualization solution to track hashrate, restarts, API update times, etc.

# Fields
status_api = 'status_api'
coin = 'coin'
endpoint = 'endpoint'
wallet = 'wallet'
kasa_device_ip = "kasa_device_ip"
worker_name = 'worker_name'
smart_strip_plug_name = 'smart_strip_plug_name'
smart_strip_plug_number = 'smart_strip_plug_number'
mandatory_fields = [
    status_api,
    wallet, 
    kasa_device_ip, 
    worker_name, 
]
power_cycle_on_delay = 'power_cycle_on_delay'
time_until_offline = 'time_until_offline'
status_check_frequency = 'status_check_frequency'
status_check_cooldown = 'status_check_cooldown'
max_consecutive_restarts = 'max_consecutive_restarts'
current_consecutive_restarts = 'current_consecutive_restarts'

# Initialize default settings for each api from defaults.json
defaults = {}
with open('defaults.json') as defaults_file:
    defaults = json.load(defaults_file)


def is_online_query(rig):
    """Queries API to determine online status. Returns True if online, false if offline."""
    if status_api in rig:
        if rig[status_api] == 'flexpool':
            response = requests.get(rig[endpoint].format(rig[coin], rig[wallet], rig[worker_name]))
            json_response = json.loads(response.content.decode())
            result = json_response['result']
    else:
        raise exceptions.RRMissingFieldException('Rig', status_api)

    if type(result) is list:
        for worker in result:
            if (type(worker is dict) and 'name' in worker):
                if (worker['name'] == rig[worker_name]):
                    return is_online_calc(rig[time_until_offline], worker, rig)
            else:
                raise exceptions.RRMissingFieldException('API Worker Result', 'name')
        raise exceptions.RRMissingWorkerException(rig[worker_name])
    elif type(result) is dict:
        if ('name' in result and result['name'] == rig[worker_name]):
            return is_online_calc(time_until_offline, worker)
        raise exceptions.RRMissingWorkerException(rig[worker_name])
    else:
        raise exceptions.RRMissingWorkerException(rig[worker_name])

def is_online_calc(t_until_offline, worker, rig):
    """Datetime calculation to determine whether rig status is offline depending on given parameters.
    
    If t_until_offline is unspecified (<=0) then the 'isOnline' field is used to determine if online/offline.
    Last seen time is still calculated and returned in this instance.
    """
    last_seen_time = datetime.fromtimestamp(worker['lastSeen'])

    last_seen_delta = (datetime.now() - last_seen_time).total_seconds()
    last_seen_delta_m, last_seen_delta_s, ur_last_seen_delta_m = round(last_seen_delta // 60), round(last_seen_delta % 60), last_seen_delta / 60
    
    passed_online_check = t_until_offline > ur_last_seen_delta_m if t_until_offline > 0 else worker['isOnline']

    last_seen_message = f'Was last seen {last_seen_delta_m}m {last_seen_delta_s}s ago.'
    if not passed_online_check:
        # Stop current rig_restarter coroutine if max concurrent restarts is reached
        rig[current_consecutive_restarts] += 1
        if rig[current_consecutive_restarts] >= rig[max_consecutive_restarts]:
            raise exceptions.RRMaxRestartFailsException(worker['name'], rig[max_consecutive_restarts])

        exceeds_message = f' This exceeds the allowed offline time of {t_until_offline} min.' if t_until_offline > 0 else ''
        log.logger.info(f'{worker["name"]} is OFFLINE. {last_seen_message}{exceeds_message} Last seen time was: [{last_seen_time.strftime("%Y-%m-%d %H:%M")}')
        log.logger.info(f'\tConsecutive Restarts: {rig[current_consecutive_restarts]}')
    else:
        rig[current_consecutive_restarts] = 0
        log.logger.info(f'{worker["name"]} is ONLINE. {last_seen_message}')
    return passed_online_check


async def rig_restarter(rig):
    """Async task for a single rig that will check status and reboot indefinitely."""
    # Validate that rig has all mandatory fields
    for mand in mandatory_fields:
        if mand not in rig:
            raise exceptions.RRMissingFieldException('Rig', mand)

    # Correctly set device. Strip needs to update() before getting info about children.
    device_type = SmartStrip if (rig[smart_strip_plug_name] or rig[smart_strip_plug_number] > -1) else SmartDevice
    device = device_type(rig[kasa_device_ip])
    await device.update()

    # If using strip, grab correct child plug.
    if rig[smart_strip_plug_name]:
        device = device.get_plug_by_name(rig[smart_strip_plug_name])
    elif rig[smart_strip_plug_number] > -1:
        device = device.get_plug_by_index(rig[smart_strip_plug_number])


    # Default rig values if unset and run status checks indefinitely
    defaulted_rig = defaults[rig[status_api]] | rig
    defaulted_rig[current_consecutive_restarts] = 0
    while True:
        if is_online_query(defaulted_rig) is False:
            # Reset Smart Device
            # Currently not working to call device.reboot(), API is behaving incorrectly. Custom implementation below
            if device.is_on:
                await device.turn_off()
                await asyncio.sleep(defaulted_rig[power_cycle_on_delay])
            await device.turn_on()             

            # Cooldown before next status check after reboot
            await asyncio.sleep(defaulted_rig[status_check_cooldown] * 60)
        else:
            # Ensure status checks follow certain frequency (unless just rebooted)
            await asyncio.sleep(defaulted_rig[status_check_frequency] * 60)


async def main():
    """Create and execute multiple parallel rig restarters for each rig."""
    rig_restarters = []
    with open('rigs.json') as rigs_file:
        rigs_json = json.load(rigs_file)
        rig_restarters = [rig_restarter(rig) for rig in rigs_json]
    
    await asyncio.gather(*rig_restarters)

if __name__ == '__main__':
    asyncio.run(main())
