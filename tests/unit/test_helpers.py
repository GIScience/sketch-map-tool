from pathlib import Path

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
