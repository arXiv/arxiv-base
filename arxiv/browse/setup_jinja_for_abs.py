from typing import Any, Optional, Callable, Dict

from arxiv.browse.util.id_patterns import do_dois_id_urls_to_tags, do_id_to_tags, \
    do_dois_arxiv_ids_to_tags
from arxiv.browse.filters import line_feed_to_br, tex_to_utf, entity_to_utf, \
    single_doi_url
from arxiv.browse.domain.identifier import canonical_url

def setup_jinja_for_abs(jinja_env: Any,
                        ct_url_for: Callable[[str],str],
                        id_to_url: Callable[[str],Any],
                        email_hash: Callable[[str],Optional[str]])->None:
    """Add filters and functions to jinja_env for the abs page macros.
    
    Parameters
    ----------
    jinja_env: 
      Jinja env object to add globals and filters to.
      This function will be modified the jinja_env.
    ct_url_for: 
      Fuction from a url to a clickthrough url. 
    id_to_url: 
      Function from a arXiv id str to a URL str.
    email_hash:
      Function from an email address to a hash.
      The same mapping should be used to verify the hash.
      See arxiv-browse.factory for an example.
    """
    
    if not jinja_env.globals:
        jinja_env.globals = {}

    jinja_env.globals['canonical_url'] = canonical_url

    def ct_single_doi_filter(doi: str)->str:
        return single_doi_url(ct_url_for, doi)

    def contextualized_id_filter(text: str)->str:
        return do_id_to_tags(id_to_url, text)

    def contextualized_doi_id_url_filter(text: str)->str:
        return do_dois_id_urls_to_tags(id_to_url, ct_url_for, text)

    def ct_doi_filter(text: str)->str:
        return do_dois_arxiv_ids_to_tags(id_to_url,
                                         ct_url_for,
                                         text)

    if not jinja_env.filters:
        jinja_env.filters = {}

    jinja_env.filters['line_feed_to_br'] = line_feed_to_br
    jinja_env.filters['tex_to_utf'] = tex_to_utf
    jinja_env.filters['entity_to_utf'] = entity_to_utf

    jinja_env.filters['clickthrough_url_for'] = ct_url_for
    jinja_env.filters['show_email_hash'] = email_hash
    
    jinja_env.filters['single_doi_url'] = ct_single_doi_filter
    jinja_env.filters['arxiv_id_urls'] = contextualized_id_filter
    jinja_env.filters['arxiv_urlize'] = contextualized_doi_id_url_filter
    jinja_env.filters['arxiv_id_doi_filter'] = ct_doi_filter
