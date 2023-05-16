import os

import pytest

from sketch_map_tool.exceptions import FileNotFoundError_, UploadLimitsExceededError


def test_too_many_uploads(flask_client, sketch_map_markings_buffer_1):
    old_max_nr = os.getenv("SMT-MAX-NR-SIM-UPLOADS")
    os.environ["SMT-MAX-NR-SIM-UPLOADS"] = "2"
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
    if old_max_nr is None:
        os.unsetenv("SMT-MAX-NR-SIM-UPLOADS")
    else:
        os.environ["SMT-MAX-NR-SIM-UPLOADS"] = old_max_nr


def test_allowed_nr_of_uploads(flask_client, sketch_map_markings_buffer_1):
    # Successful run requires that a sketch map has been generated on the instance beforehand
    old_max_nr = os.getenv("SMT-MAX-NR-SIM-UPLOADS")
    os.environ["SMT-MAX-NR-SIM-UPLOADS"] = "2"
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
    if old_max_nr is None:
        os.unsetenv("SMT-MAX-NR-SIM-UPLOADS")
    else:
        os.environ["SMT-MAX-NR-SIM-UPLOADS"] = old_max_nr
