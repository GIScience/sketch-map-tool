def test_gdal_array():
    try:
        from osgeo import gdal_array  # noqa
    except ImportError:
        assert False
