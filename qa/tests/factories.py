from qa.checks.models import SubmitEventInfo


def make_test_submit_event_info(
    type="new",
    is_oversize=False,
    metadata_version=23456,
    submitter_name="Donald Duck",
    source_format="tex",
):
    return SubmitEventInfo(
        type=type,
        is_oversize=is_oversize,
        metadata_version=metadata_version,
        submitter_name=submitter_name,
        source_format=source_format,
    )
