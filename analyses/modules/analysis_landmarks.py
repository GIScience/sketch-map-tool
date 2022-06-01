"""
- Idea: Participants using the sketch maps should be able to orientate properly on these maps for
        being able to mark areas of interest accurately. If many features that the people
        probably know are visible on the map, it is probably much easier for them to orientate on
        it, while a lower density of such features might make it more difficult to orientate.

        As landmarks considered are OSM features with the following tags:
        railway=station
        shop=*
        amenity=place_of_worship
        amenity=pharmacy
        amenity=hospital
        amenity=restaurant
        amenity=fuel
        amenity=school
        amenity=university
        amenity=college
        amenity=townhall
        amenity=police
        amenity=fire_station
        highway=bus_stop
        tourism=hotel
        tourism=attraction
        leisure=park
        boundary=national_park
        natural=peak
        natural=water
        waterway=*
- Value: Accumulated density of landmarks (see above) per km²
- Reference: "The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory
             Mapping." (Klonner, Hartmann, Dischl, Djami, Anderson, Raifer, Lima-Silva, Castro
             Degrossi, Zipf, Porto de Albuquerque, 2021, https://doi.org/10.3390/ijgi10030130)
"""
# pylint: disable=duplicate-code
import json
import multiprocessing  # noqa  # pylint: disable=unused-import
from typing import Dict, Optional

import requests
from matplotlib import pyplot as plt

from analyses.helpers import AnalysisResult, QualityLevel
from analyses.modules.analysis_base import Analysis
from helper_modules.bbox_utils import Bbox
from helper_modules.progress import update_progress
from constants import STATUS_UPDATES_ANALYSES, OHSOME_API


class LandmarkAnalysis(Analysis):
    """
    Inspect the density of orientation providing OSM features, i.e. landmarks
    """
    importance = 2
    threshold_yellow = 30  # POIs per km^2
    threshold_red = 10  # POIs per km^2

    title = "Landmark Density Analysis"
    plot_name = "_plot_poi.png"

    def __init__(self,
                 bbox: Bbox,
                 time_str: str,
                 plot_location: str = "./",
                 status_file_path: str = "analyses.status",
                 percent_threshold_for_plot: float = 0.01):
        """
        :param bbox: The bounding box for which the analysis is performed
        :param time_str: Timestamp as parameter for the ohsome API for which the landmark density
                         is inspected
        :param plot_location: Path to the directory in which the plots are stored
        :param status_file_path: Path to the file the status updates should be written to
        :param percent_threshold_for_plot: Threshold for shares to be included in the pie chart
        """
        self.bbox = bbox
        self.time_str = time_str
        self._plot_location = plot_location
        self._status_file_path = status_file_path
        self.percent_threshold_for_plot = percent_threshold_for_plot

        self.density = {
            "shops": 0,
            "places_of_worship": 0,
            "hotels": 0,
            "attractions": 0,
            "health_facilities_pharmacies": 0,
            "restaurants": 0,
            "gas_stations": 0,
            "education": 0,
            "public_safety": 0,
            "public_transport": 0,
            "parks": 0,
            "mountains": 0,
            "waterways": 0,
            "townhalls": 0
        }
        self.plot_labels = {
            "shops": "Shops",
            "places_of_worship": "Places of worship",
            "hotels": "Hotels",
            "attractions": "Attractions",
            "health_facilities_pharmacies": "Health Facilities &\nPharmacies",
            "restaurants": "Restaurants",
            "gas_stations": "Gas Stations",
            "education": "Education",
            "public_safety": "Public Safety Facilities",
            "public_transport": "Public Transport",
            "parks": "Parks",
            "mountains": "Mountains",
            "waterways": "Waterways",
            "townhalls": "Townhalls"
        }
        self.density_sum = 0

    @property
    def plot_location(self) -> str:
        return self._plot_location

    @property
    def status_file_path(self) -> str:
        return self._status_file_path

    def add_density_for_tag(self, keys: Optional[str], values: Optional[str],
                            category: str) -> None:
        """
        Send a request to the ohsome API to get the density of features with the given keys and
        values. Update the instance variables 'density' and 'density_sum' with the obtained value.

        :param keys: Parameter 'keys' to be used in the request to the ohsome API. Give None to not
                     use this parameter.
        :param values: Parameter 'values' to be used in the request to the ohsome API. Give None to
                       not use this parameter.
        :param category: Key of the value in the instance variable 'density' (dict) to which the
                             density value should be added
        """
        if category not in self.density.keys():
            raise ValueError(f"Category '{category}' is not a key in the dictionary 'density'.")
        url = "/elements/count/density"
        params = {"bboxes": self.bbox.get_str(mode="comma"),
                  "types": "node,way",
                  "time": self.time_str
                  }
        if keys is not None:
            params.update({"keys": keys})
        if values is not None:
            params.update({"values": values})

        result = requests.get(OHSOME_API + url, params)
        result = json.loads(result.text)["result"][0]
        self.density_sum += result["value"]
        self.density[category] += result["value"]

    def add_density_for_tag_aggregated(self, key: str, values_categories: Dict[str, str]) -> None:
        """
        Send a request to the ohsome API to get the aggregated density of features with the given
        key and values. Update the instance variables 'density' and 'density_sum' with the obtained
        values.

        :param key: Parameter 'groupByKey' to be used in the request to the ohsome API.
        :param values_categories: Dict containing as keys the values to be used as parameter
                                  'groupByValues' for the request to the ohsome API. Values are
                                  the categories corresponding to each groupByValue, i.e. keys of
                                  the value in the instance variable 'density' (dict) to which the
                                  density value should be added
        """
        for value in values_categories.values():
            if value not in self.density.keys():
                raise ValueError(f"Invalid value '{value}' in argument 'values_categories'. There "
                                 f"is no such key in the dictionary 'density'.")
        url = "/elements/count/density/groupBy/tag"
        params = {"bboxes": self.bbox.get_str(mode="comma"),
                  "types": "node,way",
                  "time": self.time_str,
                  "groupByKey": key,
                  "groupByValues": ", ".join(values_categories.keys())
                  }

        result = requests.get(OHSOME_API + url, params)
        result = json.loads(result.text)["groupByResult"]

        for group_by_result in result:
            if group_by_result["groupByObject"] != "remainder":
                self.density_sum += group_by_result["result"][0]["value"]
                self.density[values_categories[group_by_result["groupByObject"]
                             .replace(f"{key}=", "")]] += group_by_result["result"][0]["value"]

    def create_plot(self) -> None:
        """
        Create a pie plot based on the values stored in the instance variable 'density' and store
        it under the path given in the instance variable 'plot_location'.
        :return:
        """
        shares_with_labels = []
        for key in self.density.keys():
            percentage = round(100 * self.density[key] / self.density_sum, 2)
            shares_with_labels.append((percentage, f"{self.plot_labels[key]} ({percentage}%)"))

        for pair in shares_with_labels.copy():
            if pair[0] < self.percent_threshold_for_plot:
                shares_with_labels.remove(pair)

        shares_with_labels.sort(key=lambda x: x[0], reverse=True)
        data = [x[0] for x in shares_with_labels]
        labels = [x[1] for x in shares_with_labels]

        fig = plt.figure(figsize=(7, 7))
        plot = fig.add_subplot(111)
        plot.pie(data, autopct="%.0f%%", textprops={"color": "w", "fontsize": "xx-large"})
        lgd = plot.legend(labels, title="Landmark Categories", loc="lower right",
                          bbox_to_anchor=(.8, 0, 0.5, 1), fontsize=12)
        plot.set_title("Shares of different Landmark Categories")
        fig.savefig(self.plot_location + self.plot_name, bbox_inches="tight",
                    bbox_extra_artists=(lgd,))

    def run(self,
            queue: Optional["multiprocessing.Queue[AnalysisResult]"] = None) -> AnalysisResult:
        """
        Analyze the density of landmark features

        :param queue: Queue to which the result is appended
        """
        update_progress(result_path=self.status_file_path,
                        update=STATUS_UPDATES_ANALYSES["landmark_s"])

        self.add_density_for_tag(keys="railway", values="station", category="public_transport")
        self.add_density_for_tag(keys="shop", values=None, category="shops")

        amenity_categories = {
            "place_of_worship": "places_of_worship",
            "pharmacy": "health_facilities_pharmacies",
            "hospital": "health_facilities_pharmacies",
            "restaurant": "restaurants",
            "fuel": "gas_stations",
            "school": "education",
            "university": "education",
            "college": "education",
            "townhall": "townhalls",
            "police": "public_safety",
            "fire_station": "public_safety"
        }
        self.add_density_for_tag_aggregated(key="amenity", values_categories=amenity_categories)

        self.add_density_for_tag(keys="highway", values="bus_stop", category="public_transport")

        tourism_categories = {
            "hotel": "hotels",
            "attraction": "attractions"
        }
        self.add_density_for_tag_aggregated(key="tourism", values_categories=tourism_categories)

        self.add_density_for_tag(keys="leisure", values="park", category="parks")
        self.add_density_for_tag(keys="boundary", values="national_park", category="parks")

        natural_categories = {
            "water": "waterways",
            "peak": "mountains"
        }
        self.add_density_for_tag_aggregated(key="natural", values_categories=natural_categories)

        self.add_density_for_tag(keys="waterway", values=None, category="waterways")

        density_rounded = round(self.density_sum, 2)
        level = QualityLevel.GREEN

        message_prefix = "The density of landmarks (points of reference, e.g. waterbodies, " \
                         f"supermarkets, churches, bus stops) is {density_rounded} features per " \
                         f"km&#x00B2. "

        message = message_prefix + "It is probably easy to orientate on OSM-based sketch maps " \
                                   "of this region."
        suggestion = ""

        if self.density_sum < self.threshold_yellow:
            level = QualityLevel.YELLOW
            message = message_prefix + "It might be difficult to orientate on OSM-based sketch " \
                                       "maps of this region."
            suggestion = "There are not many orientation providing features available, you " \
                         "should explore, if participants can orientate properly."

        if self.density_sum < self.threshold_red:
            level = QualityLevel.RED
            message = message_prefix + "It is probably hard to orientate on OSM-based sketch " \
                                       "maps of this region."
            suggestion = "There are just few orientation providing features available, you " \
                         "should explore, if participants can orientate properly."

        if self.density_sum > 0:
            self.create_plot()

        result = AnalysisResult(message, level, self.importance, suggestion, self.plot_name,
                                self.title)
        if queue is not None:
            queue.put(result)
        update_progress(result_path=self.status_file_path,
                        update=STATUS_UPDATES_ANALYSES["landmark_f"])
        return result
