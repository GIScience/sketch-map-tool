"""
Generate a sketch map PDF.
"""
from typing import Tuple

from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm
from reportlab.lib import utils
from svglib.svglib import svg2rlg
from PIL import Image
import fitz
import qrcode
import qrcode.image.svg
import os
import io
from helper_modules.bbox_utils import Bbox

# PIL should be able to open high resolution PNGs of large Maps:
Image.MAX_IMAGE_PIXELS = None

RESOURCE_PATH = "printer/modules/resources/"


class PaperFormat:  # pylint: disable=R0903
    """
    Properties of sketch maps to be printed on a certain paper format
    """

    def __init__(self,
                 width: float,
                 height: float,
                 right_margin: float,
                 font_size: int,
                 qr_scale: float,
                 compass_scale: float,
                 globe_scale: float,
                 scale_height: float,
                 qr_y: float,
                 indent: float,
                 qr_contents_distances_not_rotated: Tuple[int, int],
                 qr_contents_distance_rotated: int,
                 ):  # pylint: disable=R0913
        """
        :param width: Width of the paper in cm.
        :param height: Height of the paper in cm.
        :param right_margin: Width of the margin in cm, i.e. the area not covered by the map
                             containing the QR code, scale, copyright information, etc.
        :param font_size: Font size in pt to be used for the copyright info and code contents.
        :param qr_scale: Scale factor for the QR code SVG.
        :param compass_scale: Scale factor for the compass SVG.
        :param globe_scale: Scale factor for the globe SVGs.
        :param scale_height: Height of the scale in cm, the width is calculated according to the
                             actual size of the bounding box and its size on the map.
        :param qr_y: Vertical distance from the QR code to the origin in cm.
        :param indent: Indentation in cm of the contents in the margin relative to the map area.
        :param qr_contents_distances_not_rotated: (Vertical distance in cm from the qr code contents
                                                   in text form to the position of the copyright
                                                   notice, Indentation in cm additional to the
                                                   calculated base indentation of all rotated
                                                   contents).
        :param qr_contents_distance_rotated: Horizontal distance in cm from the map area additional
                                             to the calculated base indentation of all rotated
                                             contents.
        """
        self.width = width
        self.height = height
        self.right_margin = right_margin
        self.font_size = font_size
        self.qr_scale = qr_scale
        self.compass_scale = compass_scale
        self.globe_scale = globe_scale
        self.scale_height = scale_height
        self.qr_y = qr_y
        self.indent = indent
        self.qr_contents_distances_not_rotated = qr_contents_distances_not_rotated
        self.qr_contents_distance_rotated = qr_contents_distance_rotated


def generate_pdf(output_dir_path: str,  # pylint: disable=R0914  # noqa: C901
                 map_image: Image,
                 bbox: Bbox,
                 current_date: str,
                 paper_format: str = "a0") -> str:
    """
    Generate a sketch map pdf, i.e. a PDF containing the map image as well as a code for
    georeferencing, a scale, copyright information, and objects to help the feature detection
    during the upload processing.

    :output_dir_path: Path to the directory in which the output PDF should be stored.
    :param map_image: Image of the map to be used as sketch map.
    :param bbox: Bounding box, needed for naming, scale calculation and  the code for
                 georeferencing.
    :param current_date: Current date, needed for naming and the QR code.
    :param paper_format: Paper format of the PDF document ('a0', ..., 'a5', 'tabloid', 'legal', or
                         'letter').
    :return: Path to the generated PDF file.
    """
    if paper_format not in ("a0", "a1", "a2", "a3", "a4", "a5", "tabloid", "legal", "letter",
                            "ledger"):
        raise ValueError(f"Paper format '{paper_format}' not allowed. Please use 'a0', ..., 'a5', "
                         "'tabloid', 'legal', or 'letter'.")

    if paper_format == "a0":
        paper = PaperFormat(
            width=118.9,
            height=84.1,
            right_margin=15,
            font_size=25,
            qr_scale=3.5,
            compass_scale=1,
            globe_scale=0.5,
            scale_height=1,
            qr_y=0.5,
            indent=0.5,
            qr_contents_distances_not_rotated=(10, 10),
            qr_contents_distance_rotated=10,
        )
    elif paper_format == "a1":
        paper = PaperFormat(
            width=84.1,
            height=59.4,
            right_margin=12,
            font_size=20,
            qr_scale=2.5,
            compass_scale=0.75,
            globe_scale=0.375,
            scale_height=1,
            qr_y=0.5,
            indent=0.5,
            qr_contents_distances_not_rotated=(5, 8),
            qr_contents_distance_rotated=7,
        )
    elif paper_format == "a2":
        paper = PaperFormat(
            width=59.4,
            height=42,
            right_margin=7.5,
            font_size=12,
            qr_scale=1.75,
            compass_scale=0.5,
            globe_scale=0.25,
            scale_height=0.75,
            qr_y=0.5,
            indent=0.5,
            qr_contents_distances_not_rotated=(6, 4),
            qr_contents_distance_rotated=4,
        )
    elif paper_format == "a3":
        paper = PaperFormat(
            width=42,
            height=29.7,
            right_margin=7,
            font_size=11,
            qr_scale=1.5,
            compass_scale=0.33,
            globe_scale=0.165,
            scale_height=0.5,
            qr_y=0.5,
            indent=0.5,
            qr_contents_distances_not_rotated=(3, 4),
            qr_contents_distance_rotated=4,
        )
    elif paper_format == "a4":
        paper = PaperFormat(
            width=29.7,
            height=21,
            right_margin=5,
            font_size=8,
            qr_scale=1,
            compass_scale=0.25,
            globe_scale=0.125,
            scale_height=0.33,
            qr_y=0.1,
            indent=0.25,
            qr_contents_distances_not_rotated=(2, 3),
            qr_contents_distance_rotated=3,
        )
    elif paper_format == "a5":
        paper = PaperFormat(
            width=21,
            height=14.8,
            right_margin=3,
            font_size=5,
            qr_scale=0.75,
            compass_scale=0.2,
            globe_scale=0.1,
            scale_height=0.25,
            qr_y=0.1,
            indent=0.1,
            qr_contents_distances_not_rotated=(2, 2),
            qr_contents_distance_rotated=2,
        )
    elif paper_format == "legal":
        paper = PaperFormat(
            width=35.6,
            height=21.6,
            right_margin=5,
            font_size=8,
            qr_scale=1,
            compass_scale=0.25,
            globe_scale=0.125,
            scale_height=0.33,
            qr_y=0.1,
            indent=0.25,
            qr_contents_distances_not_rotated=(2, 3),
            qr_contents_distance_rotated=3,
        )
    elif paper_format in ["tabloid", "ledger"]:
        paper = PaperFormat(
            width=43.2,
            height=27.9,
            right_margin=7,
            font_size=11,
            qr_scale=1.5,
            compass_scale=0.33,
            globe_scale=0.165,
            scale_height=0.5,
            qr_y=0.01,
            indent=0.5,
            qr_contents_distances_not_rotated=(3, 4),
            qr_contents_distance_rotated=4,
        )
    else:  # letter
        paper = PaperFormat(
            width=27.9,
            height=21.6,
            right_margin=5,
            font_size=8,
            qr_scale=1,
            compass_scale=0.25,
            globe_scale=0.125,
            scale_height=0.33,
            qr_y=0.1,
            indent=0.25,
            qr_contents_distances_not_rotated=(2, 3),
            qr_contents_distance_rotated=3,
        )

    map_width_px, map_height_px = map_image.size

    # Adjust map orientation and scaling:
    rotate = map_width_px < map_height_px
    ratio = map_height_px / map_width_px

    if not rotate:
        adjusted_width = paper.width - paper.right_margin  # cm
        adjusted_height = (paper.width-paper.right_margin)*ratio  # cm

        if adjusted_height > paper.height:
            adjusted_height = paper.height
            adjusted_width = paper.height/ratio
    else:
        adjusted_height = paper.width - paper.right_margin  # cm
        adjusted_width = (paper.width-paper.right_margin)/ratio  # cm
        if adjusted_width > paper.height:
            adjusted_width = paper.height  # cm
            adjusted_height = paper.height*ratio  # cm

    map_image_raw = io.BytesIO()
    map_image.save(map_image_raw, format="png")
    map_image_reportlab = utils.ImageReader(map_image_raw)

    # Set-up everything for the reportlab pdf:
    output_path = f"{output_dir_path}{current_date}__{bbox.get_str(mode='minus')}__" \
                  f"{paper_format}.pdf"
    canv = canvas.Canvas(output_path)
    template_pdf_path = output_path.replace(".pdf", "_template.pdf")
    template = canvas.Canvas(template_pdf_path)
    canv.setPageSize(landscape((paper.height * cm, paper.width * cm)))
    template.setPageSize(landscape((adjusted_height * cm, adjusted_width * cm)))

    # Add map to canvas:
    for canvas_object in [canv, template]:
        if rotate:
            canvas_object.rotate(90)
            canvas_object.drawImage(map_image_reportlab, 0, (-adjusted_height)*cm, mask="auto",
                                    width=adjusted_width*cm, height=adjusted_height*cm)
            canvas_object.rotate(-90)
        else:
            canvas_object.drawImage(map_image_reportlab, 0, 0, mask="auto", width=adjusted_width*cm,
                                    height=adjusted_height*cm)

    if rotate:
        adjusted_width, adjusted_height = adjusted_height, adjusted_width

    # Generate QR-Code:
    qr_factory = qrcode.image.svg.SvgPathImage
    qr_text = f"{bbox.get_str(mode='comma')};{current_date};{paper_format}"

    qr = qrcode.make(qr_text, image_factory=qr_factory)  # pylint: disable=C0103
    qr_path = output_path.replace(".pdf", "_qr.svg")
    qr.save(qr_path)
    svg_qr = svg2rlg(qr_path)
    svg_qr.scale(paper.qr_scale, paper.qr_scale)

    # Import compass and globes:
    compass = svg2rlg(RESOURCE_PATH+"north.svg")
    compass.scale(paper.compass_scale, paper.compass_scale)
    svg_globe_1 = svg2rlg(RESOURCE_PATH+"globe_1.svg")
    svg_globe_2 = svg2rlg(RESOURCE_PATH+"globe_2.svg")
    svg_globe_3 = svg2rlg(RESOURCE_PATH+"globe_3.svg")
    svg_globe_4 = svg2rlg(RESOURCE_PATH+"globe_4.svg")
    svg_globe_1.scale(paper.globe_scale, paper.globe_scale)
    svg_globe_2.scale(paper.globe_scale, paper.globe_scale)
    svg_globe_3.scale(paper.globe_scale, paper.globe_scale)
    svg_globe_4.scale(paper.globe_scale, paper.globe_scale)
    globe_length = 150*paper.globe_scale

    # Calculate scale:
    scale = adjusted_width/bbox.get_width()  # cm per meter

    if scale*10000 <= paper.right_margin-1:
        scale_length = scale*10000
        scale_text = ["5km", "10km"]
    elif scale*5000 <= paper.right_margin-1:
        scale_length = scale*5000
        scale_text = ["2.5km", "5km"]
    elif scale*2000 <= paper.right_margin-1:
        scale_length = scale*2000
        scale_text = ["1km", "2km"]
    elif scale*1000 <= paper.right_margin-1:
        scale_length = scale*1000
        scale_text = ["500m", "1km"]
    elif scale*500 <= paper.right_margin-1:
        scale_length = scale*500
        scale_text = ["250m", "500m"]
    elif scale*200 <= paper.right_margin-1:
        scale_length = scale*200
        scale_text = ["100m", "200m"]
    elif scale*100 <= paper.right_margin-1:
        scale_length = scale*100
        scale_text = ["50m", "100m"]
    elif scale*50 <= paper.right_margin-1:
        scale_length = scale*50
        scale_text = ["25m", "50m"]
    else:
        scale_length = scale*10
        scale_text = ["5m", "10m"]

    # Add a border around the map
    canv.rect(0, 0, adjusted_width*cm, adjusted_height*cm, fill=0)

    canv.setFontSize(paper.font_size)
    canv.setFillColorRGB(0, 0, 0)
    copyright_text_origin = 0.24 * paper.height * cm
    rotate_indent = -(adjusted_width + paper.compass_scale * 3 + 3 * paper.indent) * cm

    if rotate:
        canv.rotate(90)

        # Add copyright information:
        text = canv.beginText()
        text.setTextOrigin(copyright_text_origin, rotate_indent)
        text.textLines("Map: (C)OpenStreetMap Contributors")
        canv.drawText(text)

        # Add QR contents:
        text = canv.beginText()
        text.setTextOrigin(copyright_text_origin,
                           rotate_indent - paper.qr_contents_distance_rotated * cm)
        text.textLines(f"Code contents: '{qr_text}'")
        canv.drawText(text)

        # Add QR-Code:
        renderPDF.draw(svg_qr, canv, paper.qr_y*cm, -(paper.width-0.1)*cm)

        # Add scale:
        x_scale_cm = 0.24*paper.height+paper.font_size/1.5
        canv.rect(x_scale_cm*cm, rotate_indent, scale_length/2*cm,
                  paper.scale_height*cm, fill=1)
        canv.rect((x_scale_cm+scale_length/2)*cm, rotate_indent,
                  scale_length/2*cm, paper.scale_height*cm, fill=0)
        canv.drawString((x_scale_cm+scale_length/2-paper.font_size/25)*cm,
                        rotate_indent-paper.height*0.012*cm, scale_text[0])
        canv.drawString((x_scale_cm+scale_length-paper.font_size/25)*cm,
                        rotate_indent-paper.height*0.012*cm, scale_text[1])

        # Add compass:
        renderPDF.draw(compass,
                       canv,
                       (0.24*paper.height+paper.font_size/1.5+scale_length+paper.font_size/4)*cm,
                       rotate_indent-2*paper.compass_scale*cm)
        canv.rotate(-90)
    else:
        # Add copyright information:
        text = canv.beginText()
        text.setTextOrigin((adjusted_width+paper.indent)*cm, copyright_text_origin)
        if paper_format in ["a0", "a1", "a2"]:
            text.textLines("Map:\n\n(C)OpenStreetMap Contributors")
        else:
            text.textLines("Map:\n(C)OpenStreetMap Contributors")
        canv.drawText(text)

        # Add QR contents:
        canv.rotate(90)
        text = canv.beginText()
        text.setTextOrigin(copyright_text_origin + paper.qr_contents_distances_not_rotated[0]*cm,
                           rotate_indent - paper.qr_contents_distances_not_rotated[1] * cm)
        text.textLines(f"Code contents: '{qr_text}'")
        canv.drawText(text)
        canv.rotate(-90)

        # Add QR-Code:
        renderPDF.draw(svg_qr, canv, (adjusted_width+paper.indent)*cm, paper.qr_y*cm)

        # Add scale:
        canv.rect((adjusted_width+paper.indent)*cm, 0.297*paper.height*cm, scale_length/2*cm,
                  paper.scale_height*cm, fill=1)
        canv.rect((adjusted_width+paper.indent+scale_length/2)*cm, 0.297*paper.height*cm,
                  scale_length/2*cm, paper.scale_height*cm, fill=0)
        canv.drawString((adjusted_width+paper.indent+scale_length/2-paper.font_size/25)*cm,
                        0.285*paper.height*cm, scale_text[0])
        canv.drawString((adjusted_width+paper.indent+scale_length-paper.font_size/25)*cm,
                        0.285*paper.height*cm, scale_text[1])

        # Add compass:
        renderPDF.draw(compass, canv, (adjusted_width+paper.indent)*cm, 0.333*paper.height*cm)

    for canvas_object in [canv, template]:
        # Add globes to improve feature detection during upload processing
        renderPDF.draw(svg_globe_1, canvas_object, 0, 0)
        renderPDF.draw(svg_globe_3, canvas_object, 0, adjusted_height*cm-globe_length)
        renderPDF.draw(svg_globe_4, canvas_object, adjusted_width*cm-globe_length,
                       adjusted_height*cm-globe_length)
        renderPDF.draw(svg_globe_2, canvas_object, adjusted_width*cm-globe_length, 0)
        renderPDF.draw(svg_globe_2, canvas_object, 0, adjusted_height/2*cm-0.5*globe_length)
        renderPDF.draw(svg_globe_1, canvas_object, adjusted_width/2*cm-0.5*globe_length,
                       adjusted_height*cm-globe_length)
        renderPDF.draw(svg_globe_3, canvas_object, adjusted_width*cm-globe_length,
                       adjusted_height/2*cm-globe_length/2)
        renderPDF.draw(svg_globe_4, canvas_object, adjusted_width/2*cm-globe_length/2, 0)

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
