"""
- Idea: Check the changes in length or density of relevant features by comparing the changes in
        percent over time (yearly). To be suitable for a sketch map, the data (i.e. length or
        density) should have been heavily updated at least once (initialization) and saturated (no
        frequent drastic changes, indicating a state close to completeness)
- Value: change in percent of density (e.g. for amenity features) or length (e.g. for highway
         features)
- References:
              * ''Estimating Completeness of VGI Datasets by Analyzing Community Activity Over Time
                Periods'' (Gröchenig, Brunauer & Rehrl, 2014,
                https://link.springer.com/chapter/10.1007/978-3-319-03611-3_1) as cited in
                ''A Framework for Data-Centric Analysis of Mapping Activity in the Context of
                Volunteered Geographic Information''  (Rehrl & Gröchenig, 2016,
                https://www.mdpi.com/2220-9964/5/3/37/pdf)
              * ''A comprehensive framework for intrinsic OpenStreetMap quality analysis.''
                (Barron, Neis, & Zipf, 2014,
                https://onlinelibrary.wiley.com/doi/full/10.1111/tgis.12073)
"""
# pylint: disable=duplicate-code
import multiprocessing  # noqa  # pylint: disable=unused-import
import matplotlib.pyplot as plt
from typing import List, Tuple, Union, Any
import requests

from analyses.helpers import AnalysisResult, QualityLevel
from analyses.modules.analysis_base import Analysis

from constants import STATUS_UPDATES_ANALYSES, OHSOME_API
from helper_modules.bbox_utils import Bbox
from helper_modules.progress import update_progress


class CompletenessAnalysis(Analysis):
    """
    Check how complete, i.e. saturated the mapping of OSM features is
    """
    importance = 1.0
    special_importance_completion = {"amenity": 0.5}  # otherwise, the general importance is used
    special_importance_lack_of_data = {  # when threshold_major_change is never surpassed
        "highway": 2.0
    }
    threshold_yellow = 5  # percent yearly change in feature length/density
    threshold_red = 10  # percent yearly change in feature length/density
    threshold_major_change = 25  # percent yearly change in feature length/density
    #                              (if never surpassed, a general lack of data is assumed)
    baseline_thresholds = {
        "length": 7500,  # m per km^2, no major change check when surpassed
        "density": 375,  # features per km^2, no major change check when surpassed
    }

    def __init__(self,
                 bbox: Bbox,
                 time: str,
                 plot_location: str = "./",
                 status_file_path: str = "analyses.status",
                 key: Union[None, str] = None,
                 measure: str = "density",
                 measure_unit: str = "features per km²"):
        """
        :param bbox: Bounding box the OSM data of which should be inspected
        :param time: time string covering the time span and steps to be analyzed
                     (e.g. '2014-01-01/2017-01-01/P1Y')
        :param plot_location: Path to the directory in which the plots are stored
        :param status_file_path: Path to the file the status updates should be written to
        :param key: If given, only features with this key are analyzed (e.g. highway)
        :param measure: Aggregation to be requested from ohsome (e.g. 'density' or 'length')
        :param measure_unit: Unit of the measure to be included in the outputs
        """
        self.bbox = bbox
        self.time = time
        self.key = key
        self.measure = measure
        self.measure_unit = measure_unit
        self._plot_location = plot_location
        self._status_file_path = status_file_path
        self.title = "Saturation Analysis"
        if key is not None:
            self.title += f" for '{key}' features"
            self.plot_name = f"_plot_saturation_{key}.png"
        else:
            self.plot_name = "_plot_saturation_general.png"

    @property
    def plot_location(self) -> str:
        return self._plot_location

    @property
    def status_file_path(self) -> str:
        return self._status_file_path

    @staticmethod
    def request(aggregation: str, **params: Any) -> requests.Response:
        """
        Send a request with a given aggregation and parameters to the Ohsome API

        :param aggregation: Aggregation to be requested from Ohsome (added to the URL)
                            E.g.: 'length'
        :param params: Parameters to be added to the Ohsome request
                       E.g.: bboxes='1.23,2.34,3.45,4.56', time='2014-01-01/2017-01-01/P1Y',
                       keys='amenity', types='node,way'
        :return: Response from ohsome
        """
        aggregation = aggregation.replace("density", "count/density")
        return requests.get(f"{OHSOME_API}/elements/{aggregation}", params)

    def plot_results(self, data: List[Tuple[str, float]], title: str, y_label: str) -> None:
        """
        Visualize the analysis' results in a plot

        :param data: A list of tuples [(timestamp, value),...]
        :param title: The title of the plot
        :param y_label: Label of the y-axis
        """
        # extract timestamps and convert them to numpy timestamps for plotting
        timestamps = [i[0][0:10] for i in data]

        # extract length/density of features at given timestamps
        values = [i[1] for i in data]

        # define plot
        fig = plt.figure(figsize=(7, 7))
        plot = fig.add_subplot(111)
        plot.plot(timestamps, values)
        plot.set_ylim(bottom=0)
        plot.set_xlabel("timestamp (date)")
        plot.set_ylabel(y_label)
        # rotate and right align the x labels, and moves the bottom of the axes up to make room
        # for them
        fig.autofmt_xdate()

        plot.set_title(title)
        plot.grid(True)
        output_path = self.plot_location + self.plot_name
        fig.savefig(output_path)

    def run(self, queue: Union[None, "multiprocessing.Queue[AnalysisResult]"] = None) \
            -> AnalysisResult:  # noqa: C901
        """
        Inspect the saturation, i.e. completeness of OSM feature mapping

        :param queue: Queue to which the result is appended

        :return: Result object
        """
        if self.key:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["saturation_s"] +
                            f" for key: {self.key}")
        else:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["saturation_s"])
        if self.key:
            ohsome_response = self.request(self.measure, bboxes=str(self.bbox), time=self.time,
                                           keys=self.key, types="node,way").json()
        else:
            ohsome_response = self.request(self.measure, bboxes=str(self.bbox), time=self.time,
                                           types="node,way").json()

        values = [data_point["value"] for data_point in ohsome_response["result"]]

        slopes = [0]
        for i in range(1, len(values)):
            if values[i - 1] > 0:
                slopes.append(100 * ((values[i] - values[i - 1]) / values[i - 1]))

        values_with_timestamps = [(data_point["timestamp"], data_point["value"])
                                  for data_point in ohsome_response["result"]]
        if self.key:
            title = f"Development of {self.key} length"
            y_label = f"{self.measure.capitalize()} of features with '{self.key}' tag " \
                      f"({self.measure_unit})"
        else:
            title = "Development of feature length"
            y_label = f"{self.measure.capitalize()} of features tag ({self.measure_unit})"
        self.plot_results(values_with_timestamps, title, y_label)
        recommendation = ""
        importance = self.importance
        if self.key:
            importance = self.special_importance_completion.get(self.key, self.importance)
        level = QualityLevel.GREEN
        baseline_index = 0  # Find the first yearly value greater than 0 (the baseline, as
        # percentage increase from 0 to x cannot be determined)
        for value in values:
            if value > 0:
                break
            baseline_index += 1
        if baseline_index >= len(values):  # All values are 0
            baseline_index = 0
        baseline = values[baseline_index] / self.bbox.get_area()
        baseline_threshold_surpassed = False
        if self.measure in self.baseline_thresholds.keys():
            baseline_threshold_surpassed = baseline > self.baseline_thresholds[self.measure]
        if max(slopes) < self.threshold_major_change and not baseline_threshold_surpassed:
            level = QualityLevel.RED
            if self.key:
                importance = self.special_importance_lack_of_data.get(self.key, self.importance)
                message = f"There has never been a yearly increase of feature {self.measure} " \
                          f"bigger than {self.threshold_major_change}% in this region for " \
                          f"{self.key} features. There might be a lack of data in this area."
                recommendation = f"Be aware that there might be a lack of data regarding " \
                                 f"{self.key} features."
            else:
                message = f"There has never been a yearly increase of feature {self.measure} " \
                          f"bigger than {self.threshold_major_change}% in this region " \
                          f"for all features. There might be a lack of data in this area."
                recommendation = "Be aware that there might be a general lack of data."
            result = AnalysisResult(message, level, importance, recommendation, self.plot_name,
                                    self.title)
            if queue is not None:
                queue.put(result)
            return result

        last_slope = round(slopes[-1], 4)
        last_slope_display = abs(round(last_slope, 2))
        if self.key:
            message = f"The mapping of {self.key} features seems to be saturated. " \
                      f"There was just an increase of {last_slope_display}% in feature " \
                      f"{self.measure} during the last year."
        else:
            message = f"The general mapping of features seems to be near to a saturated state. " \
                      f"There was just an increase of {last_slope_display}% in feature " \
                      f"{self.measure} during the last year."
        if last_slope == 0:
            if self.key:
                message = f"The mapping of {self.key} features seems to be saturated. There was " \
                          f"no change of feature {self.measure} in the last year."
            else:
                message = f"The general mapping of features seems to be near to a saturated" \
                          f" state. There was no change of feature {self.measure} in the last year."
        elif last_slope < 0:
            if self.key:
                message = f"The mapping of {self.key} features seems to be saturated. There even" \
                          f" was a decrease of {last_slope_display}% in feature {self.measure}" \
                          f" during the last year."
            else:
                message = f"The general mapping of features seems to be near to a saturated " \
                          f"state. There even was a decrease of {last_slope_display}% in feature " \
                          f"{self.measure} during the last year."

        elif last_slope > self.threshold_yellow:
            level = QualityLevel.YELLOW
            if self.key:
                message = f"The mapping of {self.key} features might not be saturated yet. There " \
                          f"was an increase of {last_slope_display}% in feature {self.measure} " \
                          f"during the last year."
            else:
                message = f"The general mapping of features might not be saturated yet. There " \
                          f"was an increase of {last_slope_display}% in feature {self.measure}" \
                          f" during the last year."
        elif last_slope > self.threshold_red:
            level = QualityLevel.RED
            if self.key:
                message = f"The mapping of {self.key} features seems to be far from a saturated " \
                          f"state. There was an increase of {last_slope_display}% in feature " \
                          f"{self.measure} during the last year."
                recommendation = f"Be aware that the mapping of {self.key} features does not " \
                                 f"seem to be saturated and is therefore possibly not complete yet."
            else:
                message = f"The general mapping of features seems to be far from a saturated " \
                          f"state. There was an increase of {last_slope_display}% in feature" \
                          f" {self.measure} during the last year."
                recommendation = "Be aware that the general mapping of features does not seem to" \
                                 " be saturated and is therefore possibly not complete yet."
        result = AnalysisResult(message, level, importance, recommendation, self.plot_name,
                                self.title)

        if queue is not None:
            queue.put(result)
        if self.key:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["saturation_f"] +
                            f" for key: {self.key}")
        else:
            update_progress(result_path=self.status_file_path,
                            update=STATUS_UPDATES_ANALYSES["saturation_f"])
        return result
