import os
from io import BytesIO


def save_test_pdf(request, option_name: str, filename: str, content: BytesIO) -> None:
    if request.config.getoption(option_name):
        dirname = "debug-output"
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(
            "{}/{}".format(dirname, filename),
            "wb",
        ) as fw:
            fw.write(content.read())
