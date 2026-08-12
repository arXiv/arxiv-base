"""Generic control character and encoding checks."""

from qa.checks.base import BaseGenericPatternCheck


class DoesNotContainControlChars(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars"
    display_name = "Does Not Contain Control Chars"
    id = 10026
    version = "1.0.0"
    description = "The value does not contain control characters including newlines, tabs, and backspaces."
    failure_message = "Contains control characters: newlines, tabs, or backspaces."

    _pattern = r"[\u0000-\u001f]+"


class DoesNotContainControlCharsAllowNewlines(BaseGenericPatternCheck):
    name = "does_not_contain_control_chars_allow_newlines"
    display_name = "Does Not Contain Control Chars (Allow Newlines)"
    id = 10018
    version = "1.0.0"
    description = "The value does not contain control characters, but newlines (\\n) are permitted."
    failure_message = "Contains control characters."

    _pattern = r"[\u0000-\u0009\u000b-\u001f]+"


class NoUtf8DecodingErrors(BaseGenericPatternCheck):
    name = "no_utf8_decoding_errors"
    display_name = "No UTF-8 Decoding Errors"
    id = 10014
    version = "1.0.0"
    description = "The value does not contain malformed Unicode sequences."
    failure_message = "Bad Unicode encoding."

    _pattern = r"[\u00c0-\u00ff][\u0080-\u00bf]+"


class DoesNotContainRawNewline(BaseGenericPatternCheck):
    name = "does_not_contain_raw_newline"
    display_name = "Does Not Contain Raw Newline"
    id = 10057
    version = "1.0.0"
    description = "The value does not contain a raw newline or carriage return character."
    failure_message = "Contains a line break."

    _pattern = r"[\r\n]"
