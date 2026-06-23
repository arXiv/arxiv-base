"""Submission status codes for the arXiv_submissions table status column."""

WORKING = 0
"""Incomplete; not yet submitted."""
SUBMITTED = 1
"""Submitted and not on hold."""
ON_HOLD = 2
"""On hold."""
UNUSED = 3
NEXT = 4
"""Queued for the next announcement cycle."""
PROCESSING = 5
NEEDS_EMAIL = 6
PUBLISHED = 7
PUBLISHING = 8
"""In the publishing pipeline (text extraction, etc.)."""
REMOVED = 9
USER_DELETED = 10
ERROR_STATE = 19

# Expired (source files removed) variants — original status + 20
DELETED_WORKING = 20
"""Was working but source files expired."""
DELETED_ON_HOLD = 22
DELETED_PROCESSING = 25
DELETED_PUBLISHED = 27
"""Published and source files expired."""
DELETED_REMOVED = 29
DELETED_USER_DELETED = 30


STATUS_NAMES: dict[int, str] = {
    WORKING:            "working",
    SUBMITTED:          "submitted",
    ON_HOLD:            "on hold",
    UNUSED:             "unused",
    NEXT:               "next",
    PROCESSING:         "processing",
    NEEDS_EMAIL:        "needs email",
    PUBLISHED:          "published",
    PUBLISHING:         "publishing",
    REMOVED:            "removed",
    USER_DELETED:       "user deleted",
    ERROR_STATE:        "error state",
    DELETED_WORKING:    "deleted (working)",
    DELETED_ON_HOLD:    "deleted (on hold)",
    DELETED_PROCESSING: "deleted (processing)",
    DELETED_PUBLISHED:  "deleted (published)",
    DELETED_REMOVED:    "deleted (removed)",
    DELETED_USER_DELETED: "deleted (user deleted)",
}
