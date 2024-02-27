"""
Cornell Server Farm file and GCP storage object path mapping.
"""
from os.path import dirname
from arxiv.identifier import Identifier as arXivID
import logging

logger = logging.getLogger(__name__)

class PathConstant:
    """Paths used on webX."""

    GS_KEY_PREFIX: str
    CACHE_PREFIX: str
    PS_CACHE_PREFIX: str
    FTP_PREFIX: str
    DATA_PREFIX: str
    ORIG_PREFIX: str

    def __init__(self) -> None:
        self.GS_KEY_PREFIX = '/ps_cache'
        self.CACHE_PREFIX = '/cache'
        self.PS_CACHE_PREFIX = '/cache/ps_cache'
        self.FTP_PREFIX = '/data/ftp'
        self.DATA_PREFIX = '/data'
        self.ORIG_PREFIX = '/data/orig'


CONSTANTS = PathConstant()


def local_path_to_blob_key(local_path: str) -> str:
    """Handles both source and cache files. Should handle pdfs, abs, txt
    and other types of files under these directories. Bucket key should
    not start with a /"""
    if str(local_path).startswith(CONSTANTS.CACHE_PREFIX + "/"):
        return str(local_path).replace(CONSTANTS.CACHE_PREFIX + "/", '')
    elif str(local_path).startswith(CONSTANTS.DATA_PREFIX + "/"):
        return str(local_path).replace(CONSTANTS.DATA_PREFIX + "/", '')
    else:
        # noinspection LongLine
        logger.error("path_to_bucket_key: %s does not start with %s or %s",
                     local_path, CONSTANTS.CACHE_PREFIX, CONSTANTS.DATA_PREFIX)
        raise ValueError(f"Cannot convert PDF path {local_path} to a GS key")


def arxiv_id_to_local_paper(arxiv_id: arXivID, extent: str=".abs", prefix: str="") -> str:
    """Latest submission file path."""
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    return f"{CONSTANTS.FTP_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}{extent}"


def arxiv_id_to_local_pdf_path(arxiv_id: arXivID, extent: str=".pdf", prefix: str="") -> str:
    """"ID to local path for PDFs"""
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    # noinspection LongLine
    if arxiv_id.has_version:
        return f"{CONSTANTS.PS_CACHE_PREFIX}/{archive}/pdf/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}v{arxiv_id.version}{extent}"
    return f"{CONSTANTS.PS_CACHE_PREFIX}/{archive}/pdf/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}{extent}"

# For reference only
# def arxiv_id_to_local_data(arxiv_id: arXivID, extent=".abs", prefix="") -> str:
#     """ID to local data path - mainly for abs."""
#     archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
#     # noinspection LongLine
#     return f"{CONSTANTS.DATA_PREFIX}/{archive}/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}v{arxiv_id.version}{extent}"

def arxiv_id_to_local_orig(arxiv_id: arXivID, extent: str=".abs", prefix: str="") -> str:
    """ID to lcaol original submission files."""
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    # noinspection LongLine
    if arxiv_id.has_version:
        return f"{CONSTANTS.ORIG_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}v{arxiv_id.version}{extent}"
    return f"{CONSTANTS.ORIG_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{prefix}{arxiv_id.filename}{extent}"

def arxiv_id_to_pdf_blob_key(arxiv_id: arXivID) -> str:
    """Map the local file path to the GCP bucket key"""
    return local_path_to_blob_key(arxiv_id_to_local_pdf_path(arxiv_id))


def blob_pdf_root(yymm: str | None=None) -> str:
    if yymm:
        id = arXivID(f"{yymm}.00001v1")
        return dirname(arxiv_id_to_pdf_blob_key(id)) + "/"
    return GCPPDFROOT

def blob_orig_root(yymm: str | None=None) -> str:
    if yymm:
        id = arXivID(f"{yymm}.00001v1")
        return dirname(local_path_to_blob_key(arxiv_id_to_local_orig(id))) + "/"
    return GCPORIGROOT

# weird
GCPPDFROOT = dirname(blob_pdf_root("2301")[:-1]) + "/"
GCPORIGROOT = dirname(blob_orig_root("2301")[:-1]) + "/"

def arxiv_id_to_pdf_url(host: str, arxiv_id: arXivID) -> str:
    """This is to map the arXiv ID to webX url.
    Since this has nothing to do with GCP, it is kind of an alien here.
    """
    if arxiv_id.has_version:
        return f"https://{host}/pdf/{arxiv_id.filename}v{arxiv_id.version}.pdf"
    return f"https://{host}/pdf/{arxiv_id.filename}.pdf"

