"""
Functions to generate a webpage based on analyses' results
"""
from typing import List, Dict
from analyses.helpers import AnalysisResult, QualityLevel
from helper_modules.bbox_utils import Bbox

TEMPLATE_PATH = "analyses/html_gen/template.html"


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


def results_to_html(results: List[AnalysisResult], pdf_link: str, bbox: Bbox) -> str:  # noqa: C901
    """
    Generate an HTML page presenting the given results.

    :param results: The results to be presented on the webpage
    :param pdf_link: Link to a PDF report to be included on the page
    :param bbox: Bounding box to be shown on the page
    :return: Relative path to the generated file
    """
    with open(TEMPLATE_PATH, "r", encoding="utf8") as fr:
        template_code = fr.read()
    template_code = template_code.replace("{{ PDF_LINK }}", pdf_link)
    center_point = bbox.get_center_point()
    template_code = template_code.replace("{{ MAP_COORDINATES }}",
                                          f"{center_point[0]},{center_point[1]}")

    polygon = f"[[{bbox.lat1},{bbox.lon1}],[{bbox.lat2},{bbox.lon1}],[{bbox.lat2},{bbox.lon2}]," \
              f"[{bbox.lat1},{bbox.lon2}]]"
    template_code = template_code.replace("{{ PLOYGON_COORDINATES }}", polygon)
    template_code = template_code.replace("{{ LEVEL }}", str(get_general_score(results).value))

    suggestions = ""
    messages_red = {
        "very important": "",
        "important": "",
        "less important": ""
    }
    messages_yellow = {
        "very important": "",
        "important": "",
        "less important": ""
    }
    messages_green = {
        "very important": "",
        "important": "",
        "less important": ""
    }
    for result in results:
        if result.suggestion != "":
            suggestions += f"<li>{result.suggestion}</li>"
        importance = "important"
        if result.importance < 1:
            importance = "less important"
        elif result.importance >= 1.5:
            importance = "very important"
        if result.level == QualityLevel.RED:
            messages_red[importance] += f"- {result.message}<br>"
        elif result.level == QualityLevel.YELLOW:
            messages_yellow[importance] += f"- {result.message}<br>"
        elif result.level == QualityLevel.GREEN:
            messages_green[importance] += f"- {result.message}<br>"

    def get_message_block(messages: Dict[str, str]) -> str:
        block = ""
        if len(messages["very important"]) > 0:
            block += f"<b>Very Important</b><br>{messages['very important']}"
        if len(messages["important"]) > 0:
            block += f"<b>Important</b><br>{messages['important']}"
        if len(messages["less important"]) > 0:
            block += f"<b>Less Important</b><br>{messages['less important']}"
        return block

    msg_red = get_message_block(messages_red)
    msg_yellow = get_message_block(messages_yellow)
    msg_green = get_message_block(messages_green)

    template_code = template_code.replace("{{ MSG_LEVEL_RED }}", msg_red)
    template_code = template_code.replace("{{ MSG_LEVEL_YELLOW }}", msg_yellow)
    template_code = template_code.replace("{{ MSG_LEVEL_GREEN }}", msg_green)
    if suggestions != "":
        suggestions = f"<ul>{suggestions}</ul>"
    template_code = template_code.replace("{{ SUGGESTION_LIST }}", suggestions)
    return template_code
