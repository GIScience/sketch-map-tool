from io import BytesIO
from tempfile import NamedTemporaryFile

from osgeo import gdal, osr

from sketch_map_tool.upload_processing.converter import img_to_geotiff


def test_img_to_geotiff_map_frame(map_frame, bbox):
    buffer = img_to_geotiff(map_frame, bbox)
    assert isinstance(buffer, BytesIO)

    with NamedTemporaryFile() as file:
        file.write(buffer.read())
        src_ds = gdal.Open(file.name)
        assert src_ds.RasterCount == 3
        assert src_ds.RasterXSize == map_frame.shape[1]
        assert src_ds.RasterYSize == map_frame.shape[0]
        proj = osr.SpatialReference(wkt=src_ds.GetProjection())
        assert "3857" == proj.GetAttrValue("AUTHORITY", 1)

    # Too manually check the image uncomment following code.
    # import cv2
    # import numpy as np

    # buffer.seek(0)
    # img = cv2.imdecode(
    #     np.fromstring(buffer.read(), dtype="uint8"), cv2.IMREAD_UNCHANGED
    # )
    # cv2.imshow("image", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def test_img_to_geotiff_markings_detected(map_frame_markings_detected, bbox):
    buffer = img_to_geotiff(map_frame_markings_detected, bbox)
    assert isinstance(buffer, BytesIO)

    with NamedTemporaryFile() as file:
        file.write(buffer.read())
        src_ds = gdal.Open(file.name)
        assert src_ds.RasterCount == 3
        assert src_ds.RasterXSize == map_frame_markings_detected.shape[1]
        assert src_ds.RasterYSize == map_frame_markings_detected.shape[0]
        proj = osr.SpatialReference(wkt=src_ds.GetProjection())
        assert "3857" == proj.GetAttrValue("AUTHORITY", 1)

    # import cv2
    # import numpy as np

    # buffer.seek(0)
    # img = cv2.imdecode(
    #     np.fromstring(buffer.read(), dtype="uint8"), cv2.IMREAD_UNCHANGED
    # )
    # cv2.imshow("image", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
