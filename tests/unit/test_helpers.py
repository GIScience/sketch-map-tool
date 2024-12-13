from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from geojson import FeatureCollection

from sketch_map_tool import helpers


def test_get_project_root():
    expected = Path(__file__).resolve().parent.parent.parent.resolve()
    result = helpers.get_project_root()
    assert expected == result


def test_merge(detected_markings_cleaned):
    fc = helpers.merge([detected_markings_cleaned, detected_markings_cleaned])
    assert isinstance(fc, FeatureCollection)
    assert len(fc.features) == len(detected_markings_cleaned.features) * 2


def test_merge_empyt_fc():
    fc = helpers.merge([FeatureCollection(features=[])])
    assert isinstance(fc, FeatureCollection)
    assert len(fc.features) == 0


def test_zip_(sketch_map_frame_markings_detected):
    buffer = helpers.zip_(
        [
            (
                "file_name.png",
                "attribution",
                BytesIO(sketch_map_frame_markings_detected),
            ),
            (
                "file_name_2.png",
                "attribution",
                BytesIO(sketch_map_frame_markings_detected),
            ),
        ]
    )
    with ZipFile(buffer) as zip_file:
        zip_info = zip_file.infolist()
    assert len(zip_info) == 3
    assert zip_info[0].filename == "file_name.geotiff"
    assert zip_info[0].file_size == 5407584
    assert zip_info[1].filename == "file_name_2.geotiff"
    assert zip_info[1].file_size == 5407584
    assert zip_info[2].filename == "attributions.txt"
    assert zip_info[2].file_size == 11
