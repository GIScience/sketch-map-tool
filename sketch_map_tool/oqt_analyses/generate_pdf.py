from io import BytesIO

from reportlab.graphics.shapes import Circle, Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table
from svglib.svglib import svg2rlg

from sketch_map_tool.definitions import PDF_RESOURCES_PATH
from sketch_map_tool.helpers import resize_rlg_by_height


def generate_pdf(report_properties: dict) -> BytesIO:
    report_light_radius = 15
    indicator_light_radius = 10
    indicator_img_width = 300
    indicator_table_margin = 10

    metadata = report_properties["report"]["metadata"]
    result = report_properties["report"]["result"]

    bytes_output = BytesIO()
    doc = SimpleDocTemplate(bytes_output)
    styles = getSampleStyleSheet()

    # Report Results
    general_heading = Paragraph("Quality Report", styles["Heading1"])
    general_heading.keepWithNext = True
    report_description = Paragraph(metadata["description"])
    report_heading = Paragraph("Report Result", styles["Heading2"])
    report_heading.keepWithNext = True
    report_traffic_light = generate_traffic_light(
        result["label"], radius=report_light_radius
    )
    report_result_description = Paragraph(result["description"])
    report_result_table = Table(
        [[report_traffic_light, report_result_description]],
        colWidths=[report_light_radius * 4, None],
        style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE")],
    )
    # Indicator Results
    indicators_heading = Paragraph("Indicator Results", styles["Heading2"])
    indicators_heading.keepWithNext = True
    components = [
        general_heading,
        report_description,
        report_heading,
        report_result_table,
        indicators_heading,
    ]
    for indicator in report_properties["indicators"]:
        metadata = indicator["metadata"]
        result = indicator["result"]

        indicator_heading = Paragraph(
            "{} ({})".format(indicator["metadata"]["name"], indicator["topic"]["name"]),
            styles["Heading3"],
        )
        indicator_heading.keepWithNext = True
        indicator_description = Paragraph(metadata["description"])
        indicator_description.keepWithNext = True
        # indicator_heading.keepWithNext = True
        # convert svg string to bytes file-like object
        svg_bytes = BytesIO(result["svg"].encode())
        # fix width/height ratio because OQT only produces squared SVGs
        indicator_traffic_light = generate_traffic_light(
            result["label"], radius=indicator_light_radius
        )
        indicator_img = svg2rlg(svg_bytes)
        indicator_img.scale(
            indicator_img_width / indicator_img.width,
            indicator_img_width / indicator_img.width,
        )
        indicator_img.width = indicator_img_width
        indicator_img.height = indicator_img_width
        indicator_result_description = Paragraph(result["description"])
        indicator_result_table = Table(
            [[indicator_traffic_light, indicator_img]],
            colWidths=[
                indicator_light_radius * 3 + indicator_table_margin,
                indicator_img_width + indicator_table_margin,
            ],
            style=[
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ],
        )
        indicator_components = [
            indicator_heading,
            indicator_description,
            indicator_result_table,
            indicator_result_description,
        ]
        components += indicator_components

    doc.build(components, onFirstPage=report_header, onLaterPages=report_header)
    bytes_output.seek(0)
    return bytes_output


def generate_traffic_light(label, radius=10):
    margin = radius / 2
    width = radius * 2 + margin * 2
    height = radius * 2 * 3 + margin * 4
    light_colors = [colors.gray] * 3
    match label:
        case "green":
            light_colors[0] = colors.green
        case "yellow":
            light_colors[1] = colors.yellow
        case "red":
            light_colors[2] = colors.red

    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=colors.lightgrey))
    x = radius + margin
    y = radius + margin
    for i, color in enumerate(light_colors):
        drawing.add(Circle(x, y, radius, fillColor=color))
        y += radius * 2 + margin

    return drawing


def report_header(canv, doc):
    canv.saveState()
    # logos
    logo_height = doc.topMargin / 2
    logo_draw_y = doc.height + doc.bottomMargin + doc.topMargin / 2 - logo_height / 2
    # right: heigit
    heigit_logo = svg2rlg(PDF_RESOURCES_PATH / "HeiGIT_Logo_base.svg")
    heigit_logo = resize_rlg_by_height(heigit_logo, logo_height)
    heigit_logo.drawOn(
        canv, doc.width + doc.leftMargin - heigit_logo.width, logo_draw_y
    )
    # left: OQT
    oqt_logo = svg2rlg(PDF_RESOURCES_PATH / "ohsome-quality-analyst_without_fonts.svg")
    oqt_logo = resize_rlg_by_height(oqt_logo, logo_height)
    logo_draw_y = (
        doc.height + doc.bottomMargin + doc.topMargin / 2 - oqt_logo.height / 2
    )
    oqt_logo.drawOn(canv, doc.leftMargin, logo_draw_y)
    canv.restoreState()
