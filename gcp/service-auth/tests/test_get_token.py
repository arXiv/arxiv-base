import os
import subprocess
import time
from typing import Generator

import pytest
import logging
import datetime
from pathlib import Path

from gcp_service_auth import GcpIdentityToken

dev_target = "https://gcp-genpdf-6lhtms3oua-uc.a.run.app"

@pytest.fixture(scope="module")
#@pytest.mark.with_op
def gcp_browse_cred() -> Generator[str, str, str]:
    logging.basicConfig(level=logging.DEBUG)
    cred_file = os.path.join(Path(__file__).parent, "browse-local.json")
    cred_file = cred_file
    if not os.path.exists(cred_file):
        subprocess.run(["op", "document", "get", "4feibaz4tzn6iwk5c7ggvb7xwi", "-o", cred_file])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_file
    yield cred_file
    os.remove(cred_file)
    return ""

@pytest.mark.with_op
def test_get_token(gcp_browse_cred: str) -> None:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_browse_cred
    logger = logging.getLogger("test")
    idt = GcpIdentityToken(dev_target, logger=logger,
                           expiration=datetime.timedelta(seconds=1))
    token0 = idt.token
    time.sleep(2)
    token1 = idt.token
    assert token0 is not None
    assert token1 is not None
    assert token0 != token1
