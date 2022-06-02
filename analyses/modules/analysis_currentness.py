"""
- Idea: Check how up-to-date features are and return the average time since the last edit of
        features with relevant tags (highway, amenity).
- Value: Average time since last edit of the features
- Reference: ''A comprehensive framework for intrinsic OpenStreetMap quality analysis.'' (Barron,
             Neis, & Zipf, 2014, https://onlinelibrary.wiley.com/doi/full/10.1111/tgis.12073)
"""
# pylint: disable=duplicate-code
import multiprocessing  # noqa  # pylint: disable=unused-import
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import floor
from analyses.helpers import AnalysisResult, QualityLevel
from analyses.modules.analysis_base import Analysis

from constants import STATUS_UPDATES_ANALYSES
from helper_modules.progress import update_progress


class CurrentnessAnalysis(Analysis):
    """
    Check how up-to-date features are by inspecting the average time since their last edit
    """
    importance = 1
    threshold_yellow = 4  # years
    threshold_red = 8  # years

    def __init__(self,
                 ohsome_export: List[Dict[str, Any]],
                 plot_location: str = "./",
                 status_file_path: str = "analyses.status",
                 key: Optional[str] = None):
        """
        :param ohsome_export: Full history OSM data from ohsome in form of a list of features with
                              their attributes
        :param plot_location: Path to the directory in which the plots are stored
        :param status_file_path: Path to the file the status updates should be written to
        :param key: If given, only features with this key are analyzed (e.g. highway)
        """
        self.data = ohsome_export
        self.key = key
        self._plot_location = plot_location
        self._status_file_path = status_file_path
        self.title = "Currentness Analysis"
        if key is not None:
            self.title += f" for '{key}' features"
            self.plot_name = f"_plot_last_edit_{key}.png"
        else:
            self.plot_name = "_plot_last_edit_general.png"

    @property
    def plot_location(self) -> str:
        return self._plot_location

    @property
    def status_file_path(self) -> str:
        return self._status_file_path

    def plot_results(self, df: pd.DataFrame) -> None:
        """
        Create a pie plot showing the shares of features in a df with their value for the column
        'TimeDelta' in different ranges

        :param df: Dataframe containing a column 'TimeDelta' indicating how old the features are
        """
        if "TimeDelta" not in df.keys():
            raise ValueError("'df' must contain a column 'TimeDelta' indicating the features' age")
        # Categorize features by their age in years
        nr_1y = len(df[df["TimeDelta"] <= 365.25])
        nr_2y = len(df[(df["TimeDelta"] > 365.25) & (df["TimeDelta"] <= 2 * 365.25)])
        nr_3y = len(df[(df["TimeDelta"] > 2 * 365.25) & (df["TimeDelta"] <= 3 * 365.25)])
        nr_4y = len(df[(df["TimeDelta"] > 3 * 365.25) & (df["TimeDelta"] <= 4 * 365.25)])
        nr_5y = len(df[(df["TimeDelta"] > 4 * 365.25) & (df["TimeDelta"] <= 5 * 365.25)])
        nr_5plus = len(df[df["TimeDelta"] > 5 * 365.25])

        values = [nr_1y, nr_2y, nr_3y, nr_4y, nr_5y, nr_5plus]
        legend = ["Edited in the last year", "Edited in the last two years",
                  "Edited in the last three years", "Edited in the last four years",
                  "Edited in the last five years", "Not edited in the last five years"]
        fig = plt.figure(figsize=(7, 7))
        plot = fig.add_subplot(111)
        plot.pie(values, autopct="%.2f%%", textprops={"color": "w", "fontsize": "xx-large"})
        lgd = plot.legend(legend, loc="lower right", bbox_to_anchor=(.8, 0, 0.5, 1),
                          fontsize=12)
        if self.key is not None:
            key = " " + self.key + " "
        else:
            key = " "
        plot.set_title(f"Currentness of{key}data in the bbox:")
        fig.savefig(self.plot_location + self.plot_name, bbox_inches="tight",
                    bbox_extra_artists=(lgd,))

    def run(self, queue: Optional["multiprocessing.Queue[AnalysisResult]"] = None) \
            -> AnalysisResult:  # noqa: C901
        """
        Inspect the currentness of OSM features

        :param queue: Queue to which the result is appended
        :return: Result object

        >>> features = [
        ... {
        ... "type" : "Feature",
        ... "geometry" : {},
        ... "properties" : {
        ... "@osmId" : "way/399317554",
        ... "@validFrom" : "2016-02-22T21:12:04Z",
        ... "@validTo" : "2016-02-28T21:50:18Z", # Maximum validTo, time since last edit = 6d
        ... "addr:housenumber" : "cll 24 # 23-56",
        ... "building" : "residential",
        ... "building:material" : "brick"
        ... }
        ... }, {
        ... "type" : "Feature",
        ... "geometry" : {},
        ... "properties" : {
        ... "@osmId" : "way/135681294",
        ... "@validFrom" : "2016-01-01T00:00:00Z",
        ... "@validTo" : "2016-02-09T19:58:33Z", # Time shorter than maximum validTo -> deleted -> not considered  # pylint: disable=line-too-long  # noqa
        ... "building" : "contact_line"
        ... }
        ... }, {
        ... "type" : "Feature",
        ... "geometry" : {},
        ... "properties" : {
        ... "@osmId" : "way/135681294",
        ... "@validFrom" : "2016-02-20T21:12:04Z",
        ... "@validTo" : "2016-02-28T21:50:18Z", # 8d -> average=(6+8)/2=7
        ... "building" : "contact_line"}}]
        >>> result = CurrentnessAnalysis(features).run()
        >>> result.message[:76]
        'The average feature has been edited in the last 4 years, indicating that the'
        >>> result.message[76:]
        ' data are not outdated. The average last edit was 0 years, 0 months and 7 days ago'
        """
        if self.key is not None:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["last_edit_s"] + f" for key: {self.key}")
            df = pd.DataFrame([i["properties"] for i in self.data
                               if self.key in i["properties"].keys()])
        else:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["last_edit_s"])
            df = pd.DataFrame([i["properties"] for i in self.data])
        df["@validFrom"].dropna(inplace=True)  # All features need to have a validFrom attribute to
        #                                        calculate their age (validTo - validFrom)

        if len(df.index) == 0:
            if self.key is None:
                message = "No features for last-edit analysis found"
            else:
                message = f"No features with key {self.key} for last-edit analysis found"
            result = AnalysisResult(message, QualityLevel.YELLOW, 0, title_for_report=self.title)
            if queue is not None:
                queue.put(result)
            return result

        # Only keep most current version of features that have been edited
        df.drop_duplicates(subset=["@osmId"], keep="last", inplace=True)

        # Remove '@' from column names for easier access with the dot syntax
        df.rename({"@validTo": "validTo", "@validFrom": "validFrom"}, axis=1, inplace=True)

        # Transform validTo and validFrom values into datetime objects
        df["validTo"] = df.apply(lambda row: np.datetime64(str(row.validTo).replace("Z", "")),
                                 axis=1)
        df["validFrom"] = df.apply(lambda row: np.datetime64(str(row.validFrom).replace("Z", "")),
                                   axis=1)
        max_validto = max(df["validTo"])

        # Remove all features that have been deleted (are not valid at the time of the analysis
        # anymore) from the dataframe
        df.drop(df[df.validTo < max_validto].index, inplace=True)

        if len(df.index) == 0:
            if self.key is None:
                message = "No features for last-edit analysis found"
            else:
                message = f"No features with key {self.key} for last-edit analysis found"
            result = AnalysisResult(message, QualityLevel.YELLOW, 0, title_for_report=self.title)
            if queue is not None:
                queue.put(result)
            return result

        # Add column containing the features' ages in days
        df["TimeDelta"] = df.apply(lambda row:
                                   floor((row.validTo - row.validFrom) / np.timedelta64(1, "D")),
                                   axis=1)

        # Calculate the average values
        average_passed_days = df["TimeDelta"].mean()
        passed_years = average_passed_days // 365.25
        remainder = average_passed_days % 365.25
        passed_months = remainder // 30.4
        passed_days = floor(remainder % 30.4)
        if self.key is not None:
            key = " " + self.key + " "
        else:
            key = " "
        suggestion = ""

        if passed_years >= self.threshold_red:
            level = QualityLevel.RED
            message = "The average" + key + "feature has not been updated in the last " + \
                      str(self.threshold_red) + " years, so the data could be outdated."
            suggestion = "Be aware, that the" + key + "data could be outdated."
        elif passed_years >= self.threshold_yellow:
            level = QualityLevel.YELLOW
            message = "The average" + key + "feature has not been updated in the last " + \
                      str(self.threshold_yellow) + " years, so the data could be outdated."
        else:
            message = "The average" + key + "feature has been edited in the last " + \
                      str(self.threshold_yellow) + " years, indicating that the data are not " \
                                                   "outdated."
            level = QualityLevel.GREEN

        info_string = f"{int(passed_years)} years, {int(passed_months)} months and " \
                      f"{int(passed_days)} days"
        if passed_years == 1:
            info_string = info_string.replace("years", "year")
        if passed_months == 1:
            info_string = info_string.replace("months", "month")
        if passed_days == 1:
            info_string = info_string.replace("days", "day")

        message += " The average last edit was " + info_string + " ago"

        self.plot_results(df)
        result = AnalysisResult(message, QualityLevel(level), self.importance, suggestion,
                                self.plot_name, self.title)
        if queue is not None:
            queue.put(result)
        if self.key is None:
            update_progress(result_path=self. status_file_path,
                            update=STATUS_UPDATES_ANALYSES["last_edit_f"])
        else:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["last_edit_f"] + f" for key: {key}")
        return result
