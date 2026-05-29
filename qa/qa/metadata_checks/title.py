from qa.metadata_checks.base import BaseCheck, BaseAggregatedCheck
from qa.metadata_checks.models import Disposition
from qa.metadata_checks.generic import (
    MaxLength,
    MinLength,
    NoDoubleSpaces,
    NoLeadingWhitespace,
    NoTrailingWhitespace,
    StartsWithCapital,
)


class TitleCheck(BaseAggregatedCheck):
    """Aggregated check for the metadata title field."""

    name = "title"
    version = "1.0"
    description = "Checks for the metadata title field."

    required_data = {}
    results_model = ""  # TODO

    _checks: tuple[BaseCheck, ...] = (
        MinLength(5, disposition=Disposition.REJECT),
        MaxLength(2000, disposition=Disposition.WARN),
        StartsWithCapital(disposition=Disposition.WARN),
        NoLeadingWhitespace(disposition=Disposition.WARN),
        NoTrailingWhitespace(disposition=Disposition.WARN),
        NoDoubleSpaces(disposition=Disposition.WARN),
    )
