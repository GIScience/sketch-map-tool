"""
Generate sketch map PDFs
"""

import os
from datetime import datetime
from typing import Tuple

from sketch_map_tool.constants import GENERATION_OUTPUT_LINK, STATUS_UPDATES_GENERATION
from sketch_map_tool.helper_modules.bbox_utils import Bbox
from sketch_map_tool.helper_modules.progress import has_failed, update_progress
from sketch_map_tool.printer.modules import generate_pdf
from sketch_map_tool.printer.modules.get_map import get_map_image
from sketch_map_tool.printer.modules.paper_formats.paper_formats import A4, PaperFormat


def generate(
    paper_format: PaperFormat, bbox: Bbox, resolution: Tuple[int, int], output_path: str
) -> str:
    """
    Generate a PDF sketch map for a study region given with the 'bbox' parameter in the given paper
    format.

    :param paper_format: Format of the generated sketch map PDF
    :param bbox: Bounding box for which the sketch map is created
    :param resolution: Resolution in pixels of the printed map image (width, height)
    :param output_path: Path under which the created sketch map is stored
    :return: Path to the generated sketch map PDF file"""
    date = str(datetime.date(datetime.now()))
    pdf_path = get_result_path(paper_format, bbox, output_path, date)
    pdf_link = get_result_path(paper_format, bbox, GENERATION_OUTPUT_LINK, date)
    if os.path.exists(pdf_path) and not has_failed(
        pdf_path
    ):  # PDF has already been generated
        return pdf_path
    update_progress(result_path=pdf_path, update=STATUS_UPDATES_GENERATION["load_map"])
    map_image = get_map_image(bbox, resolution[1], resolution[0])
    update_progress(
        result_path=pdf_path, update=STATUS_UPDATES_GENERATION["create_pdf"]
    )
    generate_pdf.generate_pdf(pdf_path, map_image, bbox, date, paper_format)
    update_progress(result_path=pdf_path, update=STATUS_UPDATES_GENERATION["completed"])
    update_progress(result_path=pdf_path, update=pdf_link)
    return pdf_path


def get_result_path(
    paper_format: PaperFormat,
    bbox: Bbox,
    output_path: str,
    date: str = str(datetime.date(datetime.now())),
) -> str:
    """
    Get the result path for a sketch map generation process with the given
    parameters.

    :param paper_format: Paper format of the generated PDF
    :param bbox: Bounding box for which the sketch map is being created
    :param output_path: Path under which the created sketch map is stored
    :param date: The date of the PDF creation
    """
    return f"{output_path}/{date}__{bbox.get_str(mode='minus')}__{paper_format}.pdf"


def get_status_link(
    paper_format: PaperFormat,
    bbox: Bbox,
    date: str = str(datetime.date(datetime.now())),
) -> str:
    """
    Get a relative link to the status page for a sketch map generation process with the given
    parameters.

    :param paper_format: Paper format of the generated PDF
    :param bbox: Bounding box for which the sketch map is being created
    :param date: The date of the PDF creation
    """
    return f"../status?mode=generation&format={paper_format}&bbox={bbox}&d={date}"


if __name__ == "__main__":
    generate_pdf.RESOURCE_PATH = "modules/resources/"
    print(
        generate(
            A4,
            Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373"),
            (500, 500),
            "./",
        )
    )
