"""
Generate a sketch map PDF.
"""
import io
import os

import fitz
import qrcode
import qrcode.image.svg
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.lib import utils
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from sketch_map_tool.helper_modules.bbox_utils import Bbox

from .paper_formats.paper_formats import A0, A1, A2, A4, PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None

RESOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def generate_pdf(
    output_path: str,  # pylint: disable=R0914  # noqa: C901
    map_image: Image,
    bbox: Bbox,
    current_date: str,
    paper_format: PaperFormat = A4,
) -> str:
    """
    Generate a sketch map pdf, i.e. a PDF containing the given map image as well as a code for
    georeferencing, a scale, copyright information, and objects to help the feature detection
    during the upload processing.

    :output_path: Path under which the output PDF should be stored.
    :param map_image: Image of the map to be used as sketch map.
    :param bbox: Bounding box, needed for naming, scale calculation and  the code for
                 georeferencing.
    :param current_date: Current date, needed for naming and the QR code.
    :param paper_format: Paper format of the PDF document.
    :return: Path to the generated PDF file.
    """
    map_width_px, map_height_px = map_image.size

    # Adjust map orientation and scaling:
    rotate = map_width_px < map_height_px
    ratio = map_height_px / map_width_px

    if not rotate:
        adjusted_width = paper_format.width - paper_format.right_margin  # cm
        adjusted_height = (paper_format.width - paper_format.right_margin) * ratio  # cm

        if adjusted_height > paper_format.height:
            adjusted_height = paper_format.height
            adjusted_width = paper_format.height / ratio
    else:
        adjusted_height = paper_format.width - paper_format.right_margin  # cm
        adjusted_width = (paper_format.width - paper_format.right_margin) / ratio  # cm
        if adjusted_width > paper_format.height:
            adjusted_width = paper_format.height  # cm
            adjusted_height = paper_format.height * ratio  # cm

    map_image_raw = io.BytesIO()
    map_image.save(map_image_raw, format="png")
    map_image_reportlab = utils.ImageReader(map_image_raw)

    # Set-up everything for the reportlab pdf:
    canv = canvas.Canvas(output_path)
    template_pdf_path = output_path.replace(".pdf", "_template.pdf")
    template = canvas.Canvas(template_pdf_path)
    canv.setPageSize(landscape((paper_format.height * cm, paper_format.width * cm)))
    template.setPageSize(landscape((adjusted_height * cm, adjusted_width * cm)))

    # Add map to canvas:
    for canvas_object in [canv, template]:
        if rotate:
            canvas_object.rotate(90)
            canvas_object.drawImage(
                map_image_reportlab,
                0,
                (-adjusted_height) * cm,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )
            canvas_object.rotate(-90)
        else:
            canvas_object.drawImage(
                map_image_reportlab,
                0,
                0,
                mask="auto",
                width=adjusted_width * cm,
                height=adjusted_height * cm,
            )

    if rotate:
        adjusted_width, adjusted_height = adjusted_height, adjusted_width

    # Generate QR-Code:
    qr_factory = qrcode.image.svg.SvgPathImage
    qr_text = f"{bbox.get_str(mode='comma')};{current_date};{paper_format}"

    qr = qrcode.make(qr_text, image_factory=qr_factory)  # pylint: disable=C0103
    qr_path = output_path.replace(".pdf", "_qr.svg")
    qr.save(qr_path)
    svg_qr = svg2rlg(qr_path)
    svg_qr.scale(paper_format.qr_scale, paper_format.qr_scale)

    # Import compass and globes:
    compass = svg2rlg(os.path.join(RESOURCE_PATH, "north.svg"))
    compass.scale(paper_format.compass_scale, paper_format.compass_scale)
    svg_globe_1 = svg2rlg(os.path.join(RESOURCE_PATH, "globe_1.svg"))
    svg_globe_2 = svg2rlg(os.path.join(RESOURCE_PATH, "globe_2.svg"))
    svg_globe_3 = svg2rlg(os.path.join(RESOURCE_PATH, "globe_3.svg"))
    svg_globe_4 = svg2rlg(os.path.join(RESOURCE_PATH, "globe_4.svg"))
    svg_globe_1.scale(paper_format.globe_scale, paper_format.globe_scale)
    svg_globe_2.scale(paper_format.globe_scale, paper_format.globe_scale)
    svg_globe_3.scale(paper_format.globe_scale, paper_format.globe_scale)
    svg_globe_4.scale(paper_format.globe_scale, paper_format.globe_scale)
    globe_length = 150 * paper_format.globe_scale

    # Calculate scale:
    scale = adjusted_width / bbox.get_width()  # cm per meter

    if scale * 10000 <= paper_format.right_margin - 1:
        scale_length = scale * 10000
        scale_text = ["5km", "10km"]
    elif scale * 5000 <= paper_format.right_margin - 1:
        scale_length = scale * 5000
        scale_text = ["2.5km", "5km"]
    elif scale * 2000 <= paper_format.right_margin - 1:
        scale_length = scale * 2000
        scale_text = ["1km", "2km"]
    elif scale * 1000 <= paper_format.right_margin - 1:
        scale_length = scale * 1000
        scale_text = ["500m", "1km"]
    elif scale * 500 <= paper_format.right_margin - 1:
        scale_length = scale * 500
        scale_text = ["250m", "500m"]
    elif scale * 200 <= paper_format.right_margin - 1:
        scale_length = scale * 200
        scale_text = ["100m", "200m"]
    elif scale * 100 <= paper_format.right_margin - 1:
        scale_length = scale * 100
        scale_text = ["50m", "100m"]
    elif scale * 50 <= paper_format.right_margin - 1:
        scale_length = scale * 50
        scale_text = ["25m", "50m"]
    else:
        scale_length = scale * 10
        scale_text = ["5m", "10m"]

    # Add a border around the map
    canv.rect(0, 0, adjusted_width * cm, adjusted_height * cm, fill=0)

    canv.setFontSize(paper_format.font_size)
    canv.setFillColorRGB(0, 0, 0)
    copyright_text_origin = 0.24 * paper_format.height * cm
    rotate_indent = (
        -(adjusted_width + paper_format.compass_scale * 3 + 3 * paper_format.indent)
        * cm
    )

    if rotate:
        canv.rotate(90)

        # Add copyright information:
        text = canv.beginText()
        text.setTextOrigin(copyright_text_origin, rotate_indent)
        text.textLines("Map: (C)OpenStreetMap Contributors")
        canv.drawText(text)

        # Add QR contents:
        text = canv.beginText()
        text.setTextOrigin(
            copyright_text_origin,
            rotate_indent - paper_format.qr_contents_distance_rotated * cm,
        )
        text.textLines(f"Code contents: '{qr_text}'")
        canv.drawText(text)

        # Add QR-Code:
        renderPDF.draw(
            svg_qr, canv, paper_format.qr_y * cm, -(paper_format.width - 0.1) * cm
        )

        # Add scale:
        x_scale_cm = 0.24 * paper_format.height + paper_format.font_size / 1.5
        canv.rect(
            x_scale_cm * cm,
            rotate_indent,
            scale_length / 2 * cm,
            paper_format.scale_height * cm,
            fill=1,
        )
        canv.rect(
            (x_scale_cm + scale_length / 2) * cm,
            rotate_indent,
            scale_length / 2 * cm,
            paper_format.scale_height * cm,
            fill=0,
        )
        canv.drawString(
            (x_scale_cm + scale_length / 2 - paper_format.font_size / 25) * cm,
            rotate_indent - paper_format.height * 0.012 * cm,
            scale_text[0],
        )
        canv.drawString(
            (x_scale_cm + scale_length - paper_format.font_size / 25) * cm,
            rotate_indent - paper_format.height * 0.012 * cm,
            scale_text[1],
        )

        # Add compass:
        renderPDF.draw(
            compass,
            canv,
            (
                0.24 * paper_format.height
                + paper_format.font_size / 1.5
                + scale_length
                + paper_format.font_size / 4
            )
            * cm,
            rotate_indent - 2 * paper_format.compass_scale * cm,
        )
        canv.rotate(-90)
    else:
        # Add copyright information:
        text = canv.beginText()
        text.setTextOrigin(
            (adjusted_width + paper_format.indent) * cm, copyright_text_origin
        )
        if paper_format in [A0, A1, A2]:
            text.textLines("Map:\n\n(C)OpenStreetMap Contributors")
        else:
            text.textLines("Map:\n(C)OpenStreetMap Contributors")
        canv.drawText(text)

        # Add QR contents:
        canv.rotate(90)
        text = canv.beginText()
        text.setTextOrigin(
            copyright_text_origin
            + paper_format.qr_contents_distances_not_rotated[0] * cm,
            rotate_indent - paper_format.qr_contents_distances_not_rotated[1] * cm,
        )
        text.textLines(f"Code contents: '{qr_text}'")
        canv.drawText(text)
        canv.rotate(-90)

        # Add QR-Code:
        renderPDF.draw(
            svg_qr,
            canv,
            (adjusted_width + paper_format.indent) * cm,
            paper_format.qr_y * cm,
        )

        # Add scale:
        canv.rect(
            (adjusted_width + paper_format.indent) * cm,
            0.297 * paper_format.height * cm,
            scale_length / 2 * cm,
            paper_format.scale_height * cm,
            fill=1,
        )
        canv.rect(
            (adjusted_width + paper_format.indent + scale_length / 2) * cm,
            0.297 * paper_format.height * cm,
            scale_length / 2 * cm,
            paper_format.scale_height * cm,
            fill=0,
        )
        canv.drawString(
            (
                adjusted_width
                + paper_format.indent
                + scale_length / 2
                - paper_format.font_size / 25
            )
            * cm,
            0.285 * paper_format.height * cm,
            scale_text[0],
        )
        canv.drawString(
            (
                adjusted_width
                + paper_format.indent
                + scale_length
                - paper_format.font_size / 25
            )
            * cm,
            0.285 * paper_format.height * cm,
            scale_text[1],
        )

        # Add compass:
        renderPDF.draw(
            compass,
            canv,
            (adjusted_width + paper_format.indent) * cm,
            0.333 * paper_format.height * cm,
        )

    for canvas_object in [canv, template]:
        # Add globes to improve feature detection during upload processing
        renderPDF.draw(svg_globe_1, canvas_object, 0, 0)
        renderPDF.draw(
            svg_globe_3, canvas_object, 0, adjusted_height * cm - globe_length
        )
        renderPDF.draw(
            svg_globe_4,
            canvas_object,
            adjusted_width * cm - globe_length,
            adjusted_height * cm - globe_length,
        )
        renderPDF.draw(
            svg_globe_2, canvas_object, adjusted_width * cm - globe_length, 0
        )
        renderPDF.draw(
            svg_globe_2, canvas_object, 0, adjusted_height / 2 * cm - 0.5 * globe_length
        )
        renderPDF.draw(
            svg_globe_1,
            canvas_object,
            adjusted_width / 2 * cm - 0.5 * globe_length,
            adjusted_height * cm - globe_length,
        )
        renderPDF.draw(
            svg_globe_3,
            canvas_object,
            adjusted_width * cm - globe_length,
            adjusted_height / 2 * cm - globe_length / 2,
        )
        renderPDF.draw(
            svg_globe_4, canvas_object, adjusted_width / 2 * cm - globe_length / 2, 0
        )

        # Generate PDFs:
        canvas_object.save()

    # Store template image for later upload processing:
    template_img_path = output_path.replace(".pdf", "_template.jpg")
    template_pdf = fitz.open(template_pdf_path)
    page = template_pdf[0]
    if rotate:
        page.set_rotation(90)
    page.get_pixmap().save(template_img_path)
    template_pdf.close()
    os.remove(qr_path)
    os.remove(template_pdf_path)
    return output_path
