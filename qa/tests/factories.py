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


def make_test_submitter_profile(
    is_suspect=False,
    user_id=108086,
    email="submitter@example.com",
    name="Donald Duck",
    submitter_url="https://arxiv.org/auth/admin/user-detail.php?tapir_id=108086",
):
    return SubmitterProfile(
        user_id=user_id,
        email=email,
        name=name,
        is_suspect=is_suspect,
    )
