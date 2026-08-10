from qa.checks.models import SubmitEventInfo


def make_test_submit_event_info(
    type="new",
    is_oversize=False,
    submitter_name="Donald Duck",
    source_format="tex",
):
    return SubmitEventInfo(
        type=type,
        is_oversize=is_oversize,
        submitter_name=submitter_name,
        source_format=source_format,
    )
