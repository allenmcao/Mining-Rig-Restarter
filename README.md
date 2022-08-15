# Mining Rig Restarter

This script automatically restarts mining rigs that repeatedly become unresponsive or shutdown.

## Requirements

- PC/Mining rig must have "Restore on AC/Power Loss" or similar enabled in BIOS
- Power must be supplied by a Kasa Smart Plug/Strip/etc.
- Mining on supported mining pool 
    - Currently only Flexpool, but expanding to Ethermine/F2Pool/Hiveon Pool

## Getting started
Install Python 3.5+ on your system if not installed yet.
After cloning the repository, install all the dependencies with:

```sh
pipenv install
```
Create a file `/rig-restarter/rigs.json` with the mandatory fields. Look at `/rig-restarter/rigs-example.json` for the simplest possible to immediately get started.

Once you are done, run `/rig-restarter/main.py` in order to launch the script.
For windows, 

## Config

An full example config is shown below, with mandatory fields on top and optional fields below.

```json
[
    {
        "status_api" : "flexpool",
        "wallet" : "0x1234abcde1234abcde12345abcde123456",
        "worker_name" : "Example_Worker",
        "kasa_device_ip" : "192.168.0.0",
        
        "smart_strip_plug_name" : "Example_Worker_Plug",
        "smart_strip_plug_number" : "Example_Worker_Plug",
        
        "power_cycle_on_delay" : 3,
        "time_until_offline" : 10,
        "status_check_frequency" : 5,
        "status_check_cooldown" : 10,
        "max_consecutive_restarts" : 3
    }
 ]
```

### Mandatory fields
- `status_api` is the type of pool API to query rig status from. Supported pool APIs will be in `/rig-restarter/pool_api_enum.py`
- `wallet` address that you are mining to. This is needed to query API
- `worker_name` used when mining to the pool. This is needed to filter API response to check status of correct rig.
- `kasa_device_ip` that corresponds to the local IP address of the smart device connected to your rig. For IP discovery, check the docs for `python-kasa` [here](https://github.com/python-kasa/python-kasa#discovering-devices)

### Optional Fields
- `smart_strip_plug_name` only if using a Kasa Smart Strip. Either this or plug number is required.
- `smart_strip_plug_number` only if using a Kasa Smart Strip. Either this or plug name is required.
- `power_cycle_on_delay` is the time in seconds to delay setting power back on during power cycle. Some rigs are more unstablea nd do not turn off fully without waiting, so require a longer delay to safely restart.
- `status_check_frequency`is the time in minutes for how often main loop runs for this particular rig restarter.
- `status_check_cooldown` is the time in minutes to wait after restarting a rig
- `max_consecutive_restarts` is the maximum times a rig can restart in a row before it is deemed unstable. The rig-restarter coroutine for that particular rig will be stopped, but other rr coroutines will continue to run.
