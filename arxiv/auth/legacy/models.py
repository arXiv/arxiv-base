"""ORM models for legacy user and session tables."""

from typing import  List

from sqlalchemy import Column, Enum, \
    ForeignKey, Integer, SmallInteger, String, Text, text
from sqlalchemy.orm import relationship

from .. import domain

db: SQLAlchemy = SQLAlchemy()


class TapirSession(db.Model):
    """
    Legacy arXiv session table.

    +----------------+-----------------+------+-------+---------+
    | Field          | Type            | Null | Key   | Default |
    +----------------+-----------------+------+-------+---------+
    | session_id     | int(4) unsigned | NO   | PRI   | NULL    |
    | user_id        | int(4) unsigned | NO   | MUL   | 0       |
    | last_reissue   | int(11)         | NO   |       | 0       |
    | start_time     | int(11)         | NO   | MUL   | 0       |
    | end_time       | int(11)         | NO   | MUL   | 0       |
    +--------------+-------------------+------+-------+---------+
    """

    __tablename__ = 'tapir_sessions'

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey('tapir_users.user_id'), nullable=False,
                     index=True, server_default=text("'0'"))
    last_reissue = Column(Integer, nullable=False, server_default=text("'0'"))
    start_time = Column(Integer, nullable=False, index=True,
                        server_default=text("'0'"))
    end_time = Column(Integer, nullable=False, index=True,
                      server_default=text("'0'"))

    user = relationship('TapirUser')


class TapirSessionsAudit(db.Model):
    """Legacy arXiv session audit table. Notably has a tracking cookie."""

    __tablename__ = 'tapir_sessions_audit'

    session_id = Column(
        ForeignKey('tapir_sessions.session_id'), primary_key=True,
        autoincrement="false", server_default=text("'0'")
    )
    ip_addr = Column(String(16), nullable=False, index=True,
                     server_default=text("''"))
    remote_host = Column(String(255), nullable=False,
                         server_default=text("''"))
    tracking_cookie = Column(String(255), nullable=False, index=True,
                             server_default=text("''"))

    session = relationship('TapirSession')


class TapirUser(db.Model):
    """Legacy user data table."""

    __tablename__ = 'tapir_users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    suffix_name = Column(String(50))
    share_first_name = Column(Integer, nullable=False, server_default=text("'1'"))
    share_last_name = Column(Integer, nullable=False, server_default=text("'1'"))
    email = Column(String(255), nullable=False, unique=True, server_default=text("''"))
    share_email = Column(Integer, nullable=False, server_default=text("'8'"))
    email_bouncing = Column(Integer, nullable=False, server_default=text("'0'"))
    policy_class = Column(
        ForeignKey('tapir_policy_classes.class_id'),
        nullable=False, index=True, server_default=text("'0'")
    )
    joined_date = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    joined_ip_num = Column(String(16), index=True)
    joined_remote_host = Column(String(255), nullable=False, server_default=text("''"))
    flag_internal = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_edit_users = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_edit_system = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_email_verified = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_approved = Column(Integer, nullable=False, index=True, server_default=text("'1'"))
    flag_deleted = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_banned = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_wants_email = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_html_email = Column(Integer, nullable=False, server_default=text("'0'"))
    tracking_cookie = Column(String(255), nullable=False, index=True, server_default=text("''"))
    flag_allow_tex_produced = Column(Integer, nullable=False, server_default=text("'0'"))


class TapirPolicyClass(db.Model):
    """Legacy authorization table."""

    __tablename__ = 'tapir_policy_classes'

    ADMIN = 1
    PUBLIC_USER = 2
    LEGACY_USER = 3
    POLICY_CLASSES = [
        {"name": "Administrator", "class_id": ADMIN, "description": ""},
        {"name": "Public user", "class_id": PUBLIC_USER, "description": ""},
        {"name": "Legacy user", "class_id": LEGACY_USER, "description": ""}
    ]

    class_id = Column(SmallInteger, primary_key=True)
    name = Column(String(64), nullable=False, server_default=text("''"))
    description = Column(Text, nullable=False)
    password_storage = Column(Integer, nullable=False,
                              server_default=text("'0'"))
    recovery_policy = Column(Integer, nullable=False,
                             server_default=text("'0'"))
    permanent_login = Column(Integer, nullable=False,
                             server_default=text("'0'"))

    @staticmethod
    def insert_policy_classes(session) -> None:
        """Insert all the policy classes for legacy."""
        data = session.query(TapirPolicyClass).all()
        if data:
            return

        for datum in TapirPolicyClass.POLICY_CLASSES:
            session.add(TapirPolicyClass(**datum))


class TapirUsersPassword(db.Model):
    """Legacy password table."""

    __tablename__ = 'tapir_users_password'

    user_id = Column(ForeignKey('tapir_users.user_id'), nullable=False,
                     server_default=text("'0'"), primary_key=True)
    password_storage = Column(Integer, nullable=False, index=True,
                              server_default=text("'0'"))
    password_enc = Column(String(50), nullable=False)

    user = relationship('TapirUser')


class TapirPermanentToken(db.Model):
    """
    Bearer token for user authentication.

    +-------------+-----------------+------+-----+---------+-------+
    | Field       | Type            | Null | Key | Default | Extra |
    +-------------+-----------------+------+-----+---------+-------+
    | user_id     | int(4) unsigned | NO   | PRI | 0       |       |
    | secret      | varchar(32)     | NO   | PRI |         |       |
    | valid       | int(1)          | NO   |     | 1       |       |
    | issued_when | int(4) unsigned | NO   |     | 0       |       |
    | issued_to   | varchar(16)     | NO   |     |         |       |
    | remote_host | varchar(255)    | NO   |     |         |       |
    | session_id  | int(4) unsigned | NO   | MUL | 0       |       |
    +-------------+-----------------+------+-----+---------+-------+
    """

    __tablename__ = 'tapir_permanent_tokens'

    user_id = Column(Integer, primary_key=True)
    secret = Column(String(32), primary_key=True)
    """Token."""
    valid = Column(Integer, nullable=False, server_default=text("'1'"))
    issued_when = Column(Integer, nullable=False, server_default=text("'0'"))
    """Epoch time."""
    issued_to = Column(String(16), nullable=False)
    """IP address of client."""
    remote_host = Column(String(255), nullable=False)
    session_id = Column(Integer, nullable=False, server_default=text("'0'"))


class TapirNickname(db.Model):
    """
    Users' usernames (because why not have a separate table).

    +--------------+------------------+------+-----+---------+----------------+
    | Field        | Type             | Null | Key | Default | Extra          |
    +--------------+------------------+------+-----+---------+----------------+
    | nick_id      | int(10) unsigned | NO   | PRI | NULL    | autoincrement  |
    | nickname     | varchar(20)      | NO   | UNI |         |                |
    | user_id      | int(4) unsigned  | NO   | MUL | 0       |                |
    | user_seq     | int(1) unsigned  | NO   |     | 0       |                |
    | flag_valid   | int(1) unsigned  | NO   | MUL | 0       |                |
    | role         | int(10) unsigned | NO   | MUL | 0       |                |
    | policy       | int(10) unsigned | NO   | MUL | 0       |                |
    | flag_primary | int(1) unsigned  | NO   |     | 0       |                |
    +--------------+------------------+------+-----+---------+----------------+
    """

    __tablename__ = 'tapir_nicknames'

    nick_id = Column(Integer, primary_key=True)
    nickname = Column(String(20), nullable=False, unique=True, index=True)
    user_id = Column(ForeignKey('tapir_users.user_id'), nullable=False,
                     server_default=text("'0'"))
    user_seq = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_valid = Column(Integer, nullable=False, server_default=text("'0'"))
    role = Column(Integer, nullable=False, server_default=text("'0'"))
    policy = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_primary = Column(Integer, nullable=False, server_default=text("'0'"))

    user = relationship('TapirUser')


# TODO: update based on recent schema changes.
class Demographic(db.Model):
    """Legacy user profiles."""

    __tablename__ = 'arXiv_demographics'

    TYPE_CHOICES = [
        (1, 'Staff'),
        (2, "Professor"),
        (3, "Post Doc"),
        (4, "Grad Student"),
        (5, "Other")
    ]
    """Legacy ranks in arXiv user profiles."""

    user_id = Column(ForeignKey('tapir_users.user_id'), nullable=False,
                     server_default=text("'0'"), primary_key=True)
    country = Column(String(2), nullable=False)
    affiliation = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    rank = Column('type', SmallInteger, nullable=True, server_default=None)
    archive = Column(String(16), nullable=True, server_default=text("'null'"))
    subject_class = Column(String(16), nullable=True, server_default=text("'null'"))
    original_subject_classes = Column(String(255), nullable=False)
    flag_group_physics = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_math = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_cs = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_nlin = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_q_bio = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_q_fin = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_stat = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_econ = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_eess = Column(Integer, nullable=False, server_default=text("'0'"))
    user = relationship('TapirUser')

    GROUP_FLAGS = [
        ('grp_physics', 'flag_group_physics'),
        ('grp_math', 'flag_group_math'),
        ('grp_cs', 'flag_group_cs'),
        ('grp_q-bio', 'flag_group_q_bio'),
        ('grp_q-fin', 'flag_group_q_fin'),
        ('grp_q-stat', 'flag_group_stat'),
        ('grp_q-econ', 'flag_group_econ'),
        ('grp_eess', 'flag_group_eess'),
    ]

    @property
    def groups(self) -> List[str]:
        """Active groups for this user profile."""
        return [group for group, column in self.GROUP_FLAGS
                if getattr(self, column) == 1]

    def to_domain(self) -> domain.UserProfile:
        """Generate a domain representation from this database instance."""
        if self.subject_class:
            category = domain.Category(f'{self.archive}.{self.subject_class}')
        else:
            category = domain.Category(f'{self.archive}')

        return domain.UserProfile(
            affiliation=self.affiliation,
            country=self.country,
            rank=self.rank,
            submission_groups=self.groups,
            default_category=category,
            homepage_url=self.url,
        )


class Endorsement(db.Model):
    """
    Category endorsements for arXiv users.

    +----------------+-----------------------------+------+-----+---------+
    | Field          | Type                        | Null | Key | Default |
    +----------------+-----------------------------+------+-----+---------+
    | endorsement_id | int(10) unsigned            | NO   | PRI | NULL    |
    | endorser_id    | int(10) unsigned            | YES  | MUL | NULL    |
    | endorsee_id    | int(10) unsigned            | NO   | MUL | 0       |
    | archive        | varchar(16)                 | NO   | MUL |         |
    | subject_class  | varchar(16)                 | NO   |     |         |
    | flag_valid     | int(1) unsigned             | NO   |     | 0       |
    | type           | enum('user','admin','auto') | YES  |     | NULL    |
    | point_value    | int(1) unsigned             | NO   |     | 0       |
    | issued_when    | int(10) unsigned            | NO   |     | 0       |
    | request_id     | int(10) unsigned            | YES  | MUL | NULL    |
    +----------------+-----------------------------+------+-----+---------+
    """

    __tablename__ = 'arXiv_endorsements'

    endorsement_id = Column(Integer, primary_key=True, nullable=False)
    endorser_id = Column(Integer, nullable=True, server_default=None)
    endorsee_id = Column(ForeignKey('tapir_users.user_id'), nullable=False,
                         server_default=text("'0'"))
    archive = Column(String(16), nullable=False)
    subject_class = Column(String(16), nullable=False)
    flag_valid = Column(Integer, nullable=False, server_default=text("'0'"))
    endorsement_type = Column('type', Enum('user', 'admin', 'auto'),
                              nullable=True, server_default=None)
    point_value = Column(Integer, nullable=False, server_default=text("'0'"))
    issued_when = Column(Integer, nullable=False, server_default=text("'0'"))
    request_id = Column(Integer, nullable=True, server_default=None)

    endorsee = relationship('TapirUser')


class EndorsementDomain(db.Model):
    """
    Encodes some policies about endorsement.

    +--------------------+----------------------+------+-----+---------+
    | Field              | Type                 | Null | Key | Default |
    +--------------------+----------------------+------+-----+---------+
    | endorsement_domain | varchar(32)          | NO   | PRI |         |
    | endorse_all        | enum('y','n')        | NO   |     | n       |
    | mods_endorse_all   | enum('y','n')        | NO   |     | n       |
    | endorse_email      | enum('y','n')        | NO   |     | y       |
    | papers_to_endorse  | smallint(5) unsigned | NO   |     | 4       |
    +--------------------+----------------------+------+-----+---------+
    """

    __tablename__ = 'arXiv_endorsement_domains'

    endorsement_domain = Column(String(32), primary_key=True)
    endorse_all = Column(Enum('y', 'n'), server_default='n')
    mods_endorse_all = Column(Enum('y', 'n'), server_default='n')
    endorse_email = Column(Enum('y', 'n'), server_default='n')
    papers_to_endorse = Column(Integer, nullable=False,
                               server_default=text("'4'"))


class Category(db.Model):
    """
    Metadata about arXiv categories.

    +--------------------+----------------------+------+-----+---------+
    | Field              | Type                 | Null | Key | Default |
    +--------------------+----------------------+------+-----+---------+
    | archive            | varchar(16)          | NO   | PRI |         |
    | subject_class      | varchar(16)          | NO   | PRI |         |
    | definitive         | int(1)               | NO   |     | 0       |
    | active             | int(1)               | NO   |     | 0       |
    | category_name      | varchar(255)         | YES  |     | NULL    |
    | endorse_all        | enum('y','n','d')    | NO   |     | d       |
    | endorse_email      | enum('y','n','d')    | NO   |     | d       |
    | papers_to_endorse  | smallint(5) unsigned | NO   |     | 0       |
    | endorsement_domain | varchar(32)          | YES  | MUL | NULL    |
    +--------------------+----------------------+------+-----+---------+
    """

    __tablename__ = 'arXiv_categories'

    archive = Column(String(16), primary_key=True)
    subject_class = Column(String(16), primary_key=True)
    definitive = Column(Integer, nullable=False, server_default=text("'0'"))
    active = Column(Integer, nullable=False, server_default=text("'0'"))
    endorsement_domain = Column(String(32), nullable=True)


class DBPaperOwners(db.Model):
    """
    Relates arXiv users to their owned papers.

    +-----------------+-----------------------+------+-----+---------+-------+
    | Field           | Type                  | Null | Key | Default | Extra |
    +-----------------+-----------------------+------+-----+---------+-------+
    | document_id     | mediumint(8) unsigned | NO   | PRI | 0       |       |
    | user_id         | int(10) unsigned      | NO   | PRI | 0       |       |
    | date            | int(10) unsigned      | NO   |     | 0       |       |
    | valid           | int(1) unsigned       | NO   |     | 0       |       |
    | flag_author     | int(1) unsigned       | NO   |     | 0       |       |
    +-----------------+-----------------------+------+-----+---------+-------+
    """

    __tablename__ = 'arXiv_paper_owners'

    document_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    date = Column(Integer, nullable=False, server_default=text("'0'"))
    flag_author = Column(Integer, nullable=False, server_default=text("'0'"))
    valid = Column(Integer, nullable=False, server_default=text("'0'"))


class Document(db.Model):
    """
    Represents an arXiv paper.

    +-----------------------+-----------------------+------+-----+---------+
    | Field                 | Type                  | Null | Key | Default |
    +-----------------------+-----------------------+------+-----+---------+
    | document_id           | mediumint(8) unsigned | NO   | PRI | NULL    |
    | paper_id              | varchar(20)           | NO   | UNI |         |
    | title                 | varchar(255)          | NO   | MUL |         |
    | authors               | text                  | YES  |     | NULL    |
    | submitter_email       | varchar(64)           | NO   | MUL |         |
    | submitter_id          | int(10) unsigned      | YES  | MUL | NULL    |
    | dated                 | int(10) unsigned      | NO   | MUL | 0       |
    | primary_subject_class | varchar(16)           | YES  |     | NULL    |
    | created               | datetime              | YES  |     | NULL    |
    +-----------------------+-----------------------+------+-----+---------+
    """

    __tablename__ = 'arXiv_documents'

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(20), nullable=False, unique=True)
    dated = Column(Integer, nullable=False, server_default=text("'0'"))


class DBDocumentInCategory(db.Model):
    """
    M2M intermediate table for documents and their categories.

    +---------------+-----------------------+------+-----+---------+-------+
    | Field         | Type                  | Null | Key | Default | Extra |
    +---------------+-----------------------+------+-----+---------+-------+
    | document_id   | mediumint(8) unsigned | NO   | PRI | 0       |       |
    | archive       | varchar(16)           | NO   | PRI |         |       |
    | subject_class | varchar(16)           | NO   | PRI |         |       |
    | is_primary    | tinyint(1)            | NO   |     | 0       |       |
    +---------------+-----------------------+------+-----+---------+-------+
    """

    __tablename__ = 'arXiv_in_category'

    document_id = Column(Integer, primary_key=True)
    archive = Column(String(16), primary_key=True)
    subject_class = Column(String(16), primary_key=True)
    is_primary = Column(Integer, nullable=False, server_default=text("'0'"))


class DBEmailWhitelist(db.Model):
    """
    Patterns for identifying academic addresses.

    pattern | varchar(64) | YES  |     | NULL    |
    """

    __tablename__ = 'arXiv_white_email'

    pattern = Column(String(64), primary_key=True)


class DBEmailBlacklist(db.Model):
    """
    Patterns for identifying non-academic addresses.

    pattern | varchar(64) | YES  |     | NULL    |
    """

    __tablename__ = 'arXiv_black_email'

    pattern = Column(String(64), primary_key=True)
