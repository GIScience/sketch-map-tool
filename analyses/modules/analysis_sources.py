"""
- Idea: Check if there are sources accountable for a substantial share of all features and report
        them, so that their trustworthiness can be inspected
- Value: Share of features with a source
- Reference: "The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory
             Mapping." (Klonner, Hartmann, Dischl, Djami, Anderson, Raifer, Lima-Silva, Castro
             Degrossi, Zipf, Porto de Albuquerque, 2021, https://doi.org/10.3390/ijgi10030130)
"""

import multiprocessing
from typing import List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.helpers import AnalysisResult, QualityLevel
from analyses.modules.analysis_base import Analysis

from constants import STATUS_UPDATES_ANALYSES
from helper_modules.progress import update_progress


class SourcesAnalysis(Analysis):
    """
    Check if there are sources accountable for a substantial share of all features
    """
    importance = 0  # Manual inspection needed to estimate the trustworthiness
    threshold_yellow = 0.02  # i.e. 2 %
    threshold_red = None  # A red level cannot be reached as manual inspection is necessary

    title = "Source Analysis"
    plot_name = "_plot_sources.png"

    white_list = ("BAG", "Bing", "bing", "digitalglobe", "Mapbox", "cuzk:km", "Fugro 2005",
                  "landsat", "uhul:ortofoto", "yahoo", "AGIV", "aerial imagery", "survey", "image",
                  "mapillary", "local knowledge", "GPS", "common knowledge", "geoimage.at",
                  "HiRes aerial imagery")  # Typical sources that are either known for sufficient
    #                                        quality or where inspection is impossible. These
    #                                        sources are ignored in the suggestions, but shown in
    #                                        the plot.

    def __init__(self,
                 ohsome_export: List[dict],
                 plot_location: str = "./",
                 status_file_path: str = "analyses.status"):
        """
        :param ohsome_export: Full history OSM data from ohsome in form of a list of features with
                              their attributes
        :param plot_location: Path to the directory in which the plots are stored
        :param status_file_path: Path to the file the status updates should be written to
        """
        self.data = ohsome_export
        self._plot_location = plot_location
        self._status_file_path = status_file_path

    @property
    def plot_location(self):
        return self._plot_location

    @property
    def status_file_path(self):
        return self._status_file_path

    def plot_results(self, source_shares_dict: dict) -> None:
        """
        Create a pie plot showing the shares of the different sources with shares above the
        threshold

        :param source_shares_dict: Dict containing source names as keys and their shares as values
        """
        sources_for_plot = []
        below_threshold_share = 0
        not_tagged_share = 0

        for source, share in source_shares_dict.items():
            if share < self.threshold_yellow * 100:
                below_threshold_share += share
            elif str(source) == "nan":
                not_tagged_share += share
            elif len(str(source)) <= 75:
                sources_for_plot.append((str(source), share))
            else:
                sources_for_plot.append((str(source)[:75], share))

        sources_for_plot.append((f"Below {self.threshold_yellow * 100} % threshold",
                                 below_threshold_share))
        sources_for_plot.append(("Not tagged", not_tagged_share))
        sources_for_plot.sort(key=lambda x: x[1], reverse=True)

        labels = [f"{source[0]} ({round(source[1], 2)} %)" for source in sources_for_plot]
        values = [source[1] for source in sources_for_plot]

        fig = plt.figure(figsize=(7, 7))
        plot = fig.add_subplot(111)
        plot.pie(values, autopct='%.2f', textprops={'color': 'w', 'fontsize': 'xx-large'})
        lgd = plot.legend(labels, title='Names', loc='lower right', bbox_to_anchor=(.8, 0, 0.5, 1),
                          fontsize=12)
        plot.set_title("Shares of specified sources among all features")
        fig.savefig(self.plot_location + self.plot_name, bbox_inches="tight",
                    bbox_extra_artists=(lgd,))

    def run(self, queue: multiprocessing.Queue = None) -> AnalysisResult:
        """
        Retrieve important sources of OSM features

        :param queue: Queue to which the result is appended
        :return: Result object

        >>> data = [{
        ... "type" : "Feature",
        ... "geometry" : {
        ... "type" : "Polygon",
        ... "coordinates" : []},
        ... "properties" : {
        ... "@osmId" : "way/399317554",
        ... "@validFrom" : "2016-02-20T21:12:04Z",
        ... "@validTo" : "2016-02-21T21:50:18Z"}},{ # Removed!
        ... "type" : "Feature",
        ... "geometry" : {
        ... "type" : "Polygon",
        ... "coordinates" : []},
        ... "properties" : {
        ... "@osmId" : "way/399317556",
        ... "@validFrom" : "2016-02-22T21:12:04Z",
        ... "@validTo" : "2016-02-22T21:50:18Z",
        ... "addr:housenumber" : "cll 24 # 23-56",
        ... "source": "brain"}},{ # Should have 50%!
        ... "type" : "Feature",
        ... "geometry" : {
        ... "type" : "Polygon",
        ... "coordinates" : []},
        ... "properties" : {
        ... "@osmId" : "way/399317558",
        ... "@validFrom" : "2016-02-22T21:12:04Z",
        ... "@validTo" : "2016-02-22T21:50:18Z"}}]
        >>> result = SourcesAnalysis(data).run()
        >>> result.level.value, result.importance
        (1, 0)
        >>> result.message # doctest: +ELLIPSIS
        'There is at least one source accounting for a substantial share of all features, which you might want to inspect...
        >>> result.suggestion
        "You might want to check the following sources, which account for a substantial share of all features: 'brain' (50.0 %)."
        """
        update_progress(self.status_file_path, STATUS_UPDATES_ANALYSES["sources_s"])
        df = pd.DataFrame([i["properties"] for i in self.data])

        # Remove older versions of features and features that have been deleted:
        df = df.apply(pd.Series)
        df = df.drop_duplicates(subset=['@osmId'], keep='last')
        df.rename({"@validTo": "validTo"}, axis=1, inplace=True)
        df["validTo"] = df.apply(lambda row: np.datetime64(str(row.validTo).replace('Z', '')),
                                 axis=1)
        max_validTo = max(df['validTo'])
        df.drop(df[df.validTo < max_validTo].index, inplace=True)

        if "source" not in df.keys():
            result = AnalysisResult("No source information found. Thus, inspection of sources is "
                                    "not possible.", QualityLevel.GREEN, self.importance,
                                    title_for_report=self.title)
            if queue is not None:
                queue.put(result)
            return result

        source_shares = df['source'].value_counts(normalize=True, dropna=False) * 100
        source_shares_dict = source_shares.to_dict()
        relevant_sources = ""
        for source, share in source_shares_dict.items():
            if str(source) != "nan" and str(source) not in self.white_list and \
                    share >= self.threshold_yellow * 100:
                relevant_sources += f", '{source}' ({round(share, 2)} %)"
        relevant_sources = relevant_sources.strip(" ,")

        self.plot_results(source_shares_dict)

        if len(relevant_sources) > 0:
            result = AnalysisResult("There is at least one source accounting for a substantial "
                                    "share of all features, which you might want to inspect ("
                                    "See recommendations for more details).", QualityLevel.YELLOW,
                                    self.importance,
                                    "You might want to check the following sources, which account "
                                    f"for a substantial share of all features: {relevant_sources}.",
                                    self.plot_name, self.title)
        else:
            result = AnalysisResult("No source relevant for inspection found.", QualityLevel.GREEN,
                                    self.importance, "", self.plot_name, self.title)
        if queue is not None:
            queue.put(result)
        update_progress(self.status_file_path, STATUS_UPDATES_ANALYSES["sources_f"])
        return result
