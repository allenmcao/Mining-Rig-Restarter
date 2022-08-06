import asyncio
import requests
import json
import logging
import sys

from datetime import datetime
from kasa import SmartStrip, SmartDevice

# NOTES
# flexpool api seems to rate-limit updates when hitting api too often, have to scale back on status checks

# TODO
# better logging (asyncio compatible)
# create file default.json to have default values between different APIs/methods of checking online
    # related to above, find more accurate way of checking if online or not BC API is laggy
# Move API requests and logging to separate packages
# Add grafana or some other visualziation solution to track hashrate, restarts, API update times, etc.

url = 'url'
coin = 'coin'
wallet = 'wallet'
kasa_device_ip = "kasa_device_ip"
worker_name = 'worker_name'
smart_strip_plug_name = 'smart_strip_plug_name'
smart_strip_plug_number = 'smart_strip_plug_number'

log_online_deltas = 'log_online_deltas'

power_cycle_on_delay = 'power_cycle_on_delay'
time_until_offline = 'time_until_offline'
status_check_frequency = 'status_check_frequency'
status_check_cooldown = 'status_check_cooldown'

# Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rig_restarters.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def is_online(rig):
    """Queries API to determine online status. Returns True if online, false if offline."""
    response = requests.get(rig[url].format(rig[coin], rig[wallet], rig[worker_name]))
    json_response = json.loads(response.content.decode())
    result = json_response['result']

    if type(result) is list:
        for worker in result:
            if (type(worker is dict) and 'name' in worker):
                if (worker['name'] == rig[worker_name]):
                    return is_online_calc(rig[time_until_offline], worker, rig[log_online_deltas])
            else:
                logging.error("Malformed worker in list:" + str(worker))
        logging.error("Worker not found in list.")
    elif type(result) is dict:
        if ('name' in result and result['name'] == rig[worker_name]):
            return is_online_calc(time_until_offline, worker, rig[log_online_deltas])
        logging.error("Worker not found as result.")
    else:
        logging.error("Response type unknown.")

def is_online_calc(t_until_offline, worker, log_ol_deltas):
    """Datetime calculation to determine whether rig status is offline depending on given parameters."""
    last_seen_delta_in_minutes = ((datetime.now() - datetime.fromtimestamp(worker['lastSeen'])).total_seconds() / 60)
    passed_online_check = t_until_offline > last_seen_delta_in_minutes if t_until_offline > 0 else worker['isOnline']

    if not passed_online_check:
        exceeds_message = ' This exceeds the allowed offline time of {} minutes.'.format(t_until_offline) if t_until_offline > 0 else ''
        logging.info('Worker is OFFLINE, was last seen {} minutes ago.{}'.format(last_seen_delta_in_minutes, exceeds_message))
        logging.info('Last Seen Time: ' +  datetime.fromtimestamp(worker['lastSeen']).strftime("%Y-%m-%d %H:%M"))
    elif log_ol_deltas:
        logging.info('Worker is ONLINE, was last seen {} minutes ago.'.format(last_seen_delta_in_minutes))
    return passed_online_check


async def rig_restarter(rig):
    """Async task for a single rig that will check status and reboot indefinitely."""
    # Correctly set device. Strip needs to update() before getting info about children.
    device_type = SmartStrip if (rig[smart_strip_plug_name] or rig[smart_strip_plug_number] > -1) else SmartDevice
    device = device_type(rig[kasa_device_ip])
    await device.update()

    # If using strip, grab correct child plug.
    if rig[smart_strip_plug_name]:
        device = device.get_plug_by_name(rig[smart_strip_plug_name])
    elif rig[smart_strip_plug_number] > -1:
        device = device.get_plug_by_index(rig[smart_strip_plug_number])

    while True:
        if is_online(rig) is False:
            # Reset Smart Device
            # Currently not working to call device.reboot(), API is behaving incorrectly. Custom implementation below
            if device.is_on:
                await device.turn_off()
                await asyncio.sleep(rig[power_cycle_on_delay])
            await device.turn_on()             

            # Cooldown between status checks after reboot
            await asyncio.sleep(rig[status_check_cooldown] * 60)

        # Ensure status checks follow certain frequency (unless just rebooted)
        await asyncio.sleep(rig[status_check_frequency] * 60)



async def main():
    """Create and execute multiple parallel rig restarters for each rig."""
    rig_restarters = []
    with open('rigs.json') as rigs_file:
        rigs_json = json.load(rigs_file)
        rig_restarters = [rig_restarter(rig) for rig in rigs_json]

    
    await asyncio.gather(*rig_restarters)

if __name__ == '__main__':
    asyncio.run(main())
