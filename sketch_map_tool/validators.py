from typing import get_args
from uuid import UUID

from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.models import LiteratureReference


def validate_type(type_: REQUEST_TYPES):
    """Validate result type values for API parameter `type_`"""
    if type_ not in list(get_args(REQUEST_TYPES)):
        raise ValueError(
            f"'{type_}' is not a valid value for the request parameter 'type'."
            + f" Allowed values are: {REQUEST_TYPES}"
        )


def validate_uuid(uuid: str):
    """validation function for endpoint parameter <uuid>"""
    try:
        _ = UUID(uuid, version=4)
    except ValueError as error:
        raise ValueError("The provided URL does not contain a valid UUID") from error


def validate_literature_reference(literatur_reference: LiteratureReference):
    """Validate literatur reference to not include empty strings."""
    if literatur_reference.citation == "":
        raise ValueError(
            "Literature reference JSON fields "
            "should not contain empty strings as values."
        )
    if literatur_reference.img_src == "":
        raise ValueError(
            "Literature reference JSON fields "
            "should not contain empty strings as values."
        )
    if literatur_reference.url == "":
        raise ValueError(
            "Literature reference JSON fields "
            "should not contain empty strings as values."
        )
