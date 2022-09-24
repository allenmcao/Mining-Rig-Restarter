import requests
import json

import exceptions
import log
from pools_enum import Pools

from datetime import datetime
from humanfriendly import format_timespan

def is_online_query(rig):
    """Queries correct API to determine online status. Returns pool stat for worker"""
    match rig.status_api:
        case Pools.FLEXPOOL.poolname:
            response = requests.get(Pools.FLEXPOOL.endpoint.format(rig.worker_name, rig.wallet, rig.coin))
            json_response = json.loads(response.content.decode())
            result = json_response['result']

            # Flexpool API sends stats for all workers even when suppling "worker_name" param, so need to parse
            if type(result) is list:
                for worker in result:
                    if (type(worker is dict) and 'name' in worker):
                        if (worker['name'] == rig.worker_name):
                            return worker
                    else:
                        raise exceptions.RRMissingFieldException('API Worker Result', 'name')
                raise exceptions.RRMissingWorkerException(rig.worker_name)
            elif type(result) is dict:
                if ('name' in result and result['name'] == rig.worker_name):
                    return worker
                raise exceptions.RRMissingWorkerException(rig.worker_name)
            else:
                raise exceptions.RRMissingWorkerException(rig.worker_name)

def is_online_calc(worker, t_offline):
    """Performs calculation to determine whether rig status is offline depending on given parameters.
    
    If time_until_offline is unspecified (<=0) then the 'isOnline' field is used to determine if online/offline.
    Last seen time is still calculated and returned in this instance.
    """
    last_seen_time = datetime.fromtimestamp(worker['lastSeen'])
    last_seen_delta = round((datetime.now() - last_seen_time).total_seconds())
    last_seen_message = f'Was last seen {format_timespan(last_seen_delta)} ago.'
    
    passed_online_check = t_offline > last_seen_delta / 60 if t_offline > 0 else worker['isOnline']
    
    if not passed_online_check:
        exceeds_message = f' This exceeds the allowed offline time of {t_offline} min.' if t_offline > 0 else ''
        log.logger.info(f'{worker["name"]} is OFFLINE. {last_seen_message}{exceeds_message}')
    else:
        log.logger.info(f'{worker["name"]} is ONLINE. {last_seen_message}')
    return passed_online_check

def is_online(rig):
    """Checks whether rig is online depending on pool type. Returns True if online, False if offline."""
    worker_json = is_online_query(rig)
    return is_online_calc(worker_json, rig.time_until_offline)