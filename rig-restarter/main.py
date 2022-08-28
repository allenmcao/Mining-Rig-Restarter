import asyncio
import json
import os

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

# Load defaults file once and store in global variable so any rig restarter can access.
try:
    with open(os.path.join(os.path.dirname(__file__), '../defaults.json'), 'r') as defaults_file:
        defaults = json.load(defaults_file)
        defaults_file.close()
except:
    raise exceptions.RRMalformedJsonException('Defaults')


async def rig_restarter(rig):
    """Async task for a single rig that will check status and reboot indefinitely."""
    # Validate that rig has all mandatory fields
    for mand in mandatory_fields:
        if mand not in rig:
            raise exceptions.RRMissingFieldException('Rig', mand)

    # Correctly set device. Strip needs to update() before getting info about children.
    device_type = SmartStrip if (smart_strip_plug_name in rig or smart_strip_plug_number in rig) else SmartDevice
    device = device_type(rig[kasa_device_ip])
    await device.update()

    # If using strip, grab correct child plug.
    if smart_strip_plug_name in rig and rig[smart_strip_plug_name]:
        device = device.get_plug_by_name(rig[smart_strip_plug_name])
    elif smart_strip_plug_number in rig and rig[smart_strip_plug_number] > -1:
        device = device.get_plug_by_index(rig[smart_strip_plug_number])

    # Default rig values if unset and run status checks indefinitely. Reread each time bc defaults file may be accessed by query.
    rig = defaults[rig[status_api]] | rig

    # Enter indefinite rig restarter loop
    current_consecutive_restarts = 0
    while True:
        status = pool_query.is_online(*pool_query.filter_query_fields(rig))
        if status is False:
            # Stop current rig_restarter coroutine if max consecutive restarts is reached
            current_consecutive_restarts += 1
            log.logger.info(f'\tConsecutive Restarts: {current_consecutive_restarts}')
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
        with open(os.path.join(os.path.dirname(__file__), '../rigs.json'), 'r') as rigs_file:
            rigs_json = json.load(rigs_file)
            rig_restarters = [rig_restarter(rig) for rig in rigs_json]
    except:
        raise exceptions.RRMalformedJsonException('Rigs')
    
    await asyncio.gather(*rig_restarters)

if __name__ == '__main__':
    asyncio.run(main())
