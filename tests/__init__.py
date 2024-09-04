import logging
from pathlib import Path

import vcr

logging.getLogger("vcr").setLevel(logging.WARNING)

FIXTURE_DIR = Path(__file__).parent.resolve() / "fixtures"
CASSETT_DIR = FIXTURE_DIR / "cassette"

# dummy_png created with PIL and this command:
# >>> output = io.BytesIO()
# >>> Image.new("RGB", (1, 1)).save(output, format="PNG")
# >>> output.getvalue()
DUMMY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\02\x00"
    b"\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def replace_body(content_types, replacement):
    def before_record_response(response):
        headers = response["headers"]
        if "Content-Type" in headers.keys():
            content_type = "Content-Type"
        elif "Content-type" in headers.keys():
            content_type = "Content-type"
        else:
            return response

        if any(ct in content_types for ct in response["headers"][content_type]):
            response["body"]["string"] = replacement
        return response

    return before_record_response


vcr_app = vcr.VCR(
    cassette_library_dir=str(CASSETT_DIR),
    # before_record_response=replace_body(["image/png"], DUMMY_PNG),
    ignore_localhost=True,
    ignore_hosts=["neptune.ai", "basemaps-api.arcgis.com"],
)
