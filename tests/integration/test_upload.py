import os
from io import BytesIO

import pytest

from sketch_map_tool.exceptions import UploadLimitsExceededError


def test_too_many_uploads(flask_client):
    old_max_nr = os.getenv("SMT-MAX-NR-SIM-UPLOADS")
    os.environ["SMT-MAX-NR-SIM-UPLOADS"] = "2"
    with pytest.raises(UploadLimitsExceededError):
        flask_client.post(
            "/digitize/results",
            data=dict(
                file=[
                    (BytesIO(b"File1"), "file1.png"),
                    (BytesIO(b"File2"), "file2.png"),
                    (BytesIO(b"File3"), "file3.png"),
                ],
            ),
            follow_redirects=True,
        )
    if old_max_nr is None:
        os.unsetenv("SMT-MAX-NR-SIM-UPLOADS")
    else:
        os.environ["SMT-MAX-NR-SIM-UPLOADS"] = old_max_nr
