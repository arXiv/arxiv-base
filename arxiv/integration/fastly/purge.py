from typing import List, Optional, Union, Any, Tuple
import logging
import json
from datetime import date, timedelta
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

import fastly 
from fastly.api.purge_api import PurgeApi

from arxiv.config import settings
from arxiv.db import Session
from arxiv.db.models import Metadata, Updates
from arxiv.identifier import Identifier, IdentifierException
from arxiv.taxonomy.definitions import GROUPS
from arxiv.taxonomy.category import get_all_cats_from_string 


logger = logging.getLogger(__name__)

SERVICE_IDS=json.loads(settings.FASTLY_SERVICE_IDS)
MAX_PURGE_KEYS=256

def purge_cache_for_paper(paper_id:str, old_cats:Optional[str]=None):
    """purges all keys needed for an unspecified change to a paper
    clears everything related to the paper, as well as any list and year pages it is on
    old_cats: include this string if the paper undergoes a category change to also purge pages the paper may have been removed from (or new year pages it is added to)
    raises an IdentifierException if the paper_id is invalid, and KeyError if the category string contains invalid categories
    """
    arxiv_id = Identifier(paper_id)
    keys=_purge_category_change(arxiv_id, old_cats)
    keys.append(f'paper-id-{arxiv_id.id}')
    purge_fastly_keys(keys)
    return

def _get_category_and_date(arxiv_id:Identifier)-> Tuple[str, date]:
    """fetches the current categories for a paper as well as the last date it had announced changes to determine if it belongs in recent or new page
        extra days were added to accomidate for weekends and holidays, 
        these will occasionally purge new and recent papers more than is needed, but better to over clear than underclear
    """
    meta=aliased(Metadata)
    up=aliased(Updates)
    sub= (
        Session.query(
            meta.abs_categories,
            meta.document_id
        )
        .filter(meta.paper_id==arxiv_id.id)
        .filter(meta.is_current==1)
        .subquery()
    )

    result=(
        Session.query(
            sub.c.abs_categories,
            func.max(up.date)
        )
        .join(up, up.document_id==sub.c.document_id)
        .group_by(sub.c.document_id)
        .filter(up.action != "absonly")
        .first()
    )
    if not result:
        raise IdentifierException(f'paper id does not exist: {arxiv_id.id}')

    new_cats: str=result[0]
    recent_date: date=result[1]
    return new_cats, recent_date

def _purge_category_change(arxiv_id:Identifier, old_cats:Optional[str]=None )-> List[str]:
    """determines all list and year pages required for a category change to a paper
        returns list of all keys to purge
        does not include paths for the paper itself
        assumes categories will be provided as string like from abs_categories feild, but could be improved if categories could be specified in a list
    """
    grp_physics=GROUPS['grp_physics']
    new_cats, recent_date= _get_category_and_date(arxiv_id)

    #get time period affected
    today=date.today()
    new=False 
    recent=False
    if today - timedelta(days=3) <= recent_date: #farthest away a date on the new page would likely be
        new=True
    if today - timedelta(days=7) <= recent_date:
        recent=True
    
    groups, archives, cats = get_all_cats_from_string(new_cats, True)
    new_archive_ids={arch.id for arch in archives}
    list_pages={cat.id for cat in cats} | new_archive_ids
    if grp_physics in groups: #grp_physics is a group for catchup
        list_pages.add(grp_physics.id)

    year_pages=[]
    if old_cats: #clear any pages this paper may have been removed from or added to
        old_groups, old_archives, old_categories = get_all_cats_from_string(old_cats, True)
        old_cat_ids=  {cat.id for cat in old_categories}
        old_archive_ids={arch.id for arch in old_archives}
        list_pages= list_pages | old_cat_ids | old_archive_ids
        if grp_physics in old_groups: #grp_physics is a group for catchup
            list_pages.add(grp_physics.id)
        year_pages=  old_archive_ids.symmetric_difference(new_archive_ids)

    #collect all relevant keys
    keys=[]
    for cat in list_pages:
        keys.append(f'list-{arxiv_id.year:04d}-{cat}')
        keys.append(f'list-{arxiv_id.year:04d}-{arxiv_id.month:02d}-{cat}')
        if recent:
            keys.append(f'list-recent-{cat}')
        if new:
            keys.append(f'list-new-{cat}')
    for arch in year_pages:
        keys.append(f"year-{arch}-{arxiv_id.year:04d}")

    return keys

def purge_fastly_keys(key:Union[str, List[str]], service_name: Optional[str]="arxiv.org", soft_purge: Optional[bool]=False):
    """purges requested fastly surrogate keys for the service.
    If no service is specified default is the arxiv.org service
    defaults to hard purge
    """
    configuration = fastly.Configuration()
    configuration.api_token = settings.FASTLY_PURGE_TOKEN

    with fastly.ApiClient(configuration) as api_client:
        api_instance = PurgeApi(api_client)
        if isinstance(key, str):
            try:
                api_response=_purge_single_key(key, SERVICE_IDS[service_name], api_instance, soft_purge)
                logger.info(f"Fastly Purge service: {service_name}, key: {key}, status: {api_response.get('status')}, id: {api_response.get('id')}")
            except fastly.ApiException as e:
                logger.error(f"Exception purging fastly key(s): {e} service: {service_name}, key: {key}")
        else:
            try:
                _purge_multiple_keys(key, SERVICE_IDS[service_name], api_instance, soft_purge)
                logger.info(f"Fastly bulk purge complete service: {service_name}, keys ({len(key)}): {key}")
            except fastly.ApiException as e:
                logger.error(f"Exception purging fastly key(s): {e} service: {service_name}, for {len(key)} keys")

def _purge_single_key(key:str, service_id: str, api_instance: PurgeApi, soft_purge: bool=False)->Any:
    """purge all pages with a specific key from fastly, fastly will not indicate if the key does not exist"""
    options = {
        'service_id': service_id,
        'surrogate_key': key
    }
    if soft_purge:
        options['fastly_soft_purge']=1
    return api_instance.purge_tag(**options)

def _purge_multiple_keys(keys: List[str], service_id:str, api_instance: PurgeApi, soft_purge:bool):
    """purge all pages with any of the requested keys from fastly
        calls itself recursively to stay within fastly maximum key amount
    """
    if len(keys)> MAX_PURGE_KEYS:
        _purge_multiple_keys(keys[0:MAX_PURGE_KEYS], service_id, api_instance, soft_purge)
        _purge_multiple_keys(keys[MAX_PURGE_KEYS:], service_id, api_instance,soft_purge)
    else:
        options = {
            'service_id': service_id,
            'purge_response': {'surrogate_keys':keys,}
        }
        if soft_purge:
            options['fastly_soft_purge']=1
        api_response=api_instance.bulk_purge_tag(**options)
        #logger.debug(f"Bulk purge keys response: {api_response}")
    return
