# Mining Rig Restarter

This script automatically restarts mining rigs that repeatedly become unresponsive and/or often shutdown.

For each rig supplied in the config, an asyncio coroutine is created to monitor and restart that rig. This coroutine checks the rig status periodically and power-cyles the rig if it is determined to be offline. Coroutines are ran in parallel, and will error independently.

Coroutines are ran in parallel, and any error in one rig-restarter coroutine will fail independently, letting the others keep running.

If your rig is running HiveOS, there is a similar functionality with "Hashrate Watchdog" that will restart the rig when internet is lost or hashrate becomes too low. However, this will **not** work when the rig becomes unresponsive from crashing, which happens very often. Even long-running rigs may suddenly become unstable and will not report properly to HiveOS when losing connectivity, which is where this script comes in.

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
Create a file `/rig-restarter/rigs.json` with the mandatory fields. Look at `/rig-restarter/rigs-example.json` for the simplest possible config to get started.

Once you are done, run `/rig-restarter/main.py` in order to launch the script.


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

### Mandatory Fields
- `status_api` is the type of pool API to query rig status from. Supported pool APIs will be in `/rig-restarter/pool_api_enum.py`
- `wallet` address that you are mining to. This is needed to query API
- `worker_name` used when mining to the pool. This is needed to filter API response to check status of correct rig.
- `kasa_device_ip` that corresponds to the local IP address of the smart device connected to your rig. For IP discovery, check the docs for `python-kasa` [here](https://github.com/python-kasa/python-kasa#discovering-devices)

### Optional Fields
- `smart_strip_plug_name` to search which strip plug to power cycle. If using a Kasa Power Strip, either this or plug number is required.
- `smart_strip_plug_number` refers to the plug number to power cycle. If using a Kasa Power Strip, either this or plug name is required.
### Following fields will be defaulted for each pool:
- `power_cycle_on_delay` is the time in seconds to delay setting power back on during power cycle. Some rigs are more unstable and do not turn off fully without waiting, so require a longer delay to safely restart.
- `time_until_offline` is the time in minutes of unresponsiveness for the rig to be considered offline. This is determined by the delta between now and the last seen time (as given by pool API)
- `status_check_frequency`is the time in minutes for how often main loop runs for this particular rig restarter.
- `status_check_cooldown` is the time in minutes to wait after restarting a rig
- `max_consecutive_restarts` is the maximum times a rig can restart in a row before it is deemed unstable. The rig-restarter coroutine for that particular rig will be stopped, but other rr coroutines will continue to run.

## Supported Mining Pools
1. Flexpool
    - seems to generally update values every 5-10m, seems to be longer if rate-limited
    - `time_until_offline` is 10m as this is the longest it takes for the API to update
    - `status_check_frequency` is 5m as this is generally the earliest it can update
    - `status_check_cooldown` is 10m as this is the latest it would take to update, don't want to reset again
    - `max_consecutive_restarts` should depend more on the rig instability, but is left at 3 as a baseline

## Planned Features
- Create Rig object with fieldnames
    - Move methods like pool query to take a Rig object
- Allow log-file to be specified 
    - Log each day in separate file
- Handle case where worker is offline (so thus not returned in pool status API results)
- Improve project structure with util/
    - rig-restarter.py separated out (for single rig startups)
- Make JSON checking more robust (structured field checking, multiple error throwing)
- Add email/discord/telegram notifications for restarts and stats
- Add more supported APIs (Ethermine, F2Pool, HiveON)
    - Find more accurate way of checking if online or not bc Flexpool api seems to rate-limit updates when hitting api too often
- Add grafana or some other visualization solution to track hashrate, restarts, API update times, etc.
- Create and integrate dashboard to manually reset devices/create rig restarters
    - Add autodetect of smart devices to select from to eliminate need for kasa IP discovery