import asyncio
import json
import os

import exceptions
from rig_restarter import rig_restarter

# Load defaults file once and store in global variable so any rig restarter can access.
try:
    with open(os.path.join(os.path.dirname(__file__), '../defaults.json'), 'r') as defaults_file:
        defaults = json.load(defaults_file)
        defaults_file.close()
except:
    raise exceptions.RRMalformedJsonException('Defaults')

async def main():
    """Create and execute multiple parallel rig restarters for each rig."""
    rig_restarters = []

    try:
        with open(os.path.join(os.path.dirname(__file__), '../rigs.json'), 'r') as rigs_file:
            rigs_json = json.load(rigs_file)
            rig_restarters = [rig_restarter(rig, defaults) for rig in rigs_json]
    except:
        raise exceptions.RRMalformedJsonException('Rigs')
    
    await asyncio.gather(*rig_restarters)

if __name__ == '__main__':
    asyncio.run(main())
