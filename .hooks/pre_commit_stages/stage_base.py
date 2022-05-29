"""
Contains the abstract base class 'Stage' for stages
"""
from abc import ABC, abstractmethod
from typing import List


class Stage(ABC):
    """
    Stage in the pre-commit pipeline
    """

    @property
    @abstractmethod
    def file_formats(self) -> List[str]:
        """
        :return: File formats (endings) on which the stage should be executed, e.g. ['py'] for
                 Python files
        """
        raise NotImplementedError

    def __init__(self, changed_files: List[str]) -> None:
        """
        Initialize the stage with a list of all changed and staged files.
        If at least one of the changed files has a file format in file_formats,
        call the run() method

        :param changed_files: List of files with staged changes for the current git commit
        """
        self.files = changed_files
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running {self} ...")
                self.run()
                break

    @abstractmethod
    def run(self) -> None:
        """
        Execute the stage
        """
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError
