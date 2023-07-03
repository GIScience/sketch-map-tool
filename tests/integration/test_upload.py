import os
from unittest import mock

import pytest

from sketch_map_tool.exceptions import FileNotFoundError_, UploadLimitsExceededError


@mock.patch.dict(os.environ, {"SMT-MAX-NR-SIM-UPLOADS": "2"})
def test_too_many_uploads(flask_client, sketch_map_markings_buffer_1):
    with pytest.raises(UploadLimitsExceededError):
        flask_client.post(
            "/digitize/results",
            data=dict(
                file=[
                    (sketch_map_markings_buffer_1, "file1.png"),
                    (sketch_map_markings_buffer_1, "file2.png"),
                    (sketch_map_markings_buffer_1, "file3.png"),
                ],
            ),
            follow_redirects=True,
        )


@mock.patch.dict(os.environ, {"SMT-MAX-NR-SIM-UPLOADS": "2"})
def test_allowed_nr_of_uploads(flask_client, sketch_map_markings_buffer_1):
    # Successful run requires that a sketch map has been generated on the instance beforehand
    with pytest.raises(
        FileNotFoundError_
    ):  # uuid of test image not in database, but the exception shows that the uploads have been accepted and processed
        flask_client.post(
            "/digitize/results",
            data=dict(
                file=[
                    (sketch_map_markings_buffer_1, "file1.png"),
                    (sketch_map_markings_buffer_1, "file2.png"),
                ],
            ),
            follow_redirects=True,
        )
