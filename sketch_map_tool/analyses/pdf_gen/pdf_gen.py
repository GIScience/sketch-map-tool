# coding=utf8
"""
Functions to create a pdf file containing information and plots regarding sketch map analyses'
results
"""
# pylint: disable=too-many-locals,invalid-name

import json
import os
from time import strftime
from typing import List, Optional, Tuple

from reportlab.lib import utils
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from sketch_map_tool.analyses.helpers import AnalysisResult, QualityLevel
from sketch_map_tool.analyses.html_gen.analyses_output_generator import (
    get_general_score,
)
from sketch_map_tool.helper_modules.bbox_utils import Bbox

RESOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res")


def add_result_page(
    result: AnalysisResult,
    canv: canvas.Canvas,
    title: str,
    infotext: str,
    move_info_up: int = 0,
    chapter_nr: Optional[int] = None,
) -> None:
    """
    Add a result page to the Sketch Map Fitness Report

    :param result: Result of one analysis
    :param canv: Reportlab Canvas to which the page should be added
    :param title: Title of the result page
    :param infotext: Information about the analysis (e.g. references, interpretation)
    :param move_info_up: How many pixels the info_box should be moved up and enlargened
                         (for long texts)
    :param chapter_nr: Position of the result page in the report, to be shown in the headline
    :return: None
    """
    CONTENTS_X = 50

    TITLE_FONT = "Times-Roman"
    TITLE_FONT_SIZE = 18
    TITLE_Y = 800

    HORIZONTAL_LINE_Y = 795

    TRAFFIC_LIGHT_Y = 660
    TRAFFIC_LIGHT_WIDTH = 104
    TRAFFIC_LIGHT_HEIGHT = 114

    TEXT_FONT = "Times-Roman"
    TEXT_FONT_SIZE = 11

    RESULT_TEXT_WIDTH = 400
    RESULT_TEXT_HEIGHT = 100
    RESULT_TEXT_X = CONTENTS_X + TRAFFIC_LIGHT_WIDTH + 6
    RESULT_TEXT_Y = TRAFFIC_LIGHT_Y + 104

    INFO_BOX_Y = 35
    INFO_BOX_X = 75
    INFO_BOX_WIDTH = 450
    INFO_BOX_HEIGHT = 250 + move_info_up
    INFO_BOX_RGB = (0, 110.0 / 256, 214.0 / 256)
    INFO_BOX_MARGIN = 4.0

    if chapter_nr is not None:
        title = f"{chapter_nr}. {title}"
    canv.setFont(TITLE_FONT, TITLE_FONT_SIZE)
    canv.drawString(CONTENTS_X, TITLE_Y, title)
    canv.line(0, HORIZONTAL_LINE_Y, 1000, HORIZONTAL_LINE_Y)

    # Here we have one suggestion per analyses, not all recommendations together:
    text = "<b>Result:</b><br/>" + result.message.replace(
        "recommendations", "the suggestion"
    )

    if result.suggestion != "":
        text += "<br/><br/><b>Suggestion:</b><br/>" + result.suggestion
    image = os.path.join(RESOURCE_PATH, f"light_{result.level.value}.jpg")
    canv.drawImage(
        image,
        CONTENTS_X,
        TRAFFIC_LIGHT_Y,
        TRAFFIC_LIGHT_WIDTH,
        TRAFFIC_LIGHT_HEIGHT,
        showBoundary=False,
    )
    canv.setFont(TEXT_FONT, TEXT_FONT_SIZE)
    style = ParagraphStyle(name="_", fontSize=TEXT_FONT_SIZE, fontName=TEXT_FONT)
    text_par = Paragraph(text, style=style)
    _, h = text_par.wrapOn(canv, RESULT_TEXT_WIDTH, RESULT_TEXT_HEIGHT)
    text_par.drawOn(canv, RESULT_TEXT_X, RESULT_TEXT_Y - h)
    canv.setStrokeColorRGB(*INFO_BOX_RGB)
    canv.setLineWidth(INFO_BOX_MARGIN)
    canv.roundRect(
        INFO_BOX_X, INFO_BOX_Y, INFO_BOX_WIDTH, INFO_BOX_HEIGHT, 4, stroke=1, fill=0
    )
    info = Paragraph(
        "<b>Information about this analysis:</b><br/>" + infotext, style=style
    )
    _, h = info.wrapOn(canv, INFO_BOX_WIDTH - 50, INFO_BOX_HEIGHT - 25)
    info.drawOn(canv, INFO_BOX_X + 25, INFO_BOX_Y + 250 - h + move_info_up)


def add_overview_page(results: List[AnalysisResult], canv: canvas.Canvas) -> None:
    """
    Add an overview page to the Sketch Map Fitness Report.
    The general score as well as all suggestions are presented

    :param results: Results from all analyses
    :param canv: Reportlab Canvas to which the page should be added
    """
    CONTENTS_X = 50

    TITLE_FONT = "Times-Roman"
    TITLE_FONT_SIZE = 18
    TITLE_Y = 750

    RESULT_STRING_FONT = "Times-Roman"
    RESULT_STRING_FONT_HIGHLIGHT = "Times-Bold"
    RESULT_STRING_FONT_SIZE = 14
    RESULT_STRING_1_Y = 700
    RESULT_STRING_2_Y = 560

    TRAFFIC_LIGHT_Y = 580
    TRAFFIC_LIGHT_WIDTH = 104
    TRAFFIC_LIGHT_HEIGHT = 114

    SUGGESTION_HEADLINE_Y = 520
    SUGGESTIONS_FONT = "Times-Roman"
    SUGGESTIONS_FONT_SIZE = 12
    SUGGESTIONS_TEXT_WIDTH = 175 * mm
    SUGGESTIONS_TEXT_HEIGHT = 200 * mm
    SUGGESTIONS_Y = 494
    SUGGESTIONS_MARGIN_RGB = (0, 0, 0)
    SUGGESTIONS_MARGIN = 2.0

    canv.setFont(TITLE_FONT, TITLE_FONT_SIZE)
    canv.drawString(CONTENTS_X, TITLE_Y, "1. Overview")
    canv.line(0, TITLE_Y - 5, 1000, TITLE_Y - 5)
    general_score = get_general_score(results)
    canv.setFont(RESULT_STRING_FONT, RESULT_STRING_FONT_SIZE)
    canv.drawString(
        CONTENTS_X, RESULT_STRING_1_Y, "The general Sketch Map Fitness Score is: "
    )
    image = os.path.join(RESOURCE_PATH, f"light_{general_score.value}.jpg")
    canv.drawImage(
        image,
        CONTENTS_X,
        TRAFFIC_LIGHT_Y,
        TRAFFIC_LIGHT_WIDTH,
        TRAFFIC_LIGHT_HEIGHT,
        showBoundary=False,
    )
    string = "indicating an estimated "
    canv.drawString(CONTENTS_X, RESULT_STRING_2_Y, string)
    str_width = stringWidth(string, RESULT_STRING_FONT, RESULT_STRING_FONT_SIZE)
    if general_score == QualityLevel.RED:
        score_string = "low"
    elif general_score == QualityLevel.YELLOW:
        score_string = "mediocre"
    elif general_score == QualityLevel.GREEN:
        score_string = "high"
    else:
        raise ValueError(f"Invalid Quality Level '{general_score}'")
    canv.setFont(RESULT_STRING_FONT_HIGHLIGHT, RESULT_STRING_FONT_SIZE)
    canv.drawString(
        CONTENTS_X + str_width, RESULT_STRING_2_Y, score_string + " fitness"
    )
    str_width_2 = stringWidth(
        score_string + " fitness", RESULT_STRING_FONT_HIGHLIGHT, RESULT_STRING_FONT_SIZE
    )
    canv.setFont(RESULT_STRING_FONT, RESULT_STRING_FONT_SIZE)
    canv.drawString(
        CONTENTS_X + str_width + str_width_2,
        RESULT_STRING_2_Y,
        " for usage in sketch maps.",
    )
    canv.drawString(
        CONTENTS_X,
        SUGGESTION_HEADLINE_Y,
        "You might want to consider the following suggestions:",
    )
    suggestions = ""
    for result in results:
        if result.suggestion != "":
            suggestions += f"• {result.suggestion}<br/><br/>"

    style = ParagraphStyle(
        name="_", fontSize=SUGGESTIONS_FONT_SIZE, fontName=SUGGESTIONS_FONT
    )
    text_par = Paragraph(suggestions, style=style)
    w, h = text_par.wrapOn(canv, SUGGESTIONS_TEXT_WIDTH, SUGGESTIONS_TEXT_HEIGHT)
    # Necessary to have the lines belonging to a bullet point indented:
    lines = text_par.blPara.lines
    for line in lines:
        if len(line.words[0].text) == 0:
            continue
        if line.words[0].text[0] == "•":
            continue
        line.words[0].text = "   " + line.words[0].text
    sugg_y = SUGGESTIONS_Y - h
    text_par.drawOn(canv, CONTENTS_X, sugg_y)
    canv.setStrokeColorRGB(*SUGGESTIONS_MARGIN_RGB)
    canv.setLineWidth(SUGGESTIONS_MARGIN)
    canv.roundRect(CONTENTS_X - 5, sugg_y - 5, w + 15, h + 10, 4, stroke=1, fill=0)


def add_contents_page(canv: canvas.Canvas, contents: List[Tuple[str, int]]) -> None:
    """
    Add a table of contents page to the Sketch Map Fitness Report

    :param canv: Reportlab Canvas to which the page should be added
    :param contents: [(page_title, page_nr), ...]
    """
    TITLE_FONT = "Times-Roman"
    TITLE_FONT_SIZE = 18
    TITLE_Y = 750
    CONTENTS_X = 50

    ITEMS_FILLER = "."
    ITEMS_FILLER_LENGTH = 150
    ITEMS_FONT = "Times-Roman"
    ITEMS_FONT_SIZE = 12
    ITEMS_PARAGRAPH_WIDTH = 175 * mm
    ITEMS_PARAGRAPH_HEIGHT = 200 * mm
    ITEMS_PARAGRAPH_Y = 694

    canv.setFont(TITLE_FONT, TITLE_FONT_SIZE)
    canv.drawString(CONTENTS_X, TITLE_Y, "Contents")
    canv.line(0, TITLE_Y - 5, 1000, TITLE_Y - 5)
    contents_str = ""
    chapter_count = 1
    fill_char_width = stringWidth(ITEMS_FILLER, ITEMS_FONT, ITEMS_FONT_SIZE)
    for content in contents:
        first_part = f"{chapter_count}. {content[0]}"
        str_width = stringWidth(first_part, ITEMS_FONT, ITEMS_FONT_SIZE)
        nr_fill_chars = ITEMS_FILLER_LENGTH - round(str_width / fill_char_width)
        contents_str += (
            f"{first_part} {str(content[1]).rjust(nr_fill_chars, ITEMS_FILLER)}".replace(
                " ", "&nbsp;"
            )
            + "<br/><br/>"
        )
        chapter_count += 1
    style = ParagraphStyle(name="_", fontSize=ITEMS_FONT_SIZE, fontName=ITEMS_FONT)
    contents_par = Paragraph(contents_str, style=style)
    _, h = contents_par.wrapOn(
        canv, ITEMS_PARAGRAPH_WIDTH, ITEMS_PARAGRAPH_HEIGHT
    )  # pylint: disable=unused-variable,line-too-long  # noqa
    contents_par.drawOn(canv, CONTENTS_X, ITEMS_PARAGRAPH_Y - h)


def add_page_nr(canv: canvas.Canvas, nr: int) -> None:
    """
    Add the page number to the active page of the given canvas

    :param canv: Reportlab Canvas to which the page number should be added
    :param nr: Number of the current page to be added
    """
    canv.setFont("Times-Roman", 12)
    canv.drawString(190 * mm, 25, str(nr))


def add_plot(
    canv: canvas.Canvas,
    plot_path: str,
    description: str,
    plot_width: int,
    plot_y: int = 310,
) -> None:
    """
    Add a plot image to an analysis result page of the Sketch Map Fitness Report

    :param canv: Reportlab Canvas to which the plot should be added
    :param plot_path: Path to the image file showing the plot
    :param description: Description to be printed beneath the plot
    :param plot_width: Width (px) in which the plot will be added to the page
    :param plot_y: Y coordinate of the plot
    """
    if not os.path.isfile(plot_path):
        return
    page_width = 210 * mm
    img = utils.ImageReader(plot_path)
    width, height = img.getSize()
    ratio = height / width
    canv.drawImage(
        plot_path,
        page_width / 2 - plot_width / 2,
        plot_y,
        plot_width,
        plot_width * ratio,
        showBoundary=True,
    )
    canv.setFont("Times-Roman", 9)
    t = canv.beginText()
    t.setTextOrigin(page_width / 2 - plot_width / 2, plot_y - 10)
    t.textLines(description)
    canv.drawText(t)


def create_title(canv: canvas.Canvas, bbox: Bbox) -> None:
    """
    Add a title page to the Sketch Map Fitness Report

    :param canv: Reportlab Canvas to which the page should be added
    :param bbox: Bounding box of the inspected area
    :return: None
    """
    CONTENTS_X = 75
    FONT = "Times-Roman"

    TITLE_SIZE = 28
    TITLE_Y = 700

    LINK_SIZE = 12
    LINK_Y = 650

    NOTES_SIZE = 11
    NOTES_WIDTH = 500
    NOTES_Y = 75

    INFO_SIZE = 11
    BBOX_INFO_Y = 620
    META_INFO_Y = 50

    MAP_Y = 230
    MAP_WIDTH = 400
    MAP_HEIGHT = 310

    canv.setFont(FONT, TITLE_SIZE)
    canv.drawString(CONTENTS_X, TITLE_Y, "Sketch Map Fitness Report")
    style = ParagraphStyle(name="_", fontSize=LINK_SIZE, fontName=FONT)
    link_information = Paragraph(
        "Created using the <link href='https://www.geog.uni-heidelberg.de/"
        "gis/sketchmaptool.html' color='blue'><u>Sketch Map Tool</u>"
        "</link>",
        style=style,
    )
    style = ParagraphStyle(name="_", fontSize=NOTES_SIZE, fontName=FONT)
    license_information = Paragraph(
        "This tool accesses OpenStreetMap data, which is partly "
        "aggregated, via the <link href='https://www.ohsome.org' "
        "color='blue'><u>ohsome API</u></link> by the <link "
        "href='https://www.heigit.org/' color='blue'><u>Heidelberg "
        "Institute for Geoinformation Technology (HeiGIT)</u></link>. "
        "The data and statistics are based on data by<br/><link "
        "href='https://www.openstreetmap.org/copyright' color='blue'>"
        "<u>© OpenStreetMap contributors</u></link>. ohsome uses a "
        "database that contains <link href="
        "'https://www.opendatacommons.org/licenses/odbl/1-0/index.html'"
        " color='blue'><u>ODbL 1.0</u></link> licensed <link href="
        "'https://planet.osm.org/planet/full-history/' color='blue'>"
        "<u>OSM data</u></link> and <link href='"
        "https://www.creativecommons.org/licenses/by-sa/2.0/' color="
        "'blue'><u>CC-BY-SA 2.0</u></link> licensed <link href="
        "'https://planet.osm.org/cc-by-sa/' color='blue'><u>OSM data"
        "</u></link>.",
        style=style,
    )
    link_information.wrapOn(canv, 500, 100)
    link_information.drawOn(canv, CONTENTS_X, LINK_Y)
    license_information.wrapOn(canv, NOTES_WIDTH, 100)
    license_information.drawOn(canv, CONTENTS_X, NOTES_Y)

    canv.drawImage(
        os.path.join(RESOURCE_PATH, "world_map.jpg"),
        CONTENTS_X,
        MAP_Y,
        MAP_WIDTH,
        MAP_HEIGHT,
        showBoundary=True,
    )

    canv.setFont(FONT, INFO_SIZE)
    canv.drawString(
        CONTENTS_X, BBOX_INFO_Y, f"Study region: {bbox.get_str(mode='comma')}"
    )
    canv.drawString(
        CONTENTS_X, META_INFO_Y, "PDF created: " + str(strftime("%Y-%m-%d %H:%M:%S"))
    )


def create_report(
    results: List[AnalysisResult], plots_path: str, output_path: str, bbox: Bbox
) -> None:
    """
    Generate a PDF file containing information and plots from Analyses' results

    :param results: Analyses' results to be presented in the report
    :param plots_path: Path to the directory containing the plots to be used in the PDF report
    :param output_path: The path under which the PDF file should be stored
    :param bbox: The bounding box for which the results are
    """
    content_list = [("Overview", 3)]  # page 1 = Title, p. 2 = Table of contents
    page_count = 4
    for result in results:
        content_list.append((result.title_for_report, page_count))
        page_count += 1

    c = canvas.Canvas(output_path.split("/")[-1], pagesize=A4)
    create_title(c, bbox)
    c.showPage()
    add_contents_page(c, content_list)
    c.showPage()
    page_count = 3
    fig_counter = 1
    add_overview_page(results, c)
    add_page_nr(c, page_count)
    page_count += 1
    c.showPage()
    chapter_count = 2
    with open(
        os.path.join(RESOURCE_PATH, "info_texts.json"), encoding="utf-8"
    ) as infos:
        info_dict = json.loads(infos.read())

    for result in results:
        move_info_up = 0
        plot_y = 310
        plot_width = 390

        if "Landmark" in result.title_for_report:
            plot_label = "Distribution of landmark categories"
            info_text = info_dict["density"]
        elif (
            "Currentness" in result.title_for_report
            and "amenity" in result.title_for_report
        ):
            plot_label = "Currentness of amenity data"
            info_text = info_dict["le-am"]
        elif (
            "Currentness" in result.title_for_report
            and "highway" in result.title_for_report
        ):
            plot_label = "Currentness of street data"
            info_text = info_dict["le-hw"]
        elif (
            "Saturation" in result.title_for_report
            and "amenity" in result.title_for_report
        ):
            plot_label = "Development of amenity feature mapping"
            info_text = info_dict["sat-am"]
            plot_width = 250
            plot_y = 410
            move_info_up = 100
        elif (
            "Saturation" in result.title_for_report
            and "highway" in result.title_for_report
        ):
            plot_label = "Development of highway feature mapping"
            info_text = info_dict["sat-hw"]
            plot_width = 250
            plot_y = 410
            move_info_up = 100
        elif "Source" in result.title_for_report:
            plot_label = "Shares of specified sources"
            info_text = info_dict["sources"]
        else:
            plot_label = ""
            info_text = ""
            plot_width = 0
            plot_y = 0

        if result.corresponding_plot_name != "":
            add_plot(
                c,
                plots_path + result.corresponding_plot_name,
                f"Fig. {fig_counter} {plot_label}",
                plot_width,
                plot_y,
            )
            fig_counter += 1
        add_result_page(
            result,
            c,
            result.title_for_report,
            info_text,
            chapter_nr=chapter_count,
            move_info_up=move_info_up,
        )
        add_page_nr(c, page_count)
        page_count += 1
        chapter_count += 1
        c.showPage()

    current_dir = os.getcwd()
    os.chdir(os.sep.join(output_path.split("/")[:-1]))
    c.save()
    os.chdir(current_dir)
