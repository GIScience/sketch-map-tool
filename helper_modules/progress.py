"""
Utilities to track the progress of analyses, sketch map generation or upload processes
"""
import os
from typing import List


class NoStatusFileException(Exception):
    """
    Exception raised when a status file is expected but not found
    """
    def __init__(self):
        super().__init__("Status file not available. Probably the process has not been started")


class InvalidResultPathException(ValueError):
    """
    Exception representing an invalid result path, i.e. a result path that is not of the form
    some/path/file.format
    """
    def __init__(self):
        super().__init__("'result_path' must contain the whole path to the file, ending with "
                         "name.format")


def update_progress(result_path: str, update: str):
    """
    Update the status file for a process by adding an update about the current state.
    The update file is stored in the same location as the result file (result_path)
    and has the ending .status

    :param result_path: Path where the result file of the process will be stored
    :param update: Message about the progress of the process to be added to the status file
    """
    if "." not in result_path:
        raise InvalidResultPathException()
    status_path = result_path[:result_path.rindex(".")]+".status"
    if os.path.exists(status_path):
        with open(status_path, "r", encoding="utf8") as status_file:
            lines = status_file.readlines()
        for line in lines:
            if "ERROR:" in line:
                os.remove(status_path)
                break
    folder_structure = result_path.split(os.sep)
    if len(folder_structure) > 1 and not os.path.exists(os.sep.join(folder_structure[:-1])):
        os.mkdir(os.sep.join(folder_structure[:-1]))
    with open(status_path, "a+", encoding="utf8") as status_file:
        status_file.write(update+"\n")


def get_nr_of_completed_steps(result_path: str) -> int:
    """
    Get the number of status updates for the result_file under result_path

    :param result_path: Path where the result file of the process will be stored
    :return: Nr of status updates found in status file

    :raise NoStatusFileException: If status file does not exist
    """
    if "." not in result_path:
        raise InvalidResultPathException()
    status_path = result_path[:result_path.rindex(".")] + ".status"
    if not os.path.exists(status_path):
        raise NoStatusFileException()
    with open(status_path, "r", encoding="utf8") as status_file:
        contents = status_file.readlines()
    return len(contents)


def get_status_updates(result_path: str) -> List[str]:
    """
    Get a list of all status updates for the result_file under result_path

    :param result_path: Path where the result file of the process will be stored
    :return: list with all status updates

    :raise NoStatusFileException: If status file does not exist
    """
    if "." not in result_path:
        raise InvalidResultPathException()
    status_path = result_path[:result_path.rindex(".")] + ".status"
    if not os.path.exists(status_path):
        raise NoStatusFileException()
    with open(status_path, "r", encoding="utf8") as status_file:
        contents = status_file.readlines()
    return contents


def has_failed(result_path: str) -> bool:
    """
    True, if the status file indicates that the process has failed

    :param result_path: Path where the result file of the process should have been stored
    :return: True, if status file contains 'ERROR:', else False

    :raise NoStatusFileException: If status file does not exist
    """
    if "." not in result_path:
        raise InvalidResultPathException()
    status_path = result_path[:result_path.rindex(".")] + ".status"
    if not os.path.exists(status_path):
        raise NoStatusFileException()
    with open(status_path, "r", encoding="utf8") as status_file:
        contents = status_file.readlines()
    for content in contents:
        if "ERROR:" in content:
            return True
    return False
