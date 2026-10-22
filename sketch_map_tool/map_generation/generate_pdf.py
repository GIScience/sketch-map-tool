"""Generate a sketch map PDF."""

import io
from io import BytesIO
from typing import Tuple

import cv2
import pymupdf
from geojson import FeatureCollection
from geojson.utils import coords, map_tuples
from PIL import Image
from pyproj import Transformer
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import FILL_EVEN_ODD, Canvas
from reportlab.platypus import Frame, Paragraph, Table, TableStyle, flowables
from svglib.svglib import svg2rlg

from sketch_map_tool.definitions import PDF_RESOURCES_PATH, get_attribution
from sketch_map_tool.helpers import resize_rlg_by_width
from sketch_map_tool.models import Bbox, PaperFormat

# PIL should be able to open high resolution PNGs of large Maps:
flowables.Image.MAX_IMAGE_PIXELS = None  # ty: ignore[unresolved-attribute]

WGS84_TO_WEB_MERCATOR = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def generate_pdf(
    map_image_input: Image.Image,
    qr_code: Drawing,
    format_: PaperFormat,
    scale: float,
    layer: str,
    bbox: Bbox | None = None,
    markings: FeatureCollection | None = None,
) -> Tuple[BytesIO, BytesIO]:
    """Generate a Sketch Map PDF.

    The PDF will contain the given map image as well as
    a code for georeferencing, a scale, copyright information,
    and objects to help the feature detection during the upload processing.

    Also generate template image (PNG) as Pillow object for later upload processing.

    Returns a tuple with the Sketch Map as PDF and the map image
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

    if layer == "esri-world-imagery":
        img_format = "jpeg"
    elif layer.startswith(("osm", "oam")):
        img_format = "png"
    else:
        raise ValueError("Unexpected value for layer.")

    map_image_reportlab = pil_image_to_image_reader(map_image_input, img_format)

    # calculate m per px in map frame
    cm_per_px = frame_width * scale / map_width_px
    m_per_px = cm_per_px / 100
    map_img = create_map_frame(
        map_image_reportlab,
        format_,
        map_height_px,
        map_width_px,
        portrait,
        m_per_px,
        img_format,
        bbox,
        markings,
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

    # TODO: move to create_map_frame
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
    layer: str,
    portrait=False,
) -> None:
    normal_style = scale_style(format_, "Normal", 50)
    em = normal_style.fontSize

    # Add Logos
    gap = 1 * em
    logo_width = (width - margin - gap) / 2
    smt_logo = svg2rlg(PDF_RESOURCES_PATH / "SketchMap_Logo_compact.svg")

    smt_logo = resize_rlg_by_width(smt_logo, logo_width)
    # heigit_logo = svg2rlg(PDF_RESOURCES_PATH / "HeiGIT_Logo_compact.svg")
    # heigit_logo = resize_rlg_by_width(heigit_logo, width - margin)
    logos = Table(
        [[smt_logo]],  # TODO: add custom/second logo here
        colWidths=[logo_width + gap, logo_width],
        hAlign="LEFT",
    )
    logos.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    compass_size = width * 0.20  # this is the current ratio of the right column width
    compass = get_compass(compass_size, portrait)

    p_created_by_heigit = Paragraph("Created by HeiGIT gGmbH", normal_style)
    p_copyright = Paragraph(get_attribution(layer), normal_style)

    qr_size = min(width, height) - margin
    qr_code = resize_rlg_by_width(qr_code, qr_size)

    # fills up the remaining space, placed between
    # the TOP and the BOTTOM aligned elements
    space_filler = flowables.Spacer(
        width, 0
    )  # height will be filled after list creation
    # order all elements in column
    flowables_ = [
        logos,
        flowables.Spacer(width, 2 * em),
        # heigit_logo,
        space_filler,
        compass,
        flowables.Spacer(width, 2 * em),
        p_created_by_heigit,
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
        _, h = f.wrapOn(canvas, width - margin, height)
        flowables_height += h
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
    bbox: Bbox | None = None,
    markings: FeatureCollection | None = None,
) -> BytesIO:
    map_frame = BytesIO()
    canvas = Canvas(map_frame)
    canvas.setPageSize(landscape((height, width)))

    marker_size = width / 37
    point_radius = marker_size / 4
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
        draw_markers(canvas, marker_size, height=width, width=height)
        add_scalebar(canvas, height, width, m_per_px, format_, marker_size)
    else:
        canvas.drawImage(
            map_image,
            0,
            0,
            mask="auto",
            width=width,
            height=height,
        )
        draw_markers(canvas, marker_size, height, width)
        add_scalebar(canvas, width, height, m_per_px, format_, marker_size)

    if markings is not None and bbox is not None:
        draw_markings(
            canvas,
            markings,
            bbox,
            width,
            height,
            portrait,
            radius=point_radius,
        )

    canvas.save()
    map_frame.seek(0)
    return pdf_page_to_img(map_frame, img_format=img_format)


def draw_markers(canvas: Canvas, size: float, height: float, width: float):
    markers = get_aruco_markers(int(size))

    # 5 is to account for map frame border
    positions = [
        # corner markers
        # bottom left
        (5, 5),
        # top left
        (5, height - size - 5),
        # top right
        (width - size - 5, height - size - 5),
        # bottom right
        (width - size - 5, 5),
        # middle markers
        (0, ((height - 5) / 2 - size / 2)),
        ((width - 5) / 2 - size / 2, (height - size - 5)),
        (width - size - 5, (height - 5) / 2 - size),
        ((width - 5) / 2 - size / 2, 5),
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
    marker_size: float,
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
    # move to the left so that aruco markers are not overlayed
    scale_bar_x = (
        width + paper_format.scale_relative_xy[0] - scale_bar_length - (2 * marker_size)
    )
    scale_bar_y = height + paper_format.scale_relative_xy[1]
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
    with pymupdf.Document(stream=pdf, filetype="pdf") as doc:
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


def geo_to_canvas(
    lon: float,
    lat: float,
    bbox: Bbox,
    width: float,
    height: float,
    portrait: bool,
) -> tuple[float, float]:
    """Convert geo coordinates to map frame canvas coordinates."""
    x, y = WGS84_TO_WEB_MERCATOR.transform(lon, lat)
    fx = (x - bbox.lon_min) / (bbox.lon_max - bbox.lon_min)  # 0 = west, 1 = east
    fy = (y - bbox.lat_min) / (bbox.lat_max - bbox.lat_min)  # 0 = south, 1 = north
    if portrait:
        # The image is drawn rotated by 90°: north points left, east points up
        return (1 - fy) * height, fx * width
    return fx * width, fy * height


def draw_point(
    canvas: Canvas,
    x: float,
    y: float,
    radius: float,
    color: Color,
) -> None:
    canvas.saveState()
    canvas.setFillColor(color)
    canvas.setStrokeColor(color)
    canvas.setLineWidth(radius * 0.3)
    canvas.circle(x, y, radius, stroke=1, fill=1)
    canvas.restoreState()


def draw_polygon(
    canvas: Canvas,
    rings: list[list[tuple[float, float]]],
    color: Color,
    line_width: float,
    fill_opacity: float,
) -> None:
    """Draw a polygon. The first ring is the exterior, the others are holes."""
    canvas.saveState()
    canvas.setFillColor(color, alpha=fill_opacity)
    canvas.setStrokeColor(color)
    canvas.setLineWidth(line_width)
    path = canvas.beginPath()
    for ring in rings:
        path.moveTo(*ring[0])
        for x, y in ring[1:]:
            path.lineTo(x, y)
        path.close()
    canvas.drawPath(path, stroke=1, fill=1, fillMode=FILL_EVEN_ODD)
    canvas.restoreState()


def draw_markings(
    canvas: Canvas,
    markings: FeatureCollection,
    bbox: Bbox,
    width: float,
    height: float,
    portrait: bool,
    radius: float,
) -> None:
    """Draw all features of a GeoJSON FeatureCollection onto the map frame."""
    markings = map_tuples(
        lambda c: geo_to_canvas(c[0], c[1], bbox, width, height, portrait),
        markings,
    )
    for marking in markings["features"]:
        properties = marking["properties"]
        color = HexColor(properties["fill"])
        match marking["geometry"]["type"]:
            case "Point":
                for x, y in coords(marking):
                    draw_point(canvas, x, y, radius=radius, color=color)
            case "Polygon":
                fill_opacity = properties["fill-opacity"]
                draw_polygon(
                    canvas,
                    marking["geometry"]["coordinates"],
                    color,
                    radius * 0.3,
                    fill_opacity,
                )
            case other:
                raise ValueError(f"Unsupported geometry type: {other}")
