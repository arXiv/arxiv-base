import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import tempfile
import sqlite3

# Without this import, Base.metadata does not get populated. So it may look doing nothing but do not remove this.
import arxiv.db.models

from arxiv.db.models import (
    MemberInstitution,
    MemberInstitutionContact,
    MemberInstitutionIP,
    AdminLog,
    AdminMetadata,
    ArchiveCategory,
    ArchiveDef,
    ArchiveGroup,
    Archive,
    AwsConfig,
    AwsFile,
    BibFeed,
    BibUpdate,
    BogusCountries,
    Category,
    QuestionableCategory,
    CategoryDef,
    ControlHold,
    CrossControl,
    DataciteDois,
    DBLPAuthor,
    DBLPDocumentAuthor,
    DocumentCategory,
    Document,
    DBLP,
    PaperPw,
    EndorsementDomain,
    EndorsementRequest,
    EndorsementRequestsAudit,
    Endorsement,
    EndorsementsAudit,
    FreezeLog,
    GroupDef,
    Group,
    JrefControl,
    License,
    LogPosition,
    Metadata,
    MirrorList,
    ModeratorApiKey,
    MonitorKlog,
    MonitorMailq,
    MonitorMailsent,
    NextMail,
    OrcidConfig,
    OwnershipRequest,
    OwnershipRequestsAudit,
    PaperOwner,
    PaperSession,
    PilotFile,
    PublishLog,
    RejectSessionUsername,
    SciencewisePing,
    ShowEmailRequest,
    State,
    StatsMonthlyDownload,
    StatsMonthlySubmission,
    SubmissionAgreement,
    SubmissionCategory,
    SubmissionCategoryProposal,
    SubmissionControl,
    SubmissionFlag,
    SubmissionHoldReason,
    SubmissionNearDuplicate,
    SubmissionQaReport,
    SubmissionViewFlag,
    Submission,
    PilotDataset,
    SubmissionAbsClassifierDatum,
    SubmissionClassifierDatum,
    SubmitterFlag,
    SuspectEmail,
    Title,
    TopPaper,
    TrackbackPing,
    TrackbackSite,
    Tracking,
    Updates,
    Version,
    DbixClassSchemaVersion,
    Session,
    TapirAddress,
    TapirAdminAudit,
    TapirCountry,
    TapirEmailChangeToken,
    TapirEmailHeader,
    TapirEmailLog,
    TapirEmailMailing,
    TapirEmailTemplate,
    TapirEmailToken,
    TapirIntegerVariable,
    TapirNickname,
    TapirNicknamesAudit,
    TapirPermanentToken,
    TapirPhone,
    TapirPolicyClass,
    TapirPresession,
    TapirRecoveryToken,
    TapirRecoveryTokensUsed,
    TapirSession,
    TapirSessionsAudit,
    TapirStringVariable,
    TapirString,
    TapirUser,
    AuthorIds,
    Demographic,
    OrcidIds,
    QueueView,
    SuspiciousName,
    SwordLicense,
    TapirDemographic,
    TapirUsersHot,
    TapirUsersPassword,
    SubmissionLocks,
    MembershipInstitutions,
    MembershipUsers,
    CheckRoles,
    CheckResultViews,
    CheckTargets,
    Checks,
    CheckResults,
    CheckResponses,
    flagged_user_comment,
    flagged_user_detail,
    flagged_user_detail_category_relation,
)

from .. import Base, LaTeXMLBase, session_factory, _classic_engine as classic_engine

def _make_schemas(db_uri: str):
    db_engine = create_engine(db_uri)

    SessionLocal = sessionmaker(autocommit=False, autoflush=True)
    SessionLocal.configure(bind=db_engine)
    db_session = SessionLocal(autocommit=False, autoflush=True)
    db_session.execute(text('select 1'))

    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    LaTeXMLBase.metadata.drop_all(db_engine)
    LaTeXMLBase.metadata.create_all(db_engine)

    db_session.commit()


def test_db_schema():
    """
    To test the MySQL and any other DB.

    Note that, it's not possible to create the accurate MySQL arXiv schema from python
    model. This is because the model object is NOT accurate representation of schema
    as it has to be able to create sqlite3 for testing.
    """
    db_uri = os.environ.get('TEST_ARXIV_DB_URI')
    if db_uri is None:
        print("db_uri is not defined. Bypassing the test")
        return
    _make_schemas(db_uri)


def test_db_schema_sqlite3():
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as tmp:
        filename = tmp.name
    # TIL - you need 4 slashes as the hostname is between 2nd and 3rd slashes
    _make_schemas("sqlite:///" + filename)
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    n_tables = 0
    for row in cur.fetchall():
        # print(row[0])
        n_tables += 1
    conn.close()
    # There are 151 tables in production
    assert n_tables == (145 + 3 + 3)
    os.unlink(filename)

def test_models():
    assert MemberInstitution()
    assert MemberInstitutionContact()
    assert MemberInstitutionIP()
    assert AdminLog()
    assert AdminMetadata()
    assert ArchiveCategory()
    assert ArchiveDef()
    assert ArchiveGroup()
    assert Archive()
    assert AwsConfig()
    assert AwsFile()
    assert BibFeed()
    assert BibUpdate()
    assert BogusCountries()
    assert Category()
    assert QuestionableCategory()
    assert CategoryDef()
    assert ControlHold()
    assert CrossControl()
    assert DataciteDois()
    assert DBLPAuthor()
    assert DBLPDocumentAuthor()
    assert DocumentCategory()
    assert Document()
    assert DBLP()
    assert PaperPw()
    assert EndorsementDomain()
    assert EndorsementRequest()
    assert EndorsementRequestsAudit()
    assert Endorsement()
    assert EndorsementsAudit()
    assert FreezeLog()
    assert GroupDef()
    assert Group()
    assert JrefControl()
    assert License()
    assert LogPosition()
    assert Metadata()
    assert MirrorList()
    assert ModeratorApiKey()
    assert MonitorKlog()
    assert MonitorMailq()
    assert MonitorMailsent()
    assert NextMail()
    assert OrcidConfig()
    assert OwnershipRequest()
    assert OwnershipRequestsAudit()
    assert PaperOwner()
    assert PaperSession()
    assert PilotFile()
    assert PublishLog()
    assert RejectSessionUsername()
    assert SciencewisePing()
    assert ShowEmailRequest()
    assert State()
    assert StatsMonthlyDownload()
    assert StatsMonthlySubmission()
    assert SubmissionAgreement()
    assert SubmissionCategory()
    assert SubmissionCategoryProposal()
    assert SubmissionControl()
    assert SubmissionFlag()
    assert SubmissionHoldReason()
    assert SubmissionNearDuplicate()
    assert SubmissionQaReport()
    assert SubmissionViewFlag()
    assert Submission()
    assert PilotDataset()
    assert SubmissionAbsClassifierDatum()
    assert SubmissionClassifierDatum()
    assert SubmitterFlag()
    assert SuspectEmail()
    assert Title()
    assert TopPaper()
    assert TrackbackPing()
    assert TrackbackSite()
    assert Tracking()
    assert Updates()
    assert Version()
    assert DbixClassSchemaVersion()
    assert Session()
    assert TapirAddress()
    assert TapirAdminAudit()
    assert TapirCountry()
    assert TapirEmailChangeToken()
    assert TapirEmailHeader()
    assert TapirEmailLog()
    assert TapirEmailMailing()
    assert TapirEmailTemplate()
    assert TapirEmailToken()
    assert TapirIntegerVariable()
    assert TapirNickname()
    assert TapirNicknamesAudit()
    assert TapirPermanentToken()
    assert TapirPhone()
    assert TapirPolicyClass()
    assert TapirPresession()
    assert TapirRecoveryToken()
    assert TapirRecoveryTokensUsed()
    assert TapirSession()
    assert TapirSessionsAudit()
    assert TapirStringVariable()
    assert TapirString()
    assert TapirUser()
    assert AuthorIds()
    assert Demographic()
    assert OrcidIds()
    assert QueueView()
    assert SuspiciousName()
    assert SwordLicense()
    assert TapirDemographic()
    assert TapirUsersHot()
    assert TapirUsersPassword()
    assert SubmissionLocks()
    assert MembershipInstitutions()
    assert MembershipUsers()
    assert CheckRoles()
    assert CheckResultViews()
    assert CheckTargets()
    assert Checks()
    assert CheckResults()
    assert CheckResponses()
    assert flagged_user_comment()
    assert flagged_user_detail()
    assert flagged_user_detail_category_relation()
    
