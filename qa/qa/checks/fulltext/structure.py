from qa.checks.base import BaseCheck

from qa.checks.models import OnFailurePolicy, QaDataRegistry, Result


class FulltextNotTooShort(BaseCheck):
    name = "fulltext_not_too_short"
    display_name = "Fulltext Not Too Short"
    id = 15
    version = "1.0.0"
    description = "The full text extracted is not too short."
    on_failure_policy = OnFailurePolicy.WARN
    failure_message = "Text too short."

    required_data = {"fulltext"}

    min_chars = 10000
    min_words = 1400

    @classmethod
    def check(cls, fulltext: str) -> Result:
        return cls().run(QaDataRegistry(fulltext=fulltext))

    @property
    def config(self) -> dict:
        return {
            **super().config,
            "min_chars": self.min_chars,
            "min_words": self.min_words,
        }

    def _run(self, data_registry: QaDataRegistry) -> Result:
        fulltext = data_registry.fulltext
        assert fulltext is not None

        if len(fulltext) < self.min_chars and len(fulltext.split()) < self.min_words:
            return self._result(passed=False, message=self.failure_message)
        else:
            return self._result(passed=True)
