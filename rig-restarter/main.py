import asyncio
import json
import os

import exceptions
import pool_query
import log
from rig import Rig

# Load defaults file once and store in global variable so any rig restarter can access.
try:
    with open(os.path.join(os.path.dirname(__file__), '../defaults.json'), 'r') as defaults_file:
        defaults = json.load(defaults_file)
        defaults_file.close()
except:
    raise exceptions.RRMalformedJsonException('Defaults')


async def rig_restarter(rig):
    """Async task for a single rig that will check status and reboot indefinitely."""
    # Default rig values if unset and run status checks indefinitely. Reread each time bc defaults file may be accessed by query.
    rig = Rig(defaults[rig["status_api"]] | rig)

    # Correctly set device and update. Strip needs to update() before getting info about children.
    device = rig.get_device()
    await device.update()

    # If using strip, grab correct child plug.
    if rig.smart_strip_plug_name:
        device = device.get_plug_by_name(rig.smart_strip_plug_name)
    elif rig.smart_strip_plug_number and rig.smart_strip_plug_number > -1:
        device = device.get_plug_by_index(rig.smart_strip_plug_number)
    

    # Enter indefinite rig restarter loop
    while True:
        status = pool_query.is_online(rig)
        if status is False:
            # Stop current rig_restarter coroutine if max consecutive restarts is reached
            rig.current_consecutive_restarts += 1
            log.logger.info(f'\tConsecutive Restarts: {rig.current_consecutive_restarts}')
            if rig.current_consecutive_restarts >= rig.max_consecutive_restarts:
                raise exceptions.RRMaxRestartFailsException(rig.worker_name, rig.max_consecutive_restarts)

            # Reset Smart Device
            # Currently not working to call device.reboot(), API is behaving incorrectly. Custom implementation below
            if device.is_on:
                await device.turn_off()
                await asyncio.sleep(rig.power_cycle_on_delay)
            await device.turn_on()             

            # Cooldown before next status check after reboot
            await asyncio.sleep(rig.status_check_cooldown * 60)
        elif status is True:
            rig.current_consecutive_restarts = 0

            # Ensure status checks follow certain frequency (unless just rebooted)
            await asyncio.sleep(rig.status_check_frequency * 60)


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
