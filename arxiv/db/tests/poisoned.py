"""
This is a test data for testing the test.

test_schema_checker.py reads this and the last line of this file triggers the uselist=False
while the LHS type contains List, so they contradict.
"""

from typing import Optional, List

from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arxiv.db import Base


class MemberInstitutionContact(Base):
    """For testing only"""

    __tablename__ = "Subscription_UniversalInstitutionContact"

    __table_args__ = {"mysql_charset": "utf8"}
    email: Mapped[Optional[str]] = mapped_column(String(255))

    sid: Mapped[int] = mapped_column(ForeignKey("Subscription_UniversalInstitution.id", ondelete="CASCADE"), nullable=False, index=True)

    # This is the poisoned relationship. Do not change.
    Subscription_UniversalInstitution: Mapped[List["MemberInstitution"]] = relationship("MemberInstitution", back_populates="Subscription_UniversalInstitutionContact", uselist=False)
