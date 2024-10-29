import os
from io import BytesIO

import numpy as np
from numpy.typing import NDArray


def save_test_file(request, option_name: str, filename: str, content: BytesIO) -> None:
    if request.config.getoption(option_name):
        dirname = "debug-output"
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(
            "{}/{}".format(dirname, filename),
            "wb",
        ) as fw:
            fw.write(content.read())


def serialize_ndarray(array: NDArray) -> bytes:
    buffer = BytesIO()
    np.save(buffer, array)
    buffer.seek(0)
    return buffer.read()
