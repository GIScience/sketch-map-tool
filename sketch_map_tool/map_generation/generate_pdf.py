""" Generate a sketch map PDF. """
import io
from io import BytesIO
from pathlib import Path
from typing import Tuple

import fitz
from PIL import Image as PILImage
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph
from reportlab.platypus.flowables import Image, Spacer, TopPadder
from svglib.svglib import svg2rlg

from sketch_map_tool.models import PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None

RESOURCE_PATH = Path(__file__).parent.resolve() / "resources"


def generate_pdf(  # noqa: C901
    map_image_input: PILImage,
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
    :param map_image_input: Image of the map to be used as sketch map.
    :param bbox: Bounding box, needed for naming, scale calculation and  the code for
                 georeferencing.
    :param paper_format: Paper format of the PDF document.
    :return: Path to the generated PDF file.
    """
    map_width_px, map_height_px = map_image_input.size
    map_margin = format_.map_margin

    # TODO: Use orientation parameter to determine rotation
    portrait = map_width_px < map_height_px
    if portrait:
        ratio = map_width_px / map_height_px
    else:
        ratio = map_height_px / map_width_px
    # calculate right_margin
    right_margin = format_.right_margin
    # calculate width of map frame
    frame_width = format_.width - right_margin - 2 * map_margin  # cm
    # making sure the map frame isn't higher than possible
    frame_height = min(frame_width * ratio, format_.height - 2 * map_margin)  # cm
    # making sure that the ratio is still correct
    frame_width = frame_height / ratio
    # calculating right column sizes
    column_width = right_margin * cm
    column_height = format_.height * cm
    column_origin_x = (frame_width + 2 * map_margin) * cm
    column_origin_y = 0
    column_margin = map_margin * cm

    map_image_reportlab = PIL_image_to_image_reader(map_image_input)

    # create map_image by adding globes
    map_img = create_map_frame(
        map_image_reportlab, format_, frame_height, frame_width, portrait
    )

    map_pdf = BytesIO()
    # create output canvas
    canv_map = canvas.Canvas(map_pdf)
    canv_map.setPageSize(landscape((format_.height * cm, format_.width * cm)))
    # Add map to canvas:
    canv_map_margin = map_margin
    canv_map.drawImage(
        ImageReader(map_img),
        canv_map_margin * cm,
        canv_map_margin * cm,
        mask="auto",
        width=frame_width * cm,
        height=frame_height * cm,
    )

    # TODO move to create_map_frame
    # Add a border around the map
    canv_map.rect(
        map_margin * cm,
        map_margin * cm,
        frame_width * cm,
        frame_height * cm,
        fill=0,
    )

    canv_map.setFontSize(format_.font_size)
    canv_map.setFillColorRGB(0, 0, 0)

    # TODO implement for portrait
    draw_right_column(
        canv_map,
        column_width,
        column_height,
        column_origin_x,
        column_origin_y,
        column_margin,
        qr_code,
        scale,
        format_,
    )

    # Generate PDFs:
    canv_map.save()

    map_pdf.seek(0)
    map_img.seek(0)

    return map_pdf, map_img


# TODO REMOVE, NOT IN USE
def create_right_column_portrait(
    canv_map,
    compass,
    copyright_text_origin,
    format_,
    map_margin,
    qr_code,
    rotate_indent,
    scale_length,
    scale_text,
):
    canv_map.rotate(90)
    # Add copyright information:
    text = canv_map.beginText()
    text.setTextOrigin(copyright_text_origin + 1.0 * cm, rotate_indent)
    text.textLines("Map: © OpenStreetMap Contributors")
    canv_map.drawText(text)
    # Add QR-Code:
    renderPDF.draw(qr_code, canv_map, format_.qr_y * cm, -(format_.width - 1.1) * cm)
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


def draw_right_column(
    canv: canvas.Canvas,
    width: float,
    height: float,
    x: float,
    y: float,
    margin: float,
    qr_code: Drawing,
    scale,
    format_,
) -> None:
    normal_style = scale_style(format_, "Normal", 50)
    em = normal_style.fontSize

    # Add compass
    compass_size = width * 0.25  # this is the current ratio of the right column width
    compass = get_compass(compass_size)

    # Add copyright information:
    p_copyright = Paragraph("Map: © OpenStreetMap Contributors", normal_style)

    # Add QR-Code:
    qr_size = min(width, height) - margin
    qr_code = resize_rlg(qr_code, qr_size)

    # Add scale:
    scale = get_scale(
        scale,
        width_max=width - margin,
        scale_height=format_.scale_height * cm,
        font_size=em,
    )

    # order all elements in column
    flowables = [
        compass,
        Spacer(width, 2 * em),
        scale,
        Spacer(width, 2 * em),
        p_copyright,
        TopPadder(qr_code),
    ]
    frame = Frame(
        x,
        y,
        width,
        height,
        leftPadding=0,
        bottomPadding=margin,
        rightPadding=margin,
        topPadding=margin,
    )
    frame.addFromList(flowables, canv)


def scale_style(format_: PaperFormat, style_name: str, factor: float) -> ParagraphStyle:
    # factor is an arbitrary number to scale the font depending on the paper size
    normal_style = getSampleStyleSheet()[style_name]
    font_factor = format_.width / factor
    normal_style.fontSize *= font_factor
    normal_style.leading *= font_factor
    return normal_style


def PIL_image_to_image_reader(map_image_input):
    map_image_raw = io.BytesIO()
    map_image_input.save(map_image_raw, format="png")
    map_image_reportlab = ImageReader(map_image_raw)
    return map_image_reportlab


def create_map_frame(
    map_image: ImageReader,
    format_: PaperFormat,
    height: float,
    width: float,
    portrait: bool,
) -> BytesIO:
    map_frame = BytesIO()
    canv = canvas.Canvas(map_frame)
    canv.setPageSize(landscape((height * cm, width * cm)))

    if portrait:
        width, height = height, width
        canv.rotate(90)
        canv.drawImage(
            map_image,
            0,
            -height * cm,
            mask="auto",
            width=width * cm,
            height=height * cm,
        )
        canv.rotate(-90)
        add_globes(canv, format_, width, height)
    else:
        canv.drawImage(
            map_image,
            0,
            0,
            mask="auto",
            width=width * cm,
            height=height * cm,
        )
        add_globes(canv, format_, height, width)

    canv.save()
    map_frame.seek(0)
    return pdf_page_to_img(map_frame)


def add_globes(canv: canvas.Canvas, format_: PaperFormat, height: float, width: float):
    globe_1, globe_2, globe_3, globe_4 = get_globes(format_.globe_scale)

    size = 150 * format_.globe_scale
    h = height * cm - size
    w = width * cm - size

    globes = [
        # corner
        globe_1,
        globe_3,
        globe_4,
        globe_2,
        # middle
        globe_2,
        globe_1,
        globe_3,
        globe_4,
    ]
    positions = [
        # corner globes
        # bottom left
        (0, 0),
        # top left
        (0, h),
        # top right
        (w, h),
        # bottom right
        (w, 0),
        # middle globes
        (0, h / 2),
        (w / 2, h),
        (w, h / 2),
        (w / 2, 0),
    ]
    for globe, (x, y) in zip(globes, positions):
        renderPDF.draw(globe, canv, x, y)


def get_globes(scale_factor) -> Tuple[Drawing, ...]:
    """Read globe as SVG from disk, convert to RLG and scale it."""
    globes = []
    for i in range(1, 5):
        globe = svg2rlg(RESOURCE_PATH / "globe_{0}.svg".format(i))
        globe.scale(scale_factor, scale_factor)
        globes.append(globe)
    return tuple(globes)


def get_compass(size: float) -> Drawing:
    compass = svg2rlg(RESOURCE_PATH / "north.svg")
    compass = resize_rlg(compass, size)
    return compass


def get_scale(
    scale_value: float, width_max: float, scale_height: float, font_size: float
) -> tuple[float, tuple[str, str]]:
    """Get scale length [cm] and scale text.

    scale_value: Scale denominator
    width_max: Maximal width of the scale bar [cm]
    scale_height: Height of the returned scale

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
        scale_length = factor / scale_value
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
    scale = Drawing(width_max, scale_height + font_size * 1.25)
    scale.add(
        Rect(
            0,
            scale.height - scale_height,
            scale_length / 2,
            scale_height,
            fillColor="black",
        )
    )
    scale.add(
        Rect(
            scale_length / 2,
            scale.height - scale_height,
            scale_length / 2,
            scale_height,
            fillColor="white",
        )
    )
    scale.add(
        String(scale_length / 2, 0, scale_text[0], fontSize=font_size, textAnchor="end")
    )
    scale.add(
        String(scale_length, 0, scale_text[1], fontSize=font_size, textAnchor="end")
    )
    return scale


def pdf_page_to_img(pdf: BytesIO, page_id=0) -> BytesIO:
    """Extract page from PDF, convert it to PNG and write it as Pillow Image."""
    img = BytesIO()
    with fitz.Document(stream=pdf, filetype="pdf") as doc:
        page = doc.load_page(page_id)
        # TODO: Is this necessary?
        # if portrait:
        #     page.set_rotation(90)
        page.get_pixmap().pil_save(img, format="png")
    img.seek(0)
    return img


def resize_rlg(d: Drawing, size: float) -> Drawing:
    factor = size / d.width
    d.scale(factor, factor)
    d.asDrawing(size, size)
    return d
