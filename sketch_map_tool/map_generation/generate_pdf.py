""" Generate a sketch map PDF. """
import io
from io import BytesIO
from pathlib import Path
from typing import Tuple

import fitz
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib import utils
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from sketch_map_tool.models import PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None

RESOURCE_PATH = Path(__file__).parent.resolve() / "resources"


def generate_pdf(  # noqa: C901
    map_image: Image,
    qr_code: Drawing,
    format_: PaperFormat,
    scale: float,
) -> Tuple[BytesIO, BytesIO]:
    """
    Generate a sketch map pdf, i.e. a PDF containing the given map image as well as a code for
    georeferencing, a scale, copyright information, and objects to help the feature detection
    during the upload processing.

    # Generate emplate image (PNG) as Pillow object for later upload processing

    :output_path: Path under which the output PDF should be stored.
    :param map_image: Image of the map to be used as sketch map.
    :param bbox: Bounding box, needed for naming, scale calculation and  the code for
                 georeferencing.
    :param paper_format: Paper format of the PDF document.
    :return: Path to the generated PDF file.
    """
    map_width_px, map_height_px = map_image.size
    map_margin = format_.map_margin

    # TODO: Use orientation parameter to determine rotation
    rotate = map_width_px < map_height_px
    ratio = map_height_px / map_width_px

    if not rotate:  # landscape
        adjusted_width = format_.width - format_.right_margin - 2 * map_margin  # cm
        adjusted_height = adjusted_width * ratio  # cm

        if adjusted_height > format_.height:
            adjusted_height = format_.height - 2 * map_margin  # cm
            adjusted_width = adjusted_height / ratio  # cm

    else:  # portrait
        adjusted_height = format_.width - format_.right_margin - 2 * map_margin  # cm
        adjusted_width = adjusted_height / ratio  # cm
        if adjusted_width > format_.height:
            adjusted_width = format_.height - 2 * map_margin  # cm
            adjusted_height = adjusted_width * ratio  # cm

    map_image_raw = io.BytesIO()
    map_image.save(map_image_raw, format="png")
    map_image_reportlab = utils.ImageReader(map_image_raw)

    map_pdf = BytesIO()
    map_template = BytesIO()
    # Set-up everything for the reportlab pdf:
    canv_map = canvas.Canvas(map_pdf)
    canv_template = canvas.Canvas(map_template)
    canv_map.setPageSize(landscape((format_.height * cm, format_.width * cm)))
    canv_template.setPageSize(landscape((adjusted_height * cm, adjusted_width * cm)))

    # Add map to canvas:
    for canv, canv_map_margin in zip([canv_map, canv_template], [map_margin, 0]):
        if rotate:  # portrait
            canv.rotate(90)
            canv.drawImage(
                map_image_reportlab,
                canv_map_margin * cm,
                (-adjusted_height - canv_map_margin) * cm,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )
            canv.rotate(-90)
        else:  # landscape
            canv.drawImage(
                map_image_reportlab,
                canv_map_margin * cm,
                canv_map_margin * cm,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )

    if rotate:
        adjusted_width, adjusted_height = adjusted_height, adjusted_width

    compass = get_compass(format_.compass_scale)
    globe_1, globe_2, globe_3, globe_4 = get_globes(format_.globe_scale)
    globe_length = 150 * format_.globe_scale
    scale_length, scale_text = get_scale(scale, width_max=(format_.right_margin - 1))

    # Add a border around the map
    canv_map.rect(
        map_margin * cm,
        map_margin * cm,
        adjusted_width * cm,
        adjusted_height * cm,
        fill=0,
    )

    canv_map.setFontSize(format_.font_size)
    canv_map.setFillColorRGB(0, 0, 0)
    copyright_text_origin = 0.24 * format_.height * cm
    rotate_indent = (
        -(
            map_margin * 2
            + adjusted_width
            + format_.compass_scale * 2
            + 3 * format_.indent
        )
        * cm
    )

    if rotate:  # portrait
        canv_map.rotate(90)

        # Add copyright information:
        text = canv_map.beginText()
        text.setTextOrigin(copyright_text_origin + 1.0 * cm, rotate_indent)
        text.textLines("Map: © OpenStreetMap Contributors")
        canv_map.drawText(text)

        # Add QR-Code:
        renderPDF.draw(
            qr_code, canv_map, format_.qr_y * cm, -(format_.width - 1.1) * cm
        )

        # Add scale:
        x_scale_cm = 0.24 * format_.height + format_.font_size / 1.5 + map_margin
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
            rotate_indent - 2 * format_.compass_scale * cm + format_.qr_y * cm,
        )
        canv_map.rotate(-90)
    else:  # landscape
        x_right_margin = map_margin * 2 + adjusted_width + format_.indent
        # Add copyright information:
        text = canv_map.beginText()
        text.setTextOrigin(
            x_right_margin * cm, copyright_text_origin + format_.qr_y * cm
        )
        if format_.title in ("a0", "a1", "a2"):
            text.textLines("Map:\n\n© OpenStreetMap Contributors")
        else:
            text.textLines("Map:\n© OpenStreetMap Contributors")
        canv_map.drawText(text)

        # Add QR-Code:
        renderPDF.draw(
            qr_code,
            canv_map,
            x_right_margin * cm,
            format_.qr_y * cm,
        )

        # Add scale:
        canv_map.rect(
            x_right_margin * cm,
            0.297 * format_.height * cm + format_.qr_y * cm,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=1,
        )
        canv_map.rect(
            (x_right_margin + scale_length / 2) * cm,
            0.297 * format_.height * cm + format_.qr_y * cm,
            scale_length / 2 * cm,
            format_.scale_height * cm,
            fill=0,
        )
        canv_map.drawString(
            (x_right_margin + scale_length / 2 - format_.font_size / 25) * cm,
            0.285 * format_.height * cm + format_.qr_y * cm,
            scale_text[0],
        )
        canv_map.drawString(
            (x_right_margin + scale_length - format_.font_size / 25) * cm,
            0.285 * format_.height * cm + format_.qr_y * cm,
            scale_text[1],
        )

        # Add compass:
        renderPDF.draw(
            compass,
            canv_map,
            x_right_margin * cm,
            0.333 * format_.height * cm + format_.qr_y * cm,
        )

    for canv, canv_map_margin in zip([canv_map, canv_template], [map_margin, 0]):
        # Add globes to improve feature detection during upload processing

        # corner globes
        # bottom left
        renderPDF.draw(globe_1, canv, canv_map_margin * cm, canv_map_margin * cm)
        # top left
        renderPDF.draw(
            globe_3,
            canv,
            canv_map_margin * cm,
            (canv_map_margin + adjusted_height) * cm - globe_length,
        )
        # top right
        renderPDF.draw(
            globe_4,
            canv,
            (canv_map_margin + adjusted_width) * cm - globe_length,
            (canv_map_margin + adjusted_height) * cm - globe_length,
        )
        # bottom right
        renderPDF.draw(
            globe_2,
            canv,
            (canv_map_margin + adjusted_width) * cm - globe_length,
            canv_map_margin * cm,
        )

        # middle globes
        renderPDF.draw(
            globe_2,
            canv,
            canv_map_margin * cm,
            (canv_map_margin + adjusted_height / 2) * cm - 0.5 * globe_length,
        )
        renderPDF.draw(
            globe_1,
            canv,
            (canv_map_margin + adjusted_width / 2) * cm - 0.5 * globe_length,
            (canv_map_margin + adjusted_height) * cm - globe_length,
        )
        renderPDF.draw(
            globe_3,
            canv,
            (canv_map_margin + adjusted_width) * cm - globe_length,
            (canv_map_margin + adjusted_height) / 2 * cm - globe_length / 2,
        )
        renderPDF.draw(
            globe_4,
            canv,
            (canv_map_margin + adjusted_width / 2) * cm - globe_length / 2,
            canv_map_margin * cm,
        )

        # Generate PDFs:
        canv.save()

    map_pdf.seek(0)
    map_template.seek(0)

    map_img = pdf_page_to_img(map_template)

    return (map_pdf, map_img)


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


def get_scale(scale: float, width_max: float) -> tuple[float, tuple[str, str]]:
    """Get scale length [cm] and scale text.

    :scale: Scale denominator
    :width_max: Maximal width of the scale bar [cm]

    E.g.
    (scale bar) 1 cm = 11545.36 cm (scale denominator)
    (scale bar) ? cm = 50000 cm    (factor)
    """
    for factor in (
        1000000,  # 10 km
        500000,
        200000,
        100000,  # 1 km
        50000,
        20000,
        10000,  # 100 m
        5000,
        1000,  # 10 m
    ):
        scale_length = factor / scale
        if scale_length <= width_max:
            # Two parts of the black and white scale bar
            if factor >= 100000:
                # In kilometer
                scale_text = (
                    str(int((factor / 100000) / 2)) + "km",
                    str(int(factor / 100000)) + "km",
                )
            else:
                # In meter
                scale_text = (
                    str(int((factor / 100) / 2)) + "m",
                    str(int(factor / 100)) + "m",
                )
            break
    return (scale_length, scale_text)


def pdf_page_to_img(pdf: BytesIO, page_id=0) -> BytesIO:
    """Extract page from PDF, convert it to PNG and write it as Pillow Image."""
    img = BytesIO()
    with fitz.Document(stream=pdf, filetype="pdf") as doc:
        page = doc.load_page(page_id)
        # TODO: Is this necessary?
        # if rotate:
        #     page.set_rotation(90)
        page.get_pixmap().pil_save(img, format="png")
    img.seek(0)
    return img
