"""
Functions to generate a webpage based on analyses' results
"""
from datetime import datetime
from typing import List, Dict, Tuple
from analyses.helpers import AnalysisResult, QualityLevel
from helper_modules.bbox_utils import Bbox
import json


def get_general_score(results: List[AnalysisResult]) -> QualityLevel:
    """
    Get the average level for given AnalysesResults, weighted by the analyses' importances.
    The level is determined after rounding the average score.

    :param results: Results of which the weighted average level should be calculated
    :return: Weighted average level
    """
    sum_scores = 0.0
    sum_weights = 0.0
    for result in results:
        sum_scores += result.level.value * result.importance
        sum_weights += result.importance
    avg_score = round(sum_scores / sum_weights)
    return QualityLevel(avg_score)


def get_result_texts(results: List[AnalysisResult]) \
        -> Tuple[Dict[QualityLevel, Dict[str, List[str]]], List[str]]:
    """
    Get result texts based on analyses results to be added to result pages.

    :param results: Results based on which the texts will be created
    :return: Messages for the different levels and importances, suggestions
    """
    suggestions = []
    messages: Dict[QualityLevel, Dict[str, List[str]]] = {
        QualityLevel.RED: {
            "very important": [],
            "important": [],
            "less important": []
        },
        QualityLevel.YELLOW: {
            "very important": [],
            "important": [],
            "less important": []
        },
        QualityLevel.GREEN: {
            "very important": [],
            "important": [],
            "less important": []
        }
    }
    for result in results:
        if result.suggestion != "":
            suggestions.append(result.suggestion)
        importance = "important"
        if result.importance < 1:
            importance = "less important"
        elif result.importance >= 1.5:
            importance = "very important"
        messages[result.level][importance].append(result.message)
    return messages, suggestions


def write_results_to_json(bbox: Bbox,
                          results: List[AnalysisResult],
                          pdf_link: str,
                          json_path: str) -> None:
    """
    Write the results of an analysis to a JSON file. The information from this file can be used
    to render a jinja template to present the results

    :param bbox: Bounding box for which the analyses where executed
    :param results: Results from the analyses
    :param pdf_link: Link to the PDF report for the results
    :param json_path: Path under which the JSON file should be stored
    """
    center_point = bbox.get_center_point()
    messages, suggestions = get_result_texts(results)
    results_for_template = {
        "PDF_LINK": pdf_link,
        "CREATION_DATE": datetime.today().date().strftime("%Y-%m-%d"),
        "RESTART_LINK": f"../../analyses?bbox={bbox.get_str(mode='comma')}",
        "MAP_COORDINATES": f"{center_point[0]},{center_point[1]}",
        "PLOYGON_COORDINATES": f"[[{bbox.lat1},{bbox.lon1}],[{bbox.lat2},{bbox.lon1}],[{bbox.lat2},"
                               f"{bbox.lon2}],[{bbox.lat1},{bbox.lon2}]]",
        "LEVEL": str(get_general_score(results).value),
        "MSG_LEVEL_RED": messages[QualityLevel.RED],
        "MSG_LEVEL_YELLOW": messages[QualityLevel.YELLOW],
        "MSG_LEVEL_GREEN": messages[QualityLevel.GREEN],
        "SUGGESTION_LIST": suggestions
    }
    with open(json_path, "w", encoding="utf8") as fw:
        json.dump(results_for_template, fw)
