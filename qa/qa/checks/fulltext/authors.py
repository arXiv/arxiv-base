from qa.checks.base import BaseCheck

from qa.checks.models import AuthorCheckReport, OnFailurePolicy, QaDataRegistry, Result


class AuthorsFoundInFulltext(BaseCheck):
    name = "authors_found_in_fulltext"
    display_name = "Authors Found In Fulltext"
    id = 8
    version = "1.0.0"
    description = "Every metadata author was found in the full text."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Some authors from metadata not found in text."

    required_data = {"author_report"}

    # Flag written by the arxiv-qa check_authors cloud function.
    failure_flag_id = "missing-authors-fulltext"

    @classmethod
    def check(cls, author_report: AuthorCheckReport) -> Result:
        return cls().run(QaDataRegistry(author_report=author_report))

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "failure_flag_id": self.failure_flag_id,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        author_report = data_registry.author_report
        assert author_report is not None

        for flag in author_report.flags:
            if flag.id == self.failure_flag_id:
                return self._result(passed=False, message=flag.description or self.failure_message)
        return self._result(passed=True)
