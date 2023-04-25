""" Generate a sketch map PDF. """
import io
from io import BytesIO
from typing import Tuple

import fitz
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph
from reportlab.platypus.flowables import Image, Spacer
from svglib.svglib import svg2rlg

from sketch_map_tool.definitions import PDF_RESOURCES_PATH
from sketch_map_tool.helpers import resize_rlg_by_width
from sketch_map_tool.models import PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None


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

    map_image_reportlab = PIL_image_to_image_reader(map_image_input)

    # calculate m per px in map frame
    # cm_per_px = frame_width * scale / map_width_px
    # m_per_px = cm_per_px / 100
    # create map_image by adding globes
    map_img = create_map_frame(
        map_image_reportlab, format_, map_height_px, map_width_px, portrait, scale
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

    if portrait:  # Rotate the map frame for correct georeferencing
        map_img_rotated_bytes = BytesIO()
        map_img_rotated = PILImage.open(map_img).rotate(270, expand=1)
        map_img_rotated.save(map_img_rotated_bytes, format="png")
        map_img_rotated_bytes.seek(0)
        map_img = map_img_rotated_bytes

    return map_pdf, map_img


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

    # Add Logos
    smt_logo = svg2rlg(PDF_RESOURCES_PATH / "SketchMap_Logo_compact.svg")
    smt_logo = resize_rlg_by_width(smt_logo, width - margin)
    heigit_logo = svg2rlg(PDF_RESOURCES_PATH / "HeiGIT_Logo_compact.svg")
    heigit_logo = resize_rlg_by_width(heigit_logo, width - margin)

    # Add compass
    compass_size = width * 0.25  # this is the current ratio of the right column width
    compass = get_compass(compass_size)

    # Add copyright information:
    p_copyright = Paragraph("Map: © OpenStreetMap Contributors", normal_style)

    # Add QR-Code:
    qr_size = min(width, height) - margin
    qr_code = resize_rlg_by_width(qr_code, qr_size)

    # fills up the remaining space, placed between the TOP and the BOTTOM aligned elements
    space_filler = Spacer(width, 0)  # height will be filled after list creation
    # order all elements in column
    flowables = [
        smt_logo,
        Spacer(width, 2 * em),
        heigit_logo,
        space_filler,
        compass,
        Spacer(width, 2 * em),
        p_copyright,
        Spacer(width, 2 * em),
        qr_code,
    ]
    space_filler.height = calculate_space_filler_height(
        canv, flowables, width, height, margin
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
    frame.addFromList(flowables, canv)


def calculate_space_filler_height(canv, flowables, width, height, margin):
    flowables_height = 0
    for f in flowables:
        if isinstance(f, Paragraph):
            # a Paragraph doesn't have a height without this command
            f.wrapOn(canv, width - margin, height)
        flowables_height += f.height
    return height - 2 * margin - flowables_height


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
    scale: float,
) -> BytesIO:
    map_frame = BytesIO()
    canv = canvas.Canvas(map_frame)
    canv.setPageSize(landscape((height, width)))

    globe_size = width / 37
    if portrait:
        canv.rotate(90)
        canv.drawImage(
            map_image,
            0,
            -height,
            mask="auto",
            width=width,
            height=height,
        )
        canv.rotate(-90)
        add_globes(canv, globe_size, height=width, width=height)
    else:
        canv.drawImage(
            map_image,
            0,
            0,
            mask="auto",
            width=width,
            height=height,
        )
        add_globes(canv, globe_size, height, width)

    canv.rect(width * 0.75, height * 0.97, ppi_to_pixel_per_cm(192), 10, fill=True)
    canv.drawString(width * 0.75, height * 0.95, f"1cm : {scale / 100}m")

    canv.save()
    map_frame.seek(0)
    return pdf_page_to_img(map_frame)


def ppi_to_pixel_per_cm(ppi: float) -> float:
    """
    :param ppi: Value in pixels per inch
    :return: Corresponding pixels per centimeter
    """
    return 0.393701*ppi


def add_scalebar(input_image: BytesIO, m_per_px: float, img_width: int, img_height: int, ppi: int) -> BytesIO:
    # render legend with matplotlib


    img = plt.imread(input_image)
    width, height = img.shape[1], img.shape[0]
    # dpi do not have to be correct, just should be fixed during processing
    dpi = 192
    plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    plt.axis("off")
    # add image to plot
    plt.imshow(img)
    plt.tight_layout(pad=0)
    scalebar = ScaleBar(m_per_px)
    plt.gca().add_artist(scalebar)

    # write output
    figure_output = BytesIO()
    plt.savefig(figure_output, dpi="figure", format="png")
    plt.close()
    figure_output.seek(0)

    # convert from RGB to RGBA
    output_image = BytesIO()
    PILImage.open(figure_output).convert("RGB").save(output_image, format="png")
    output_image.seek(0)
    return output_image


def add_globes(canv: canvas.Canvas, size: float, height: float, width: float):
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
        renderPDF.draw(globe, canv, x, y)


def get_globes(expected_size) -> Tuple[Drawing, ...]:
    """Read globe as SVG from disk, convert to RLG and scale it."""
    globes = []
    for i in range(1, 5):
        globe = svg2rlg(PDF_RESOURCES_PATH / "globe_{0}.svg".format(i))
        globe = resize_rlg_by_width(globe, expected_size)
        globes.append(globe)
    return tuple(globes)


def get_compass(size: float) -> Drawing:
    compass = svg2rlg(PDF_RESOURCES_PATH / "north.svg")
    compass = resize_rlg_by_width(compass, size)
    return compass


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
