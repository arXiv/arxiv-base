"""
Provide endorsement authorizations for users.

Endorsements are authorization scopes tied to specific classificatory
categories, and are used primarily to determine whether or not a user may
submit a paper with a particular primary or secondary classification.

This module preserves the behavior of the legacy system with respect to
interpreting endorsements and evaluating potential autoendorsement. The
relevant policies can be found on the `arXiv help pages
<https://arxiv.org/help/endorsement>`_.
"""

from typing import List, Dict, Optional, Callable, Set, Iterable, Union
from collections import Counter
from datetime import datetime
from functools import lru_cache as memoize
from itertools import groupby

from sqlalchemy.sql.expression import literal

from . import util
from .. import domain
from arxiv.taxonomy import definitions
from arxiv.db import session
from arxiv.db.models import TapirUser, Endorsement, t_arXiv_paper_owners, Document, \
    t_arXiv_in_category, Category, EndorsementDomain, t_arXiv_white_email, \
    t_arXiv_black_email


GENERAL_CATEGORIES = [
    definitions.CATEGORIES['math.GM'],
    definitions.CATEGORIES['physics.gen-ph'],
]

WINDOW_START = util.from_epoch(157783680)

Endorsements = List[Union[domain.Category,str]]


def get_endorsements(user: domain.User) -> Endorsements:
    """
    Get all endorsements (explicit and implicit) for a user.

    Parameters
    ----------
    user : :class:`.domain.User`

    Returns
    -------
    list
        Each item is a :class:`.domain.Category` for which the user is
        either explicitly or implicitly endorsed.

    """
    endorsements = list(set(explicit_endorsements(user))
                        | set(implicit_endorsements(user)))

    return endorsements


@memoize()
def _categories_in_archive(archive: str) -> Set[str]:
    return set(category for category, definition
               in definitions.CATEGORIES_ACTIVE.items()
               if definition.in_archive == archive)


@memoize()
def _category(archive: str, subject_class: str) -> domain.Category:
    if subject_class:
        return definitions.CATEGORIES[f'{archive}.{subject_class}']
    return definitions.CATEGORIES[archive]


@memoize()
def _get_archive(category: domain.Category) -> str:
    return category.in_archive
    archive: str
    if category.id.endswith(".*"):
        archive = category.id.split(".", 1)[0]
    else:
        try:
            archive = definitions.CATEGORIES_ACTIVE[category].in_archive
        except KeyError:
            if "." in category:
                archive = category.split(".", 1)[0]
            else:
                archive = ""
    return archive


def _all_archives(endorsements: Endorsements) -> bool:
    archives = set(_get_archive(category) for category in endorsements
                   if category.id.endswith(".*"))
    missing = set(definitions.ARCHIVES_ACTIVE.keys()) - archives
    return len(missing) == 0 or (len(missing) == 1 and 'test' in missing)


def _all_subjects_in_archive(archive: str, endorsements: Endorsements) -> bool:
    return len(_categories_in_archive(archive) - set(endorsements)) == 0


def compress_endorsements(endorsements: Endorsements) -> Endorsements:
    """
    Compress endorsed categories using wildcard notation if possible.

    We want to avoid simply enumerating all of the categories that exist. If
    all subjects in an archive are present, we represent that as "{archive}.*".
    If all subjects in all archives are present, we represent that as "*.*".

    Parameters
    ----------
    endorsements : list
        A list of endorsed categories.

    Returns
    -------
    list
        The same endorsed categories, compressed with wildcards where possible.

    """
    compressed: Endorsements = []
    grouped = groupby(sorted(endorsements, key=_get_archive), key=_get_archive)
    for archive, archive_endorsements in grouped:
        archive_endorsements_list = list(archive_endorsements)
        if _all_subjects_in_archive(archive, archive_endorsements_list):
            compressed.append(domain.Category(id=f"{archive}.*",
                                       full_name=f"all of {archive}",
                                       is_active=True,
                                       in_archive=archive,
                                       is_general=False,
                                       ))

        else:
            for endorsement in archive_endorsements_list:
                compressed.append(endorsement)
    if _all_archives(compressed):
        return list(definitions.CATEGORIES.values())
    return compressed


def explicit_endorsements(user: domain.User) -> Endorsements:
    """
    Load endorsed categories for a user.

    These are endorsements (including auto-endorsements) that have been
    explicitly commemorated.

    Parameters
    ----------
    user : :class:`.domain.User`

    Returns
    -------
    list
        Each item is a :class:`.domain.Category` for which the user is
        explicitly endorsed.

    """
    data: List[Endorsement] = (
        session.query(
            Endorsement.archive,
            Endorsement.subject_class,
            Endorsement.point_value,
        )
        .filter(Endorsement.endorsee_id == user.user_id)
        .filter(Endorsement.flag_valid == 1)
        .all()
    )
    pooled: Counter = Counter()
    for archive, subject, points in data:
        pooled[_category(archive, subject)] += points
    return [category for category, points in pooled.items() if points]


def implicit_endorsements(user: domain.User) -> Endorsements:
    """
    Determine categories for which a user may be autoendorsed.

    In the classic system, this was determined upon request, when the user
    attempted to submit to a particular category. Because we are separating
    authorization concerns (which includes endorsement) from the submission
    system itself, we want to calculate possible autoendorsement categories
    ahead of time.

    New development of autoendorsement-related functionality should not happen
    here. This function and related code are intended only to preserve the
    business logic already implemented in the classic system.

    Parameters
    ----------
    :class:`.User`

    Returns
    -------
    list
        Each item is a :class:`.domain.Category` for which the user may be
        auto-endorsed.

    """
    candidates = [definitions.CATEGORIES[category]
                  for category, data in definitions.CATEGORIES_ACTIVE.items()]
    policies = category_policies()
    invalidated = invalidated_autoendorsements(user)
    papers = domain_papers(user)
    user_is_academic = is_academic(user)
    return [
        category for category in candidates
        if category in policies
        and not _disqualifying_invalidations(category, invalidated)
        and (policies[category]['endorse_all']
             or _endorse_by_email(category, policies, user_is_academic)
             or _endorse_by_papers(category, policies, papers))
    ]


def is_academic(user: domain.User) -> bool:
    """
    Determine whether a user is academic, based on their email address.

    Uses whitelist and blacklist patterns in the database.

    Parameters
    ----------
    user : :class:`.domain.User`

    Returns
    -------
    bool

    """
    in_whitelist = (
        session.query(t_arXiv_white_email.c.pattern)
        .filter(literal(user.email).like(t_arXiv_white_email.c.pattern))
        .first()
    )
    if in_whitelist:
        return True
    in_blacklist = (
        session.query(t_arXiv_black_email.c.pattern)
        .filter(literal(user.email).like(t_arXiv_black_email.c.pattern))
        .first()
    )
    if in_blacklist:
        return False
    return True


def _disqualifying_invalidations(category: domain.Category,
                                 invalidated: Endorsements) -> bool:
    """
    Evaluate whether endorsement invalidations are disqualifying.

    This enforces the policy that invalidated (revoked) auto-endorsements can
    prevent future auto-endorsement.

    Parameters
    ----------
    category : :class:`.Category`
        The category for which an auto-endorsement is being considered.
    invalidated : list
        Categories for which the user has had auto-endorsements invalidated
        (revoked).

    Returns
    -------
    bool

    """
    return bool((category in GENERAL_CATEGORIES and category in invalidated)
                or (category not in GENERAL_CATEGORIES and invalidated))


def _endorse_by_email(category: domain.Category,
                      policies: Dict[domain.Category, Dict],
                      user_is_academic: bool) -> bool:
    """
    Evaluate whether an auto-endorsement can be issued based on email address.

    This enforces the policy that some categories allow auto-endorsement for
    academic users.

    Parameters
    ----------
    category : :class:`.Category`
        The category for which an auto-endorsement is being considered.
    policies : dict
        Describes auto-endorsement policies for each category (inherited from
        their endorsement domains).
    user_is_academic : bool
        Whether or not the user has been determined to be academic.

    Returns
    -------
    bool

    """
    policy = policies.get(category)
    if policy is None or 'endorse_email' not in policy:
        return False
    return policy['endorse_email'] and user_is_academic


def _endorse_by_papers(category: domain.Category,
                       policies: Dict[domain.Category, Dict],
                       papers: Dict[str, int]) -> bool:
    """
    Evaluate whether an auto-endorsement can be issued based on prior papers.

    This enforces the policy that some categories allow auto-endorsements for
    users who have published a minimum number of papers in categories that
    share an endoresement domain.

    Parameters
    ----------
    category : :class:`.Category`
        The category for which an auto-endorsement is being considered.
    policies : dict
        Describes auto-endorsement policies for each category (inherited from
        their endorsement domains).
    papers : dict
        The number of papers that the user has published in each endorsement
        domain. Keys are str names of endorsement domains, values are int.

    Returns
    -------
    bool

    """
    N_papers = papers.get(policies[category]['domain'], 0)
    min_papers = policies[category]['min_papers']
    return bool(N_papers >= min_papers)


def domain_papers(user: domain.User,
                  start_date: Optional[datetime] = None) -> Dict[str, int]:
    """
    Calculate the number of papers that a user owns in each endorsement domain.

    This includes both submitted and claimed papers.

    Parameters
    ----------
    user : :class:`.domain.User`
    start_date : :class:`.datetime` or None
        If provided, will only count papers published after this date.

    Returns
    -------
    dict
        Keys are classification domains (str), values are the number of papers
        in each respective domain (int).

    """
    query = session.query(t_arXiv_paper_owners.c.document_id,
                             Document.document_id,
                             t_arXiv_in_category.c.document_id,
                             Category.endorsement_domain) \
        .filter(t_arXiv_paper_owners.c.user_id == user.user_id) \
        .filter(Document.document_id == t_arXiv_paper_owners.c.document_id) \
        .filter(t_arXiv_in_category.c.document_id == Document.document_id) \
        .filter(Category.archive == t_arXiv_in_category.c.archive) \
        .filter(Category.subject_class == t_arXiv_in_category.c.subject_class)

    if start_date:
        query = query.filter(Document.dated > util.epoch(start_date))
    data = query.all()
    return dict(Counter(domain for _, _, _, domain in data).items())


def category_policies() -> Dict[domain.Category, Dict]:
    """
    Load auto-endorsement policies for each category from the database.

    Each category belongs to an endorsement domain, which defines the
    auto-endorsement policies. We retrieve those policies from the perspective
    of the individueal category for ease of lookup.

    Returns
    -------
    dict
        Keys are :class:`.domain.Category` instances. Values are dicts with
        policiy details.

    """
    data = session.query(Category.archive,
                            Category.subject_class,
                            EndorsementDomain.endorse_all,
                            EndorsementDomain.endorse_email,
                            EndorsementDomain.papers_to_endorse,
                            EndorsementDomain.endorsement_domain) \
        .filter(Category.definitive == 1) \
        .filter(Category.active == 1) \
        .filter(Category.endorsement_domain
                == EndorsementDomain.endorsement_domain) \
        .all()

    policies = {}
    for arch, subj, endorse_all, endorse_email, min_papers, e_domain in data:
        policies[_category(arch, subj)] = {
            'domain': e_domain,
            'endorse_all': endorse_all == 'y',
            'endorse_email': endorse_email == 'y',
            'min_papers': min_papers
        }

    return policies


def invalidated_autoendorsements(user: domain.User) -> Endorsements:
    """
    Load any invalidated (revoked) auto-endorsements for a user.

    Parameters
    ----------
    user : :class:`.domain.User`

    Returns
    -------
    list
        Items are :class:`.domain.Category` for which the user has had past
        auto-endorsements revoked.

    """
    data: List[Endorsement] = session.query(Endorsement.archive,
                                                 Endorsement.subject_class) \
        .filter(Endorsement.endorsee_id == user.user_id) \
        .filter(Endorsement.flag_valid == 0) \
        .filter(Endorsement.type == 'auto') \
        .all()
    return [_category(archive, subject) for archive, subject in data]
