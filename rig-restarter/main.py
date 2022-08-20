import asyncio
import json

import exceptions
import pool_query
import log

from kasa import SmartStrip, SmartDevice

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


def is_online(rig):
    """Checks whether rig is online depending on pool type. Returns True if online, False if offline."""
    worker_json = pool_query.is_online_query(rig[status_api], rig[worker_name], rig[wallet], rig[coin])
    return pool_query.is_online_calc(worker_json, rig[time_until_offline])

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
    defaults = {}
    with open('defaults.json') as defaults_file:
        defaults = json.load(defaults_file)
    defaults_file.close()
    rig = defaults[rig[status_api]] | rig
    
    current_consecutive_restarts = 0
    while True:
        if is_online(rig) is False:
            # Stop current rig_restarter coroutine if max consecutive restarts is reached
            current_consecutive_restarts += 1
            log.logger.info(f'\tConsecutive Restarts: {rig[current_consecutive_restarts]}')
            if current_consecutive_restarts >= rig[max_consecutive_restarts]:
                raise exceptions.RRMaxRestartFailsException(rig[worker_name], rig[max_consecutive_restarts])

            # Reset Smart Device
            # Currently not working to call device.reboot(), API is behaving incorrectly. Custom implementation below
            if device.is_on:
                await device.turn_off()
                await asyncio.sleep(rig[power_cycle_on_delay])
            await device.turn_on()             

            # Cooldown before next status check after reboot
            await asyncio.sleep(rig[status_check_cooldown] * 60)
        else:
            current_consecutive_restarts = 0

            # Ensure status checks follow certain frequency (unless just rebooted)
            await asyncio.sleep(rig[status_check_frequency] * 60)


async def main():
    """Create and execute multiple parallel rig restarters for each rig."""
    rig_restarters = []

    try:
        with open('rigs.json') as rigs_file:
            rigs_json = json.load(rigs_file)
            rig_restarters = [rig_restarter(rig) for rig in rigs_json]
    except:
        raise exceptions.RRMalformedJsonException('Rigs')
    
    await asyncio.gather(*rig_restarters)

if __name__ == '__main__':
    asyncio.run(main())
