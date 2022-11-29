def test_gdal_array():
    try:
        from osgeo import gdal_array  # noqa
    except ImportError:
        assert False


def test_qgis():
    try:
        import qgis.analysis  # noqa
        import qgis.core  # noqa
    except ImportError:
        assert False
