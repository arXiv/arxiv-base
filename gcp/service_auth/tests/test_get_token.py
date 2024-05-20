import os
import sys
import subprocess
import time
from typing import Generator

import pytest
import logging
import datetime
from pathlib import Path
import json

try:
    from gcp_service_auth import GcpIdentityToken
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from gcp_service_auth import GcpIdentityToken
    pass
                                 


@pytest.fixture(scope="module")
#@pytest.mark.with_op
def gcp_browse_cred() -> (Generator[str, str, str], str):
    logging.basicConfig(level=logging.DEBUG)
    cred_file = os.path.join(Path(__file__).parent, "browse-local.json")
    cred_file = cred_file
    if not os.path.exists(cred_file):
        subprocess.run(["op", "document", "get", "4feibaz4tzn6iwk5c7ggvb7xwi", "-o", cred_file])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_file
    op = subprocess.run(["op", "item", "get", "4feibaz4tzn6iwk5c7ggvb7xwi", "--format", "json"], stdout=subprocess.PIPE)
    test_meta = json.loads(op.stdout)
    test_url = ""
    for field in test_meta['fields']:
        if field["id"] == "heltf7phky3h6rnlvd7zi3542u":
            test_url = field["value"]
            break
    yield (cred_file, test_url)
    os.remove(cred_file)
    return ""

@pytest.mark.with_op
def test_get_token(gcp_browse_cred: (str, str)) -> None:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_browse_cred[0]
    logger = logging.getLogger("test")
    idt = GcpIdentityToken(gcp_browse_cred[0][1], logger=logger,
                           expiration=datetime.timedelta(seconds=1))
    token0 = idt.token
    time.sleep(2)
    token1 = idt.token
    assert token0 is not None
    assert token1 is not None
    assert token0 != token1

