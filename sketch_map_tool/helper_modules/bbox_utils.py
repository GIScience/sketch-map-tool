"""
Functions and classes to support work with bounding boxes and coordinates
"""

import re
from math import asin, cos, pi, sin, sqrt
from typing import Dict, Tuple


class BboxTooLargeException(Exception):
    """
    Exception indicating that a selected bounding box is too large to be processed
    """

    def __init__(self) -> None:
        super().__init__("Bounding box selection is too large")


class Bbox(object):
    """
    Bounding box (https://wiki.openstreetmap.org/w/index.php?title=Bounding_Box&oldid=2079213)
    """

    def __init__(self, lon1: float, lat1: float, lon2: float, lat2: float):
        self.lon1 = lon1
        self.lat1 = lat1
        self.lon2 = lon2
        self.lat2 = lat2

    @classmethod
    def bbox_from_str(cls, bbox_str: str) -> "Bbox":
        """
        Get a Bbox object from a string containing comma separated values for the coordinates

        :param bbox_str: String containing coordinates in the form 1.123,1.123,1.123,1.123
        :return: Bbox object based on the given coordinates
        """
        bbox_str = bbox_str.strip("; ")
        if not is_bbox_str(bbox_str) or len(bbox_str.split(";")) > 1:
            raise ValueError(
                "Parameter bbox_str is expected to contain the coordinates for one "
                "bounding box in the format 1.123,1.123,1.123,1.123"
            )
        coordinates = bbox_str.split(",")
        return Bbox(
            float(coordinates[0]),
            float(coordinates[1]),
            float(coordinates[2]),
            float(coordinates[3]),
        )

    def get_height(self) -> float:
        """
        Get the height of the bbox in m

        :return: Height the bounding box in metres
        """
        return calculate_distance((self.lat1, self.lon1), (self.lat2, self.lon1))

    def get_width(self) -> float:
        """
        Get the width of the bbox in m

        :return: Width the bounding box in metres
        """
        return calculate_distance((self.lat1, self.lon1), (self.lat1, self.lon2))

    def get_area(self) -> float:
        """
        Calculate the area that the bounding box roughly covers in km^2
        :return: Area covered by the bbox in km^2

        >>> bbox = Bbox(8.7065432, 49.400013, 8.7123456, 49.212345)
        >>> bbox.get_area() - 8.76 < 0.05
        True
        """
        width = self.get_width()
        height = self.get_height()
        return width * height / 1e6

    def get_center_point(self) -> Tuple[float, float]:
        """
        Get the center point of the bbox

        :return: (lat,lon)
        """
        return (self.lat1 + self.lat2) / 2, (self.lon1 + self.lon2) / 2

    def to_dict(self) -> Dict[str, float]:
        """
        Return a bbox dict with 'lon1', 'lon2', 'lat1' and 'lat2' keys

        :return: dict with one item for each value

        >>> bbox = Bbox(8.68947744, 49.2317231, 8.70706400, 49.2452287).to_dict()
        >>> bbox['lon1']
        8.68947744
        >>> bbox['lat2']
        49.2452287
        """
        return {
            "lon1": self.lon1,
            "lat1": self.lat1,
            "lon2": self.lon2,
            "lat2": self.lat2,
        }

    def get_str(self, mode: str = "minus") -> str:
        """
        Provide a string representation of the bounding box in a given mode

        :param mode: Either entries seperated by 'minus' or 'comma'
        :return: bbox string in format determined by 'mode'

        >>> Bbox(9.87, 1.23, 8.76, 2.34).get_str()
        '9_87-1_23-8_76-2_34'
        >>> Bbox(9.87, 1.23, 8.76, 2.34).get_str(mode="comma")
        '9.87,1.23,8.76,2.34'
        """
        if mode == "minus":
            return f"{self.lon1}-{self.lat1}-{self.lon2}-{self.lat2}".replace(".", "_")
        if mode == "comma":
            return f"{self.lon1},{self.lat1},{self.lon2},{self.lat2}"
        raise ValueError("'mode' needs to be either 'minus' or 'comma'")

    def __str__(self) -> str:
        return self.get_str(mode="comma")

    def __repr__(self) -> str:
        return self.get_str(mode="comma")


def is_bbox_str(bbox_str: str) -> bool:
    """
    Checks if a bbox string matches a regex for ';' separated lists of bounding boxes

    :param bbox_str: String to be checked
    :return: True if it is a list of bounding boxes, else False

    >>> is_bbox_str("10.6721131,53.8588041,10.6982375,53.8769225;")
    True
    >>> is_bbox_str("10,6721131 53,8588041 10,6982375 53.8769225;")
    False
    """
    regex = re.compile(
        r"\A((-?\d+\.\d+,){3}-?\d+\.\d+)|(((-?\d+\.\d+,){3}-?\d+\.\d+;)+)\Z"
    )
    if not regex.fullmatch(bbox_str):
        return False
    return True


def calculate_distance(
    point_a: Tuple[float, float], point_b: Tuple[float, float]
) -> float:
    """
    Calculate the distance between two points (lat,lon-format!) in metres using the Haversine
    formula

    :param point_a: First point of the two points of which the distance will be calculated
    :param point_b: Second point of the two points of which the distance will be calculated
    :return: Distance between the two points in metres

    >>> p_1 = (49.400013, 8.7065432)
    >>> p_2 = (49.212345, 8.7123456)
    >>> calculate_distance(p_1, p_2) - 20870 < 500
    True
    """
    earth_rad = 6371000
    lat_a = point_a[0] * pi / 180
    lat_b = point_b[0] * pi / 180
    lon_a = point_a[1] * pi / 180
    lon_b = point_b[1] * pi / 180
    distance = (
        2
        * earth_rad
        * asin(
            sqrt(
                sin((lat_b - lat_a) / 2) ** 2
                + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
            )
        )
    )
    return distance
