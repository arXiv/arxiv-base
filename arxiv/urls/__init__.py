from ..identifier import Identifier

def pdf_canonical_url (identifier: Identifier) -> str:
    # This won't include the version unless identifier 
    # was explicitly initialized with a version
    return f'https://arxiv.org/pdf/{identifier.idv}'
    
def html_canonical_url (identifier: Identifier) -> str:
    return f'https://arxiv.org/html/{identifier.idv}'

def abs_canonical_url (identifier: Identifier) -> str:
    return f'https://arxiv.org/abs/{identifier.idv}'