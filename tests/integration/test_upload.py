import os
from unittest import mock

import pytest

from sketch_map_tool.exceptions import UploadLimitsExceededError


@mock.patch.dict(os.environ, {"SMT_MAX_NR_SIM_UPLOADS": "2"})
def test_max_nr_sim_uploades(flask_client, sketch_map_buffer):
    with pytest.raises(UploadLimitsExceededError):
        flask_client.post(
            "/digitize/results",
            data=dict(
                file=[
                    (sketch_map_buffer, "file1.png"),
                    (sketch_map_buffer, "file2.png"),
                    (sketch_map_buffer, "file3.png"),
                ],
            ),
            follow_redirects=True,
        )
