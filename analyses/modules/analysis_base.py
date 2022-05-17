"""
Abstract base class for all analyses
"""
import multiprocessing  # noqa  # pylint: disable=unused-import
from abc import ABC, abstractmethod
from typing import Union

from analyses.helpers import AnalysisResult


class Analysis(ABC):
    """
    Base class for an OSM analysis
    """

    @property
    @abstractmethod
    def importance(self) -> float:
        """
        The weight of the analyses results when calculating a general fitness score
        Also reflected in output to the user: 'less important' if < 1, 'very important' if > 1.5
        otherwise 'important'

        :return: Importance, i.e. weight of this analysis
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def threshold_yellow(self) -> Union[None, float]:
        """
        If this threshold is surpassed, the level changes from green (good fitness) to yellow
        (potential problems)

        :return: Threshold from level green to level yellow
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def threshold_red(self) -> Union[None, float]:
        """
        If this threshold is surpassed, the level changes from yellow (potential problems) to red
        (probable problems)

        :return: Threshold from level yellow to level red
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def plot_location(self) -> str:
        """
        :return: Path to the directory in which the generated plots are stored
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def status_file_path(self) -> str:
        """
        :return: Path to the file the status updates should be written to
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self, queue: Union[None, "multiprocessing.Queue[AnalysisResult]"]) -> AnalysisResult:
        """
        Run the analysis

        :param queue: multiprocessing.Queue to store the results in multiprocessing applications
        :return: Results of the analysis
        """
        raise NotImplementedError()
