from qa.checks.models import SubmitEventInfo


def make_test_submit_event_info(
    type="new",
    is_oversize=False,
    data_version=12345,
    metadata_version=23456,
    submitter_name="Donald Duck",
    user_is_flagged=False,
    source_format="tex",
):
    return SubmitEventInfo(
        type=type,
        is_oversize=is_oversize,
        data_version=data_version,
        metadata_version=metadata_version,
        submitter_name=submitter_name,
        user_is_flagged=user_is_flagged,
        source_format=source_format,
    )
