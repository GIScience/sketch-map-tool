import os
from io import BytesIO
from typing import get_args
from uuid import UUID

import PIL.Image as Image

from sketch_map_tool import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import UploadLimitsExceededError
from sketch_map_tool.models import LiteratureReference


def validate_type(type_: REQUEST_TYPES):
    """Validate result type values for API parameter `type_`"""
    if type_ not in list(get_args(REQUEST_TYPES)):
        raise ValueError(
            f"'{type_}' is not a valid value for the request parameter 'type'."
            + f" Allowed values are: {REQUEST_TYPES}"
        )


def validate_uploaded_sketchmap(file):
    """Validation function for uploaded files."""
    max_single_file_size = int(get_config_value("max_single_file_size"))
    max_pixel_per_image = int(get_config_value("max_pixel_per_image"))

    file_length = file.seek(0, os.SEEK_END)
    if file_length > max_single_file_size:
        raise UploadLimitsExceededError(
            f"You can only upload pictures "
            f"up to a filesize of {max_single_file_size}."
        )
    file.seek(0, os.SEEK_SET)
    content = file.read()
    img = Image.open(BytesIO(content))
    total_pxl_cnt = img.size[0] * img.size[1]
    if total_pxl_cnt > max_pixel_per_image:
        raise UploadLimitsExceededError(
            f"You can only upload pictures up to "
            f"a total pixel count of {max_pixel_per_image}."
        )
    return content


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
