from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
from numpy.typing import NDArray
from osgeo import gdal, osr

from sketch_map_tool.models import Bbox


def georeference(img: NDArray, bbox: Bbox, bgr: bool = True) -> BytesIO:
    """Create a GeoTIFF from an image (map frame) and bounding box coordinates.

    The image (numpy array) should be in BGR (3 channels).
    If it is not in BGR the image is expected to contain detected markings and the
    result is expected to be vectorized.

    The Bounding Box is in WGS 84 / Pseudo-Mercator.
    """
    gdal.UseExceptions()

    width = img.shape[1]
    height = img.shape[0]
    pixel_width = abs(bbox.lon_max - bbox.lon_min) / width
    pixel_height = abs(bbox.lat_max - bbox.lat_min) / height

    with TemporaryDirectory() as tmpdirname:
        outfile_name = Path(tmpdirname) / "out.geotiff"
        # create dataset (destination raster)
        dataset = gdal.GetDriverByName("GTiff").Create(
            str(outfile_name),
            width,
            height,
            3 if bgr else 1,
            gdal.GDT_Byte,
        )

        if bgr:
            # write numpy array to destination raster in RGB (Reverse GBR image)
            dataset.GetRasterBand(1).WriteArray(img[:, :, 2])  # Red
            dataset.GetRasterBand(2).WriteArray(img[:, :, 1])  # Green
            dataset.GetRasterBand(3).WriteArray(img[:, :, 0])  # Blue
        else:
            dataset.GetRasterBand(1).WriteArray(img)  # color value

        # set geo transform
        # fmt: off
        transform = [
            bbox.lon_min,   # x-coordinate of upper-left corner of upper-left pixel
            pixel_width,
            0,              # row rotation (typically zero)
            bbox.lat_max,   # y-coordinate of upper-left corner of upper-left pixel
            0,              # column rotation (typically zero)
            -pixel_height,  # negative value for a north-up image
        ]
        # fmt: on
        dataset.SetGeoTransform(transform)

        # set spatial reference system
        spatial_reference_system = osr.SpatialReference()
        spatial_reference_system.ImportFromEPSG(3857)  # WGS 84 / Pseudo-Mercator
        dataset.SetProjection(spatial_reference_system.ExportToWkt())

        dataset = None  # close dataset
        with open(outfile_name, "rb") as f:
            return BytesIO(f.read())


def print_copyright_note(img: NDArray) -> NDArray:
    """
    Print an OSM copyright note on a given image

    :param img: Image on which the OSM copyright note should be printed
    :return: Imgage with the copyright note on it
    """
    font = cv2.FONT_HERSHEY_TRIPLEX
    colour = (0, 0, 0)
    scale = 1
    line_thickness = 2
    height, width, _ = img.shape
    img = cv2.putText(
        img,
        "(C) OpenStreetMap contributors, see OSM.org",
        (round(width * 0.53), height - 50),
        font,
        scale,
        colour,
        line_thickness,
    )
    return img
