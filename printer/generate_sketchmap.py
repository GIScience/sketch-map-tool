"""
Generate sketch map PDFs
"""

import os
import traceback
from datetime import datetime
from typing import Tuple, Optional

from helper_modules.bbox_utils import Bbox
from helper_modules.progress import update_progress, has_failed
from .modules.get_map import get_map_image
from .modules import generate_pdf
from .modules.paper_formats.paper_formats import PaperFormat, A4
from constants import (STATUS_UPDATES_GENERATION, STATUS_ERROR_GENERATION_GET_MAP)


def generate(paper_format: PaperFormat,
             bbox: Bbox,
             resolution: Tuple[int, int],
             output_path: str) -> str:
    """
    Generate a PDF sketch map for a study region given with the 'bbox' parameter in the given paper
    format.

    :param paper_format: Format of the generated sketch map PDF
    :param bbox: Bounding box for which the sketch map is created
    :param resolution: Resolution in pixels of the printed map image (width, height)
    :param output_path: Path under which the created sketch map is stored
    :return: Link to the generated sketch map PDF file    """
    date = str(datetime.date(datetime.now()))
    directory = f"{output_path}/{bbox.get_str(mode='minus')}__{date}{paper_format}"
    pdf_path = f"{directory}/{date}__{bbox.get_str(mode='minus')}__{paper_format}.pdf"
    if not os.path.exists(directory):
        os.makedirs(directory)
    elif os.path.exists(pdf_path) and not has_failed(pdf_path):  # PDF has already been generated
        return pdf_path
    try:
        map_image = get_map_image(bbox, resolution[1], resolution[0])
    except Exception:  # ToDo: Specify possible exceptions
        traceback.print_exc()
        update_progress(result_path=pdf_path, update=STATUS_ERROR_GENERATION_GET_MAP)
        return "ERROR"

    update_progress(result_path=pdf_path, update=STATUS_UPDATES_GENERATION["create_pdf"])
    generate_pdf.generate_pdf(directory, map_image, bbox, date, paper_format)
    update_progress(result_path=pdf_path, update=STATUS_UPDATES_GENERATION["completed"])
    update_progress(result_path=pdf_path, update=pdf_path)
    return pdf_path


if __name__ == "__main__":
    generate_pdf.RESOURCE_PATH = "modules/resources/"
    print(generate(A4, Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373"),
                   (500, 500), "./"))
