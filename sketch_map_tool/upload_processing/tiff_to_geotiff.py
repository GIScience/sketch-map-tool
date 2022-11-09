"""
Functions to create a georeferenced GeoTIFF based on the map cut-out from a sketch map
"""

from io import BytesIO

import cv2
import np
import PIL
from numpy.typing import NDArray
from osgeo import gdal, osr


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


def convert(image: NDArray, bbox: Bbox) -> BytesIO:
    """
    Convert a given TIFF image to a GeoTIFF file with a given bbox

    :param image: Image to be converted to a GeoTIFF
    :param bbox: Bounding box in list form for the georeferencing
    :return: GeoTIFF
    """
    gdal.FileFromMemBuffer("/vsimem/input.tiff", image)
    src_ds = gdal.Open("/vsimem/input.tiff")
    file_format = "GTiff"
    driver = gdal.GetDriverByName(file_format)
    dst_ds = driver.CreateCopy("/vsimem/output.tiff", src_ds, 0)
    image_object = PIL.Image.fromarray(image)
    width, height = image_object.size
    rel_width = abs(float(bbox.lon2) - float(bbox.lon1)) / width
    rel_height = abs(float(bbox.lat2) - float(bbox.lat1)) / height
    transformation = [float(bbox.lon1), rel_width, 0, float(bbox.lat2), 0, -rel_height]
    dst_ds.SetGeoTransform(transformation)
    ref = osr.SpatialReference()
    ref.ImportFromEPSG(4326)
    dest_wkt = ref.ExportToWkt()
    dst_ds.SetProjection(dest_wkt)
    dst_ds = None
    src_ds = None
    result = gdal.GetMemFileBuffer("/vsimem/output.tiff")
    gdal.Unlink("/vsimem/input.tiff")
    gdal.Unlink("/vsimem/output.tiff")
    return result
