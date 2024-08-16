from typing import Dict, List
from werkzeug.datastructures import Headers

def add_surrogate_key(headers: Dict[str,str], keys:List[str])-> Headers:
    """adds surrogate key(s) to a response header, 
    will update the header dictionary with new keys while retaining the rest of the header information"""
    old_keys=f' {headers.get("Surrogate-Key","").strip()} '
    for key in keys:
        key=key.strip()
        if f" {key} " not in old_keys:
            old_keys+=key+" "
    headers.update({"Surrogate-Key":old_keys.strip()})        
    return headers