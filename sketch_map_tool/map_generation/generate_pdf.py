"""Generate a sketch map PDF."""

import io
from io import BytesIO
from typing import Tuple

import cv2
import fitz
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame, Paragraph, flowables
from svglib.svglib import svg2rlg

from sketch_map_tool.definitions import PDF_RESOURCES_PATH, get_attribution
from sketch_map_tool.helpers import resize_rlg_by_width
from sketch_map_tool.models import Layer, PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
flowables.Image.MAX_IMAGE_PIXELS = None


def generate_pdf(
    map_image_input: Image.Image,
    qr_code: Drawing,
    format_: PaperFormat,
    scale: float,
    layer: Layer,
    aruco_markers: bool = False,
) -> Tuple[BytesIO, BytesIO]:
    """
    Generate a sketch map pdf, i.e. a PDF containing the given map image
    as well as a code for georeferencing, a scale, copyright information,
    and objects to help the feature detection during the upload processing.

    Also generate template image (PNG) as Pillow object for later upload processing

    :param map_image_input: Image of the map to be used as sketch map.
    :param qr_code: QR code to be included on the sketch map for georeferencing.
    :param format_: Paper format of the PDF document.
    :param scale: Ratio for the scale in the sketch map legend
    :return: Sketch Map PDF, Template image
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

    if layer == Layer.ESRI_WORLD_IMAGERY:
        img_format = "jpeg"
    else:
        img_format = "png"

    map_image_reportlab = pil_image_to_image_reader(map_image_input, img_format)

    # calculate m per px in map frame
    cm_per_px = frame_width * scale / map_width_px
    m_per_px = cm_per_px / 100
    # create map_image by adding globes
    map_img = create_map_frame(
        map_image_reportlab,
        format_,
        map_height_px,
        map_width_px,
        portrait,
        m_per_px,
        img_format,
        aruco_markers,
    )

    map_pdf = BytesIO()
    canvas = Canvas(map_pdf)
    canvas.setPageSize(landscape((format_.height * cm, format_.width * cm)))
    # Add map to canvas:
    canv_map_margin = map_margin
    canvas.drawImage(
        ImageReader(map_img),
        canv_map_margin * cm,
        canv_map_margin * cm,
        mask="auto",
        width=frame_width * cm,
        height=frame_height * cm,
    )

    # TODO move to create_map_frame
    # Add a border around the map
    canvas.rect(
        map_margin * cm,
        map_margin * cm,
        frame_width * cm,
        frame_height * cm,
        fill=0,
    )

    canvas.setFontSize(format_.font_size)
    canvas.setFillColorRGB(0, 0, 0)

    draw_right_column(
        canvas,
        column_width,
        column_height,
        column_origin_x,
        column_origin_y,
        column_margin,
        qr_code,
        scale,
        format_,
        layer,
        portrait,
    )

    # Generate PDFs:
    canvas.save()

    map_pdf.seek(0)
    map_img.seek(0)

    if portrait:  # Rotate the map frame for correct georeferencing
        map_img_rotated_bytes = BytesIO()
        map_img_rotated = Image.open(map_img).rotate(270, expand=1)
        map_img_rotated.save(map_img_rotated_bytes, format="png")
        map_img_rotated_bytes.seek(0)
        map_img = map_img_rotated_bytes

    return map_pdf, map_img


def draw_right_column(
    canvas: Canvas,
    width: float,
    height: float,
    x: float,
    y: float,
    margin: float,
    qr_code: Drawing,
    scale,  # TODO: is not accessed
    format_,
    layer: Layer,
    portrait=False,
) -> None:
    normal_style = scale_style(format_, "Normal", 50)
    em = normal_style.fontSize

    # Add Logos
    smt_logo = svg2rlg(PDF_RESOURCES_PATH / "SketchMap_Logo_compact.svg")
    smt_logo = resize_rlg_by_width(smt_logo, width - margin)
    heigit_logo = svg2rlg(PDF_RESOURCES_PATH / "HeiGIT_Logo_compact.svg")
    heigit_logo = resize_rlg_by_width(heigit_logo, width - margin)

    # Add compass
    compass_size = width * 0.25  # this is the current ratio of the right column width
    compass = get_compass(compass_size, portrait)

    # Add copyright information:
    p_copyright = Paragraph(get_attribution(layer), normal_style)

    # Add QR-Code:
    qr_size = min(width, height) - margin
    qr_code = resize_rlg_by_width(qr_code, qr_size)

    # fills up the remaining space, placed between
    # the TOP and the BOTTOM aligned elements
    space_filler = flowables.Spacer(
        width, 0
    )  # height will be filled after list creation
    # order all elements in column
    flowables_ = [
        smt_logo,
        flowables.Spacer(width, 2 * em),
        heigit_logo,
        space_filler,
        compass,
        flowables.Spacer(width, 2 * em),
        p_copyright,
        flowables.Spacer(width, 2 * em),
        qr_code,
    ]
    space_filler.height = calculate_space_filler_height(
        canvas, flowables_, width, height, margin
    )
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
    frame.addFromList(flowables_, canvas)


def calculate_space_filler_height(canvas, flowables_, width, height, margin):
    flowables_height = 0
    for f in flowables_:
        if isinstance(f, Paragraph):
            # a Paragraph doesn't have a height without this command
            f.wrapOn(canvas, width - margin, height)
        flowables_height += f.height
    return height - 2 * margin - flowables_height


def scale_style(format_: PaperFormat, style_name: str, factor: float) -> ParagraphStyle:
    # factor is an arbitrary number to scale the font depending on the paper size
    normal_style = getSampleStyleSheet()[style_name]
    font_factor = format_.width / factor
    normal_style.fontSize *= font_factor
    normal_style.leading *= font_factor
    return normal_style


def pil_image_to_image_reader(map_image_input, img_format):
    map_image_raw = io.BytesIO()
    if map_image_input.mode != "RGB" and img_format == "jpeg":
        map_image_input = map_image_input.convert("RGB")
    map_image_input.save(map_image_raw, format=img_format)
    map_image_reportlab = ImageReader(map_image_raw)
    return map_image_reportlab


def create_map_frame(
    map_image: ImageReader,
    format_: PaperFormat,
    height: int,
    width: int,
    portrait: bool,
    m_per_px: float,
    img_format: str,
    aruco_markers: bool = False,
) -> BytesIO:
    map_frame = BytesIO()
    canvas = Canvas(map_frame)
    canvas.setPageSize(landscape((height, width)))

    globe_size = width / 37
    if portrait:
        canvas.rotate(90)
        canvas.drawImage(
            map_image,
            0,
            -height,
            mask="auto",
            width=width,
            height=height,
        )
        canvas.rotate(-90)
        if aruco_markers:
            draw_markers(canvas, globe_size, height=width, width=height)
        else:
            draw_globes(canvas, globe_size, height=width, width=height)
        add_scalebar(
            canvas, width=height, height=width, m_per_px=m_per_px, paper_format=format_
        )
    else:
        canvas.drawImage(
            map_image,
            0,
            0,
            mask="auto",
            width=width,
            height=height,
        )
        if aruco_markers:
            draw_markers(canvas, globe_size, height, width)
        else:
            draw_globes(canvas, globe_size, height, width)
        add_scalebar(canvas, width, height, m_per_px, format_)

    canvas.save()
    map_frame.seek(0)
    return pdf_page_to_img(map_frame, img_format=img_format)


def draw_globes(canvas: Canvas, size: float, height: float, width: float):
    globe_1, globe_2, globe_3, globe_4 = get_globes(size)

    h = height - size
    w = width - size

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
        renderPDF.draw(globe, canvas, x, y)


def get_globes(expected_size) -> Tuple[Drawing, ...]:
    """Read globe as SVG from disk, convert to RLG and scale it."""
    globes = []
    for i in range(1, 5):
        globe = svg2rlg(PDF_RESOURCES_PATH / "globe_{0}.svg".format(i))
        globe = resize_rlg_by_width(globe, expected_size)
        globes.append(globe)
    return tuple(globes)


def draw_markers(canvas: Canvas, size: float, height: float, width: float):
    markers = get_aruco_markers(int(size))

    h = height - size
    w = width - size

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
    for m, (x, y) in zip(markers, positions):
        canvas.drawImage(ImageReader(Image.fromarray(m)), x, y)


def get_compass(size: float, portrait=False) -> Drawing:
    file_name = "north.svg"
    if portrait:
        file_name = "north_rotated.svg"
    compass = svg2rlg(PDF_RESOURCES_PATH / file_name)
    compass = resize_rlg_by_width(compass, size)
    return compass


def add_scalebar(
    canvas: Canvas,
    width: int,
    height: int,
    m_per_px: float,
    paper_format: PaperFormat,
):
    scale_bar_length = round(width * 0.075)
    corresponding_meters = round(m_per_px * scale_bar_length)
    if corresponding_meters >= 1000:
        corresponding_meters = (
            corresponding_meters - corresponding_meters % 1000 + 1000
        )  # Round up to the next 1000m
    elif corresponding_meters >= 500:
        corresponding_meters = (
            corresponding_meters - corresponding_meters % 500 + 500
        )  # Round up to the next 500m
    elif corresponding_meters >= 100:
        corresponding_meters = (
            corresponding_meters - corresponding_meters % 100 + 100
        )  # Round up to the next 100m
    elif corresponding_meters >= 50:
        corresponding_meters = (
            corresponding_meters - corresponding_meters % 50 + 50
        )  # Round up to the next 50m
    else:
        corresponding_meters = (
            corresponding_meters - corresponding_meters % 10 + 10
        )  # Round up to the next 10m
    scale_bar_length = round(corresponding_meters / m_per_px)
    scale_bar_x, scale_bar_y = (
        width + paper_format.scale_relative_xy[0] - scale_bar_length,
        height + paper_format.scale_relative_xy[1],
    )
    canvas.setFillColorRGB(255, 255, 255)
    background_params = paper_format.scale_background_params
    canvas.rect(
        scale_bar_x + background_params[0],
        scale_bar_y + background_params[1],
        scale_bar_length + background_params[2],
        background_params[3],
        fill=True,
    )
    canvas.setFillColorRGB(0, 0, 0)
    canvas.rect(
        scale_bar_x, scale_bar_y, scale_bar_length, paper_format.scale_height, fill=True
    )
    canvas.setFont(
        "Times-Roman", paper_format.font_size * 2
    )  # Should be a bit bigger than e.g. the copyright note
    canvas.drawString(
        scale_bar_x,
        scale_bar_y - paper_format.scale_distance_to_text,
        f"{corresponding_meters}m",
    )


def pdf_page_to_img(pdf: BytesIO, img_format, page_id=0) -> BytesIO:
    """Extract page from PDF, convert it to PNG and write it as Pillow Image."""
    img = BytesIO()
    with fitz.Document(stream=pdf, filetype="pdf") as doc:
        page = doc.load_page(page_id)
        # TODO: Is this necessary?
        # if portrait:
        #     page.set_rotation(90)
        page.get_pixmap().pil_save(img, format=img_format)
    img.seek(0)
    return img


def get_aruco_markers(size: int) -> list:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    # TODO: change markers in x direction depending or landscape or
    # portrait
    markers = []
    for i in range(8):
        marker = cv2.aruco.generateImageMarker(dictionary, i, int((size * 0.9)))
        w = int(size * 0.1)
        marker = cv2.copyMakeBorder(
            src=marker,
            top=w,
            bottom=w,
            left=w,
            right=w,
            borderType=cv2.BORDER_CONSTANT,
            value=(255, 255, 255),  # white border
        )
        markers.append(marker)
    return markers
