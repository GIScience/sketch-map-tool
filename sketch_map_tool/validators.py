from string import Template
from typing import get_args
from uuid import UUID

import PIL.Image as Image
from werkzeug.datastructures import FileStorage

from sketch_map_tool import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import ValueError, UploadLimitsExceededError
from sketch_map_tool.models import LiteratureReference


def N_(s: str) -> str:  # noqa
    """Mark for translation."""
    return s


def validate_type(type_: REQUEST_TYPES):
    """Validate result type values for API parameter `type_`"""
    if type_ not in list(get_args(REQUEST_TYPES)):
        raise ValueError(
            N_(
                "{type} is not a valid value for the request parameter 'type'. "
                + "Allowed values are: {request_type}"
            ),
            {"type": type_, "request_type": REQUEST_TYPES},
        )


def validate_uploaded_sketchmaps(files: list[FileStorage]):
    """Validation function for uploaded files."""

    max_nr_simultaneous_uploads = int(get_config_value("max-nr-simultaneous-uploads"))
    max_pixel_per_image = int(get_config_value("max_pixel_per_image"))

    if len(files) > max_nr_simultaneous_uploads:
        raise UploadLimitsExceededError(
            f"You can only upload up to {max_nr_simultaneous_uploads} files at once."
        )

    for file in files:
        img = Image.open(file)
        total_pxl_cnt = img.size[0] * img.size[1]
        if total_pxl_cnt > max_pixel_per_image:
            raise UploadLimitsExceededError(
                f"You can only upload pictures up to "
                f"a total pixel count of {max_pixel_per_image}."
            )
        del img
        file.seek(0)


def validate_uuid(uuid: str):
    """validation function for endpoint parameter <uuid>"""
    try:
        _ = UUID(uuid, version=4)
    except ValueError as error:
        raise ValueError("The provided URL does not contain a valid UUID") from error


def validate_literature_reference(literature_reference: LiteratureReference):
    """Validate literature reference to not include empty strings."""
    if literature_reference.citation == "":
        raise ValueError(
            "Literature reference JSON fields "
            + "should not contain empty strings as values."
        )
    if literature_reference.img_src == "":
        raise ValueError(
            "Literature reference JSON fields should "
            + "not contain empty strings as values."
        )
    if literature_reference.url == "":
        raise ValueError(
            "Literature reference JSON fields should "
            + "not contain empty strings as values."
        )
