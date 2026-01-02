from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
import shapely.wkt
from geojson import FeatureCollection
from pytest_approval import verify

from sketch_map_tool import helpers
from tests import FIXTURE_DIR


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


@pytest.fixture(scope="module")
def geo_ip_database_path():
    return FIXTURE_DIR / "geoip" / "GeoIP2-City-Test.mmdb"


@pytest.mark.parametrize("ip, path", [("foo", None), (None, Path.cwd()), (None, None)])
def test_geo_ip_lookup_none(ip, path):
    assert helpers.geo_ip_lookup(ip, path) == (None, None, None, None)


def test_geo_ip_lookup_address_not_found(geo_ip_database_path, caplog):
    results = helpers.geo_ip_lookup("42.2.228.64", geo_ip_database_path)
    assert results == (None, None, None, None)
    assert verify(caplog.text.splitlines()[0])


def test_geo_ip_lookup_database_not_found(caplog):
    path = FIXTURE_DIR / "foo.mmdb"
    results = helpers.geo_ip_lookup("2a02:e440::", path)
    assert results == (None, None, None, None)
    assert "FileNotFoundError: [Errno 2] No such file or directory:" in caplog.text
    assert results == (None, None, None, None)


def test_geo_ip_lookup_city_not_found(geo_ip_database_path):
    assert verify(str(helpers.geo_ip_lookup("2a02:e440::", geo_ip_database_path)))


def test_geo_ip_lookup(geo_ip_database_path):
    assert verify(str(helpers.geo_ip_lookup("2.2.3.0", geo_ip_database_path)))


def test_geo_ip_lookup_wkt_validation(geo_ip_database_path):
    result = helpers.geo_ip_lookup("2.2.3.0", geo_ip_database_path)
    wkt = result[-1]
    assert wkt is not None
    assert shapely.wkt.loads(wkt).is_valid
