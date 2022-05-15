"""
Execute the analyses scripts and create output files
"""
# pylint: disable=too-many-locals

import os

import requests
import json
import shutil
import random
from multiprocessing import Process, Queue
from typing import List, Dict, Union
from datetime import datetime

from analyses.helpers import add_one_day, get_result_path
from analyses.modules.analysis_completeness import CompletenessAnalysis
from analyses.modules.analysis_landmarks import LandmarkAnalysis
from analyses.modules.analysis_sources import SourcesAnalysis
from analyses.modules.analysis_currentness import CurrentnessAnalysis
from analyses.helpers import AnalysisResult
from analyses.html_gen import analyses_output_generator
from analyses.pdf_gen.pdf_gen import create_report
from helper_modules.bbox_utils import Bbox
from helper_modules.progress import update_progress
from constants import (STATUS_UPDATES_ANALYSES, OHSOME_API,
                       STATUS_ERROR_OHSOME_NOT_AVAILABLE,
                       TIMEOUT_OHSOME_METADATA)


def run_for_single_bbox(bbox: Bbox,
                        session_id: str,
                        output_path: str,
                        time_str_whole_time: str,
                        time_str_full_yearly: str,
                        time_str_current: str) -> None:
    """
    Run the analyses for a single given bounding box and generate HTML and PDF output files

    :param bbox: Bounding box to be analysed
    :param session_id: Name of the folder containing the files for the current session
    :param output_path: The location where the analyses' output files will be stored
    :param time_str_whole_time: The time parameter for the ohsome API, when the whole available
                                time span is requested
    :param time_str_full_yearly: The time parameter for the ohsome API, with the whole time span in
                                 yearly steps
    :param time_str_current: The time parameter for the ohsome API, with the last available date as
                             both min and max timestamp in yearly steps to obtain only data for this
                             date
    :return: Link to the status page for the analyses for the given bounding box
    """
    print(f"Running analyses for bbox: '{bbox}'")
    status_path = get_result_path(bbox, output_path)

    # Get Full-History-Data (used in multiple analyses):

    params = {"bboxes": str(bbox),
              "types": "node,way",
              "properties": "tags",
              "time": time_str_whole_time
              }

    result = json.loads(requests.get(OHSOME_API + "/elementsFullHistory/bbox", params).text)
    if "status" in result.keys() and result["status"] == 503:
        update_progress(result_path=status_path, update=STATUS_ERROR_OHSOME_NOT_AVAILABLE)
        return
    full_history_whole_time = result["features"]

    result_queue: Queue[Union[AnalysisResult, str]] = Queue()

    currentness_amenity = CurrentnessAnalysis(full_history_whole_time, session_id+"/", status_path,
                                              key="amenity")
    currentness_highway = CurrentnessAnalysis(full_history_whole_time, session_id+"/", status_path,
                                              key="highway")
    completeness_amenity = CompletenessAnalysis(bbox, time_str_full_yearly, session_id+"/",
                                                status_path, key="amenity", measure="density",
                                                measure_unit="features per km²")
    completeness_highway = CompletenessAnalysis(bbox, time_str_full_yearly, session_id+"/",
                                                status_path, key="highway", measure="length",
                                                measure_unit="m")
    landmark_density = LandmarkAnalysis(bbox, time_str_current, session_id+"/", status_path)
    sources = SourcesAnalysis(full_history_whole_time, session_id+"/", status_path)

    analyses = [currentness_amenity,
                currentness_highway,
                completeness_amenity,
                completeness_highway,
                landmark_density,
                sources,
                ]
    processes = []
    os.mkdir(session_id)  # Create directory where the plots are temporarily stored
    for analysis in analyses:
        processes.append(Process(target=analysis.run, args=(result_queue,)))
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    result_queue.put("END")
    results = []
    while (result := result_queue.get()) != "END":
        results.append(result)
    result_queue.close()
    update_progress(result_path=status_path, update=STATUS_UPDATES_ANALYSES["results"])
    export_path_html = get_result_path(bbox, output_path)
    export_path_pdf = export_path_html.replace(".html", ".pdf")
    create_report(results, session_id+"/", export_path_pdf, bbox)
    html_code = analyses_output_generator.results_to_html(results,
                                                          export_path_pdf.replace(output_path+"/",
                                                                                  ""), bbox)
    with open(export_path_html, "w", encoding="utf8") as fw:
        fw.write(html_code)
    shutil.rmtree(session_id + "/")  # Delete temporary folder for plots
    update_progress(result_path=status_path, update=export_path_html)


def run_preparations_and_analyses(bboxes_input: List[Bbox], output_path: str) -> None:
    """
    Get data from ohsome required by analyses for all bounding boxes and start the analyses for
    each bounding box afterwards

    :param bboxes_input: Bounding boxes to be analyzed
    :param output_path: The location where the analyses' output files will be saved
    """
    try:
        metadata = requests.get(OHSOME_API + "/metadata", timeout=TIMEOUT_OHSOME_METADATA).json()
    except requests.exceptions.ReadTimeout:
        print("ERROR Timeout: Ohsome API not available")
        for bbox in bboxes_input:
            status_path = get_result_path(bbox, output_path)
            update_progress(result_path=status_path, update=STATUS_ERROR_OHSOME_NOT_AVAILABLE)
        return

    # adjust str_time_full_yearly for the yearly analyses (pattern: yyyy-mm-dd,yyyy-mm-dd)
    time_str_full_yearly = metadata["extractRegion"]["temporalExtent"]["fromTimestamp"][0:10] + \
        "/" + metadata["extractRegion"]["temporalExtent"]["toTimestamp"][0:10] + "/P1Y"
    time_str_full_yearly = add_one_day(time_str_full_yearly)  # necessary in case the data available
    #                                                           does not start at 0:00 this day
    time_str_whole_time = time_str_full_yearly.replace("/P1Y", "").replace("/", ",")

    # Adjust time_str for the analysis of the current situation
    # Format: 2018-08-29/2018-08-29/P1Y
    time_str_current = time_str_whole_time[11:21] + "/" + time_str_whole_time[11:21] + "/P1Y"

    for bbox in bboxes_input:
        session_id = datetime.now().strftime("%d_%m_%Y_%H_%M_") + \
                     bbox.get_str(mode="minus") + \
                     str(random.randint(10000, 99000)) + "_"
        analyses_process = Process(target=run_for_single_bbox, args=(bbox, session_id,
                                                                     output_path,
                                                                     time_str_whole_time,
                                                                     time_str_full_yearly,
                                                                     time_str_current))
        analyses_process.start()


def run(bboxes_input: List[Bbox], output_path: str) -> Dict[str, str]:
    """
    Start the analyses for all given bboxes and get links to their status pages

    :param bboxes_input: Bounding boxes to be analyzed
    :param output_path: The location where the analyses' output files will be saved
    :return: Dict containing the bboxes as keys and the links to their output status pages as values
    """
    print(f"Running analyses for bboxes: '{bboxes_input}'...")
    # Request metadata to know which is the last covered timespan of a year
    Process(target=run_preparations_and_analyses, args=(bboxes_input, output_path)).start()
    results = dict()
    for bbox in bboxes_input:
        results[str(bbox)] = f"../status?mode=analyses&bbox={str(bbox)}"
        status_path = get_result_path(bbox, output_path)
        update_progress(result_path=status_path, update=STATUS_UPDATES_ANALYSES["start"])
    return results
