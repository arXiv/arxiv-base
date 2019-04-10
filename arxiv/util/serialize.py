"""Tools for encoding/serializing data."""

from typing import Any, Union, List
import json
from datetime import datetime, date
from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()


class ISO8601JSONEncoder(json.JSONEncoder):
    """Renders date and datetime objects as ISO8601 datetime strings."""

    def default(self, obj: Any) -> Union[str, List[Any]]:
        """Overriden to render date(time)s in isoformat."""
        try:
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return json.JSONEncoder.default(self, obj)  # type: ignore


class ISO8601JSONDecoder(json.JSONDecoder):
    """Attempts to parse ISO8601 strings as datetime objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Pass :func:`object_hook` to the base constructor."""
        kwargs['object_hook'] = kwargs.get('object_hook', self.object_hook)
        super(ISO8601JSONDecoder, self).__init__(*args, **kwargs)

    def _try_isoparse(self, value: Any) -> Any:
        """Attempt to parse a value as an ISO8601 datetime."""
        if type(value) is not str:
            return value
        try:
            # Switched from dateutil.parser because it was too liberal.
            return datetime.fromisoformat(value)  # type: ignore
        except ValueError:
            return value

    def object_hook(self, data: dict, **extra: Any) -> Any:
        """Intercept and coerce ISO8601 strings to datetimes."""
        for key, value in data.items():
            if type(value) is list:
                data[key] = [self._try_isoparse(v) for v in value]
            else:
                data[key] = self._try_isoparse(value)
        return data


def dumps(obj: Any) -> str:
    """Generate JSON from a Python object."""
    return json.dumps(obj, cls=ISO8601JSONEncoder)


def loads(data: str) -> Any:
    """Load a Python object from JSON."""
    return json.loads(data, cls=ISO8601JSONDecoder)
