from typing import get_args
from uuid import UUID

from sketch_map_tool.definitions import ALLOWED_TYPES


def validate_type(type_: ALLOWED_TYPES):
    """Validate result type values for API parameter `type_`"""
    if type_ not in list(get_args(ALLOWED_TYPES)):
        raise ValueError(
            f"'{type_}' is not a valid value for the request parameter 'type'."
            + f" Allowed values are: {ALLOWED_TYPES}"
        )


def validate_uuid(uuid: str):
    """validation function for endpoint parameter <uuid>"""
    try:
        _ = UUID(uuid, version=4)
    except ValueError as error:
        raise ValueError("The provided URL does not contain a valid UUID") from error
