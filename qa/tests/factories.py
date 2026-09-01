from qa.checks.models import SubmitEventInfo, SubmitterProfile


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


def make_test_submitter_profile(is_suspect=False):
    return SubmitterProfile(is_suspect=is_suspect)
