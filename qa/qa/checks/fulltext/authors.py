from qa.checks.base import BaseCheck

from qa.checks.models import AuthorCheckReport, OnFailurePolicy, QaDataRegistry, Result


class AuthorsFoundInFulltext(BaseCheck):
    name = "authors_found_in_fulltext"
    display_name = "Authors Found In Fulltext"
    id = 8
    version = "1.0.0"
    description = "The metadata authors were found in the full text, and none look anonymous or invalid."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Author check failed."

    required_data = {"author_report"}

    # Flags written by the arxiv-qa check_authors cloud function.
    failure_flag_ids = ("missing-authors-fulltext", "anonymous-authors", "bad-authors")

    @classmethod
    def check(cls, author_report: AuthorCheckReport) -> Result:
        return cls().run(QaDataRegistry(author_report=author_report))

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "failure_flag_ids": self.failure_flag_ids,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        author_report = data_registry.author_report
        assert author_report is not None

        failures = [flag for flag in author_report.flags if flag.id in self.failure_flag_ids]

        if failures:
            message = " ".join(flag.description or self.failure_message for flag in failures)
            return self._result(passed=False, message=message)
        return self._result(passed=True)
