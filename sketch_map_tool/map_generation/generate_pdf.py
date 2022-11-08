"""
Generate a sketch map PDF.
"""
import io
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import fitz
from haversine import Unit, haversine
from PIL import Image
from pyproj import Transformer
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib import utils
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from sketch_map_tool.map_generation.paper_format import paper_format
from sketch_map_tool.map_generation.qr_code import generate_qr_code

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None

RESOURCE_PATH = Path(__file__).parent.resolve() / "resources"


def generate_pdf(
    map_image: Image,
    uuid: str,
    bbox: str,
    format_: str,
    orientation: str,
    size: Dict[str, float],
) -> Tuple[BytesIO, BytesIO]:
    """
    Generate a sketch map pdf, i.e. a PDF containing the given map image as well as a code for
    georeferencing, a scale, copyright information, and objects to help the feature detection
    during the upload processing.

    :output_path: Path under which the output PDF should be stored.
    :param map_image: Image of the map to be used as sketch map.
    :param bbox: Bounding box, needed for naming, scale calculation and  the code for
                 georeferencing.
    :param paper_format: Paper format of the PDF document.
    :return: Path to the generated PDF file.
    """
    # TODO: Factor out code parts to separate functions
    format_ = paper_format(format_)

    map_width_px, map_height_px = map_image.size

    # TODO: Use orientation parameter to determine rotation
    # Adjust map orientation and scaling:
    rotate = map_width_px < map_height_px
    ratio = map_height_px / map_width_px

    if not rotate:
        adjusted_width = format_.width - format_.right_margin  # cm
        adjusted_height = (format_.width - format_.right_margin) * ratio  # cm

        if adjusted_height > format_.height:
            adjusted_height = format_.height
            adjusted_width = format_.height / ratio
    else:
        adjusted_height = format_.width - format_.right_margin  # cm
        adjusted_width = (format_.width - format_.right_margin) / ratio  # cm
        if adjusted_width > format_.height:
            adjusted_width = format_.height  # cm
            adjusted_height = format_.height * ratio  # cm

    map_image_raw = io.BytesIO()
    map_image.save(map_image_raw, format="png")
    map_image_reportlab = utils.ImageReader(map_image_raw)

    map_pdf = BytesIO()
    map_template = BytesIO()
    map_template_image = BytesIO()
    # Set-up everything for the reportlab pdf:
    canv_map = canvas.Canvas(map_pdf)
    canv_template = canvas.Canvas(map_template)
    canv_map.setPageSize(landscape((format_.height * cm, format_.width * cm)))
    canv_template.setPageSize(landscape((adjusted_height * cm, adjusted_width * cm)))

    # Add map to canvas:
    for canv in [canv_map, canv_template]:
        if rotate:
            canv.rotate(90)
            canv.drawImage(
                map_image_reportlab,
                0,
                (-adjusted_height) * cm,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )
            canv.rotate(-90)
        else:
            canv.drawImage(
                map_image_reportlab,
                0,
                0,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )

    if rotate:
        adjusted_width, adjusted_height = adjusted_height, adjusted_width

    qr_code = generate_qr_code(
        uuid,
        bbox,
        format_.title,
        orientation,
        size,
        format_.qr_scale,
    )
    compass = get_compass(format_.compass_scale)
    globe_1, globe_2, globe_3, globe_4 = get_globes(format_.globe_scale)
    globe_length = 150 * format_.globe_scale

    # Calculate scale:
    scale = adjusted_width / get_width(bbox)  # cm per meter
    # TODO: Use scale from OL component

    if scale * 10000 <= format_.right_margin - 1:
        scale_length = scale * 10000
        scale_text = ["5km", "10km"]
    elif scale * 5000 <= format_.right_margin - 1:
        scale_length = scale * 5000
        scale_text = ["2.5km", "5km"]
    elif scale * 2000 <= format_.right_margin - 1:
        scale_length = scale * 2000
        scale_text = ["1km", "2km"]
    elif scale * 1000 <= format_.right_margin - 1:
        scale_length = scale * 1000
        scale_text = ["500m", "1km"]
    elif scale * 500 <= format_.right_margin - 1:
        scale_length = scale * 500
        scale_text = ["250m", "500m"]
    elif scale * 200 <= format_.right_margin - 1:
        scale_length = scale * 200
        scale_text = ["100m", "200m"]
    elif scale * 100 <= format_.right_margin - 1:
        scale_length = scale * 100
        scale_text = ["50m", "100m"]
    elif scale * 50 <= format_.right_margin - 1:
        scale_length = scale * 50
        scale_text = ["25m", "50m"]
    else:
        scale_length = scale * 10
        scale_text = ["5m", "10m"]

    # Add a border around the map
    canv_map.rect(0, 0, adjusted_width * cm, adjusted_height * cm, fill=0)

    canv_map.setFontSize(format_.font_size)
    canv_map.setFillColorRGB(0, 0, 0)
    copyright_text_origin = 0.24 * format_.height * cm
    rotate_indent = (
        -(adjusted_width + format_.compass_scale * 3 + 3 * format_.indent) * cm
    )

    if rotate:
        canv_map.rotate(90)

        # Add copyright information:
        text = canv_map.beginText()
        text.setTextOrigin(copyright_text_origin, rotate_indent)
        text.textLines("Map: (C)OpenStreetMap Contributors")
        canv_map.drawText(text)

        # TODO
        # Add QR contents:
        # text = canv.beginText()
        # text.setTextOrigin(
        #     copyright_text_origin,
        #     rotate_indent - paper_format.qr_contents_distance_rotated * cm,
        # )
        # text.textLines(f"Code contents: '{qr_text}'")
        # canv.drawText(text)

        # Add QR-Code:
        renderPDF.draw(
            qr_code, canv_map, format_.qr_y * cm, -(format_.width - 0.1) * cm
        )

        # Add scale:
        x_scale_cm = 0.24 * format_.height + format_.font_size / 1.5
        canv_map.rect(
            x_scale_cm * cm,
            rotate_indent,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=1,
        )
        canv_map.rect(
            (x_scale_cm + scale_length / 2) * cm,
            rotate_indent,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=0,
        )
        canv_map.drawString(
            (x_scale_cm + scale_length / 2 - format_.font_size / 25) * cm,
            rotate_indent - format_.height * 0.012 * cm,
            scale_text[0],
        )
        canv_map.drawString(
            (x_scale_cm + scale_length - format_.font_size / 25) * cm,
            rotate_indent - format_.height * 0.012 * cm,
            scale_text[1],
        )

        # Add compass:
        renderPDF.draw(
            compass,
            canv_map,
            (
                0.24 * format_.height
                + format_.font_size / 1.5
                + scale_length
                + format_.font_size / 4
            )
            * cm,
            rotate_indent - 2 * format_.compass_scale * cm,
        )
        canv_map.rotate(-90)
    else:
        # Add copyright information:
        text = canv_map.beginText()
        text.setTextOrigin(
            (adjusted_width + format_.indent) * cm, copyright_text_origin
        )
        if format_.title in ("a0", "a1", "a2"):
            text.textLines("Map:\n\n(C)OpenStreetMap Contributors")
        else:
            text.textLines("Map:\n(C)OpenStreetMap Contributors")
        canv_map.drawText(text)

        # TODO
        # Add QR contents:
        # canv.rotate(90)
        # text = canv.beginText()
        # text.setTextOrigin(
        #     copyright_text_origin
        #     + paper_format.qr_contents_distances_not_rotated[0] * cm,
        #     rotate_indent - paper_format.qr_contents_distances_not_rotated[1] * cm,
        # )
        # text.textLines(f"Code contents: '{qr_text}'")
        # canv.drawText(text)
        # canv.rotate(-90)

        # Add QR-Code:
        renderPDF.draw(
            qr_code,
            canv_map,
            (adjusted_width + format_.indent) * cm,
            format_.qr_y * cm,
        )

        # Add scale:
        canv_map.rect(
            (adjusted_width + format_.indent) * cm,
            0.297 * format_.height * cm,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=1,
        )
        canv_map.rect(
            (adjusted_width + format_.indent + scale_length / 2) * cm,
            0.297 * format_.height * cm,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=0,
        )
        canv_map.drawString(
            (
                adjusted_width
                + format_.indent
                + scale_length / 2
                - format_.font_size / 25
            )
            * cm,
            0.285 * format_.height * cm,
            scale_text[0],
        )
        canv_map.drawString(
            (adjusted_width + format_.indent + scale_length - format_.font_size / 25)
            * cm,
            0.285 * format_.height * cm,
            scale_text[1],
        )

        # Add compass:
        renderPDF.draw(
            compass,
            canv_map,
            (adjusted_width + format_.indent) * cm,
            0.333 * format_.height * cm,
        )

    for canv in [canv_map, canv_template]:
        # Add globes to improve feature detection during upload processing
        renderPDF.draw(globe_1, canv, 0, 0)
        renderPDF.draw(globe_3, canv, 0, adjusted_height * cm - globe_length)
        renderPDF.draw(
            globe_4,
            canv,
            adjusted_width * cm - globe_length,
            adjusted_height * cm - globe_length,
        )
        renderPDF.draw(globe_2, canv, adjusted_width * cm - globe_length, 0)
        renderPDF.draw(globe_2, canv, 0, adjusted_height / 2 * cm - 0.5 * globe_length)
        renderPDF.draw(
            globe_1,
            canv,
            adjusted_width / 2 * cm - 0.5 * globe_length,
            adjusted_height * cm - globe_length,
        )
        renderPDF.draw(
            globe_3,
            canv,
            adjusted_width * cm - globe_length,
            adjusted_height / 2 * cm - globe_length / 2,
        )
        renderPDF.draw(globe_4, canv, adjusted_width / 2 * cm - globe_length / 2, 0)

        # Generate PDFs:
        canv.save()

    map_pdf.seek(0)
    map_template.seek(0)

    # Store template image for later upload processing:
    # template_pdf = fitz.open(map_template)
    # page = template_pdf[0]
    # if rotate:
    #     page.set_rotation(90)
    # page.get_pixmap().save(map_template_image)
    # template_pdf.close()
    map_template_image.seek(0)
    return (map_pdf, map_template_image)


def get_globes(scale_factor) -> Tuple[Drawing, ...]:
    """Read globe as SVG from disk, convert to RLG and scale it."""
    globes = []
    for i in range(1, 5):
        globe = svg2rlg(RESOURCE_PATH / "globe_{0}.svg".format(i))
        globe.scale(scale_factor, scale_factor)
        globes.append(globe)
    return tuple(globes)


def get_compass(scale_factor: float) -> Drawing:
    "ssert compass is not None" "Read compass as SVG from disk, convert to RLG and scale it." ""
    compass = svg2rlg(RESOURCE_PATH / "north.svg")
    compass.scale(scale_factor, scale_factor)
    return compass


def get_width(bbox: list) -> float:
    """Get width of bounding box in meter."""
    transformer = Transformer.from_crs(3857, 4326)  # Pseudo-Mercator to lat/lon
    return haversine(
        transformer.transform(bbox[0], bbox[1]),
        transformer.transform(bbox[2], bbox[3]),
        unit=Unit.METERS,
    )
