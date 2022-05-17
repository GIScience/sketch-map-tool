"""
Helper functions for the analyses of OSM data and the handling of their result files
"""
from typing import Dict, Tuple, Union
from enum import Enum

from helper_modules.bbox_utils import Bbox


def add_one_day(time_str: str) -> str:
    """
    Roughly adds one day to the start time of a given time string
    When the new date would be the 29th, the month is increased,
    no matter which month it acutally was.
    Therefore, this is only meant to be used, when such inaccuracies
    do not pose a problem.

    :param time_str: Format yyyy-mm-dd/yyyy-mm-dd/XXX
    :return: time_str with the start time increased by one day

    >>> time_str = "2007-10-28/2020-06-29/P1Y"
    >>> add_one_day(time_str)
    '2007-11-01/2020-06-29/P1Y'
    >>> time_str = "2007-11-01/2020-06-29/P1Y"
    >>> add_one_day(time_str)
    '2007-11-02/2020-06-29/P1Y'
    >>> time_str = "2007-12-28/2020-06-29/P1Y"
    >>> add_one_day(time_str)
    '2008-01-01/2020-06-29/P1Y'
    """
    if int(time_str[8:10])+1 < 29:
        return time_str[0:8] + str(int(time_str[8:10])+1).zfill(2) + time_str[10:]
    if int(time_str[5:7])+1 < 13:
        return time_str[0:5] + str(int(time_str[5:7])+1).zfill(2) + "-01" + time_str[10:]
    return str(int(time_str[0:4])+1) + "-01-01" + time_str[10:]


def get_result_path(bbox: Bbox, output_path: str) -> str:
    """
    Get the path under which the result file will be stored

    :param bbox: Bounding box of which the result file will be generated
    :param output_path: The location where the analyses' output files will be saved
    :return: Path to the HTML file which will be generated when the analyses are carried out
             for the given bbox
    """
    return f"{output_path}/{bbox.get_str(mode='minus')}_output.html"


class QualityLevel(Enum):
    """
    Sketch Map Fitness quality level in the traffic light system (RED meaning "potential problems",
    YELLOW meaning "mediocre fitness", GREEN meaning "good fitness")
    """
    RED = 0
    YELLOW = 1
    GREEN = 2


class AnalysisResult:
    """
    The results of an OSM quality analysis
    """
    def __init__(self, message: str, level: QualityLevel, importance: int = 1,
                 suggestion: str = "", corresponding_plot_name: str = "",
                 title_for_report: str = ""):
        """
        :param message: Result message containing relevant values to be presented to the user
        :param level: The quality level indicated by the results
        :param importance: Weighting of these results when calculating a general fitness score
        :param suggestion: Consequences the user should draw from these results
        :param corresponding_plot_name: Filename of the plot corresponding to this result
        :param title_for_report: Title of the analyses to be used in reports
        """
        self.message = message
        self.level = level
        self.importance = importance
        self.suggestion = suggestion
        self.corresponding_plot_name = corresponding_plot_name
        self.title_for_report = title_for_report

    def to_dict(self) -> Dict[str, Union[str, int, QualityLevel]]:
        """
        Get a dict containing all attributes of this AnalysisResult object

        :return: dict containing all attributes
        """
        return {
            "message": self.message,
            "level": self.level,
            "importance": self.importance,
            "suggestion": self.suggestion
        }

    def to_tuple(self) -> Tuple[int, int, str, str]:
        """
        Get a Tuple containing all attributes of this AnalysisResult object

        :return: Tuple  level, importance, message, suggestion
        """
        return self.level.value, self.importance, self.message, self.suggestion
