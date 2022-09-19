"""
Constants like messages shown to the user for the whole tool and its different parts
"""
from enum import Enum
from types import MappingProxyType

# Notes: ------------------------------------------------------------------------------------------
# Errors are detected in status files through the prefix 'ERROR:'. Thus, if you change the error
# messages, you should keep this prefix.


# General: ----------------------------------------------------------------------------------------
TOOL_URL = "https://www.geog.uni-heidelberg.de/gis/sketchmaptool.html"

TEMPLATE_ANALYSES = "analyses.html"
TEMPLATE_ANALYSES_RESULTS = "analyses_result.html"

TIMEOUT_REQUESTS = 50  # seconds, see
#                        https://requests.readthedocs.io/en/stable/user/advanced/#timeouts

# Analyses: ---------------------------------------------------------------------------------------
STATUS_UPDATES_ANALYSES = MappingProxyType({
    "start": "Preparing analyses...",
    "last_edit_s": "Running data currentness analyses...",
    "last_edit_f": "Finished data currentness analyses...",
    "saturation_s": "Running data completeness analyses...",
    "saturation_f": "Finished data completeness analyses...",
    "landmark_s": "Running landmark density analyses...",
    "landmark_f": "Finished landmark density analyses...",
    "sources_s": "Running sources analyses...",
    "sources_f": "Finished sources analyses...",
    "results": "Generating result files...",
    "completed": "Completed"
})

STATUS_ERROR_OHSOME_NOT_AVAILABLE = "ERROR: The ohsome API " \
                                    "(https://heigit.org/big-spatial-data-analytics-en/ohsome/)," \
                                    " which the tool is using to get aggregated OSM data, is " \
                                    "currently not available. Please try again later"
RESULT_COULD_NOT_BE_LOADED = "ERROR: The result file could not be loaded. Please make sure the " \
                             "URL is correct."

BBOX_TOO_BIG = "Invalid input: Selected bounding box is bigger than 50 km^2. Please select a " \
               "smaller one. The Sketch Map Tool is not meant for analyzing large areas - for " \
               "this purpose you might use https://hex.ohsome.org for example."

NR_OF_ANALYSES_STEPS = len(STATUS_UPDATES_ANALYSES) + 2  # Some analyses are run for multiple keys

ANALYSES_OUTPUT_PATH = "static/output"
OHSOME_API = "https://api.ohsome.org/stable"


# Status pages: -----------------------------------------------------------------------------------
INVALID_STATUS_LINK_MESSAGE = "Invalid link, something went wrong."
NO_STATUS_FILE_MESSAGE = "Process not found, it might have been cancelled or is still being " \
                         "started."

# Error Codes: -----------------------------------------------------------------------------------


class ErrorCode(Enum):
    """
    Error codes for certain errors which are given e.g. as a URL parameter for the corresponding
    message to be displayed.
    """
    # Analyses
    RESULT_COULD_NOT_BE_LOADED = 100
    # Status
    INVALID_STATUS_LINK_MESSAGE = 200
    NO_STATUS_FILE_MESSAGE = 201


ERROR_MSG_FOR_CODE = {
    ErrorCode.RESULT_COULD_NOT_BE_LOADED: RESULT_COULD_NOT_BE_LOADED,
    ErrorCode.INVALID_STATUS_LINK_MESSAGE: INVALID_STATUS_LINK_MESSAGE,
    ErrorCode.NO_STATUS_FILE_MESSAGE: NO_STATUS_FILE_MESSAGE
}
