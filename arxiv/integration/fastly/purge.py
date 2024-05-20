from typing import List, Optional, Union, Any
import logging
import json

import fastly 
from fastly.api.purge_api import PurgeApi

from arxiv.config import settings

logger = logging.getLogger(__name__)

SERVICE_IDS=json.loads(settings.FASTLY_SERVICE_IDS)
MAX_PURGE_KEYS=256

def purge_fastly_keys(key:Union[str, List[str]], service_name: Optional[str]="arxiv.org"):
    """purges requested fastly surrogate keys for the service.
    If no service is specified default is the arxiv.org service
    """
    configuration = fastly.Configuration()
    configuration.api_token = settings.FASTLY_PURGE_TOKEN

    with fastly.ApiClient(configuration) as api_client:
        api_instance = PurgeApi(api_client)
        try:
            if isinstance(key, str):
                api_response=_purge_single_key(key, SERVICE_IDS[service_name], api_instance)
                logger.info(f"Fastly Purge service: {service_name}, key: {key}, status: {api_response.get('status')}, id: {api_response.get('id')}")
            else:
                _purge_multiple_keys(key, SERVICE_IDS[service_name], api_instance)
                logger.info(f"Fastly bulk purge complete service: {service_name}, keys: {key}")
        except fastly.ApiException as e:
            logger.error(f"Exception purging fastly key(s): {e} service: {service_name}, key: {key}")

def _purge_single_key(key:str, service_id: str, api_instance: PurgeApi)->Any:
    """purge all pages with a specific key from fastly, fastly will not indicate if the key does not exist"""
    options = {
        'service_id': service_id,
        'surrogate_key': key,
        'fastly_soft_purge':1
    }
    return api_instance.purge_tag(**options)

def _purge_multiple_keys(keys: List[str], service_id:str, api_instance: PurgeApi):
    """purge all pages with any of the requested keys from fastly
        calls itself recursively to stay within fastly maximum key amount
    """
    if len(keys)> MAX_PURGE_KEYS:
        _purge_multiple_keys(keys[0:MAX_PURGE_KEYS])
        _purge_multiple_keys(keys[MAX_PURGE_KEYS:])

    options = {
        'service_id': service_id,
        'purge_response': {'surrogate_keys':keys,},
        'fastly_soft_purge':1
    }
    api_response=api_instance.bulk_purge_tag(**options)
    logger.debug(f"Bulk purge keys response: {api_response}")
    return
