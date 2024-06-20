"""Defines user concepts for use in arXiv services."""


from typing import Any, Optional, List, NamedTuple
from collections.abc import Iterable

from datetime import datetime
from pytz import timezone, UTC

from pydantic import BaseModel, ConfigDict, ValidationError, validator
from arxiv.taxonomy.category import Category
from arxiv.taxonomy import definitions
from arxiv.db.models import Demographic

EASTERN = timezone('US/Eastern')

STAFF = ('1', 'Staff')
PROFESSOR = ('2', 'Professor')
POST_DOC = ('3', 'Post doc')
GRAD_STUDENT = ('4', 'Grad student')
OTHER = ('5', 'Other')
RANKS = [STAFF, PROFESSOR, POST_DOC, GRAD_STUDENT, OTHER]


def _check_category(data: Any) -> Category:
    if isinstance(data, Category):
        return data
    if not isinstance(data, str):
        raise ValidationError(f"object of type {type(data)} cannnot be used as a Category", Category)
    cat = Category(data)
    cat.name # possible rasie value error on non-existance
    return cat


class UserProfile(BaseModel):
    """User profile data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    affiliation: str
    """Institutional affiliation."""

    country: str
    """Should be an ISO 3166-1 alpha-2 country code."""

    rank: int
    """Academic rank. Must be one of :const:`.RANKS`."""

    submission_groups: List[str]
    """
    Groups to which the user prefers to submit.

    Items should be one of :ref:`arxiv.taxonomy.definitions.GROUPS`.
    """

    default_category: Optional[Category]
    """
    Default submission category.

    Should be one of :ref:`arxiv.taxonomy.CATEGORIES`.
    """

    # @validator('default_category')
    # @classmethod
    # def check_category(cls, data: Any) -> Category:
    #     """Checks if `data` is a category."""
    #     return _check_category(data)

    homepage_url: str = ''
    """User's homepage or external profile URL."""

    remember_me: bool = True
    """Indicates whether the user prefers permanent session cookies."""

    @property
    def rank_display(self) -> str:
        """The display name of the user's rank."""
        _rank: str = dict(RANKS)[str(self.rank)]
        return _rank

    @property
    def default_archive(self) -> Optional[str]:
        """The archive of the default category."""
        return self.default_category.in_archive if self.default_category else None

    @property
    def default_subject(self) -> Optional[str]:
        """The subject of the default category."""
        if self.default_category is not None:
            subject: str
            if '.' in self.default_category.id:
                subject = self.default_category.id.split('.', 1)[1]
            else:
                subject = self.default_category.id
            return subject
        return None

    @property
    def groups_display(self) -> str:
        """Display-ready representation of active groups for this profile."""
        return ", ".join([
            definitions.GROUPS[group]['name']
            for group in self.submission_groups
        ])
    
    @staticmethod
    def from_orm (model: Demographic) -> 'UserProfile':
        if model.subject_class:
            category = definitions.CATEGORIES[f'{model.archive}.{model.subject_class}']
        elif model.archive:
            category = definitions.CATEGORIES[f'{model.archive}']
        else:
            category = None

        return UserProfile(
            affiliation=model.affiliation,
            country=model.country,
            rank=model.type,
            submission_groups=model.groups,
            default_category=category,
            homepage_url=model.url,
        )


class Scope(str):
    """Represents an authorization policy."""

    def __new__(cls, domain, action=None, resource=None):
        """Handle __new__."""
        return str.__new__(cls, cls.from_parts(domain, action, resource))

    @property
    def domain(self) -> str:
        """
        The domain to which the scope applies.

        This will generally refer to a specific service.
        """
        return self.parts[0]

    @property
    def action(self) -> str:
        """An action within ``domain`."""
        return self.parts[1]

    @property
    def resource(self) -> Optional[str]:
        """The specific resource to which this policy applies."""
        return self.parts[2]

    @property
    def parts(self) -> str:
        """Get parts of the Scope."""
        parts = self.split(':')
        parts = parts + [None] * (3 - len(parts))
        return parts

    def for_resource(self, resource_id: str) -> 'Scope':
        """Create a copy of this scope with a specific resource."""
        return Scope(domain=self.domain, action=self.action, resource=resource_id)

    def as_global(self) -> 'Scope':
        """Create a copy of this scope with a global resource."""
        return self.for_resource('*')

    @classmethod
    def from_parts(cls, domain, action=None, resource=None):
        """Create a scope string from parts."""
        return ":".join([o for o in [domain,action,resource] if o is not None])

    @classmethod
    def to_parts(cls, scopestr):
        """Split a scop string to parts."""
        parts = scopestr.split(':')
        return parts + [None] * (3 - len(parts))

    @classmethod
    def from_str(cls, scopestr:str) -> "Scope":
        """Make a Scope from a string."""
        parts = cls.to_parts(scopestr)
        return cls(domain=parts[0], action=parts[1], resource=parts[2])


class Authorizations(BaseModel):
    """Authorization information, e.g. associated with a :class:`.Session`."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    classic: int = 0
    """Capability code associated with a user's session."""

    endorsements: List[Category] = []
    """Categories to which the user is permitted to submit."""

    @validator('endorsements')
    @classmethod
    def check_endorsements(cls, data: Any) -> List[Category]:
        """Checks if `data` contains endorsements."""
        if isinstance(data, str) or not issubclass(type(data), Iterable):
            raise ValidationError("endorsements must be a list", cls)
        return [ _check_category(obj) for obj in data ]


    scopes: List[str] = []
    """Authorized :class:`.scope`s. See also :mod:`arxiv.users.auth.scopes`."""

    def endorsed_for(self, category: Category) -> bool:
        """
        Check whether category is included in this endorsement authorization.

        If a user/client is authorized for all categories in a particular
        archive, the category names in :attr:`Authorization.endorsements` will
        be compressed to a wilcard ``archive.*`` representation. If the
        user/client is authorized for all categories in the system, this will
        be compressed to "*.*".

        Parameters
        ----------
        category : :class:`.Category`

        Returns
        -------
        bool

        """
        archive = category.split(".", 1)[0] if "." in category else category
        endorsement_ids = [ cat if isinstance(cat, str) else cat.id for cat in self.endorsements]
        return (category.id in endorsement_ids
                or f"{archive}.*" in endorsement_ids
                or "*.*" in endorsement_ids)

    @classmethod
    def before_init(cls, data: dict) -> None:
        """Make sure that endorsements are :class:`.Category` instances."""
        # Iterative coercion is hard. It's a lot easier to handle this here
        # than to implement a general-purpose coercsion.
        # if self.endorsements and type(self.endorsements[0]) is not Category:
        data['endorsements'] = [
            Category(obj) for obj in data.get('endorsements', [])
        ]
        if 'scopes' in data:
            if type(data['scopes']) is str:
                data['scopes'] = [
                    Scope(*scope.split(':')) for scope
                    in data['scopes'].split()
                ]
            elif type(data['scopes']) is list:
                data['scopes'] = [
                    Scope(**scope) if type(scope) is dict
                    else Scope(*scope.split(':'))
                    for scope in data['scopes']
                ]


class UserFullName(BaseModel):
    """Represents a user's full name."""

    forename: str
    """First name or given name."""

    surname: str
    """Last name or family name."""

    suffix: Optional[str] = ''
    """Any title or qualifier used as a suffix/postfix."""


class User(BaseModel):
    """Represents an arXiv user and their authorizations."""

    username: str
    """Slug-like username."""

    email: str
    """The user's primary e-mail address."""

    user_id: Optional[str] = None
    """Unique identifier for the user. If ``None``, the user does not exist."""

    name: Optional[UserFullName] = None
    """The user's full name (if available)."""

    profile: Optional[UserProfile] = None
    """The user's account profile (if available)."""

    verified: bool = False
    """Whether or not the users' e-mail address has been verified."""

    # def asdict(self) -> dict:
    #     """Generate a dict representation of this :class:`.User`."""
    #     data = super(User, self)._asdict()
    #     if self.name is not None:
    #         data['name'] = self.name._asdict()
    #     if self.profile is not None:
    #         data['profile'] = self.profile._asdict()
    #     return data

    # TODO: consider whether this information is relevant beyond the
    # ``arxiv.users.legacy.authenticate`` module.
    #
    # approved: bool = True
    # """Whether or not the users' account is approved."""
    #
    # banned: bool = False
    # """Whether or not the user has been banned."""
    #
    # deleted: bool = False
    # """Whether or not the user has been deleted."""


class Client(BaseModel):
    """API client."""

    owner_id: str
    """The arXiv user responsible for the client."""

    client_id: Optional[str] = None
    """Unique identifier for a :class:`.Client`."""

    name: Optional[str] = None
    """Human-friendly name of the API client."""

    url: Optional[str] = None
    """Homepage or other resource describing the API client."""

    description: Optional[str] = None
    """Brief description of the API client."""

    redirect_uri: Optional[str] = None
    """The authorized redirect URI for the client."""


class Session(BaseModel):
    """Represents an authenticated session in the arXiv system."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    """Unique identifier for the session."""

    start_time: datetime
    """The ISO-8601 datetime when the session was created."""

    user: Optional[User] = None
    """The user for which the session was created."""

    client: Optional[Client] = None
    """The client for which the session was created."""

    end_time: Optional[datetime] = None
    """The ISO-8601 datetime when the session ended."""

    authorizations: Optional[Authorizations] = None
    """Authorizations for the current session."""

    ip_address: Optional[str] = None
    """The IP address of the client for which the session was created."""

    remote_host: Optional[str] = None
    """The hostname of the client for which the session was created."""

    nonce: Optional[str] = None
    """A pseudo-random nonce generated when the session was created."""

    def is_authorized(self, scope: Scope, resource: str) -> bool:
        """Check whether this session is authorized for a specific resource."""
        return (self.authorizations is not None and (
                scope.as_global() in self.authorizations.scopes
                or scope.for_resource(resource) in self.authorizations.scopes))

    @property
    def expired(self) -> bool:
        """Expired if the current time is later than :attr:`.end_time`."""
        return bool(self.end_time is not None
                    and datetime.now(tz=UTC) >= self.end_time)

    @property
    def expires(self) -> Optional[int]:
        """
        Number of seconds until the session expires.

        If the session is already expired, returns 0.
        """
        if self.end_time is None:
            return None
        duration = (self.end_time - datetime.now(tz=UTC)).total_seconds()
        return int(max(duration, 0))

    def json_safe_dict(self) -> dict:
        """Creates a json dict with the datetimes converted to ISO datetime strs."""
        out = self.dict()
        if self.start_time:
            out['start_time'] = self.start_time.isoformat()
        if self.end_time:
            out['end_time'] = self.end_time.isoformat()
        return out

def session_from_dict(data: dict) -> Session:
    """Create a Session from a dict."""
    return Session.parse_obj(data)
