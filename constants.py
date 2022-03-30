import os
from types import MappingProxyType

# Notes: ------------------------------------------------------------------------------------------
# Errors are detected in status files through the prefix 'ERROR:'. Thus, if you change the error
# messages, you should keep this prefix.


# General: ----------------------------------------------------------------------------------------
TOOL_URL = "https://www.geog.uni-heidelberg.de/gis/sketchmaptool.html"

TEMPLATE_ANALYSES = "analyses.html"

TIMEOUT_OHSOME_METADATA = 50  # seconds

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

NR_OF_ANALYSES_STEPS = len(STATUS_UPDATES_ANALYSES) + 2  # Some analyses are run for multiple keys

ANALYSES_OUTPUT_PATH = "static/output"
OHSOME_API = "https://api.ohsome.org/stable"


# Status pages: -----------------------------------------------------------------------------------
INVALID_STATUS_LINK_MESSAGE = "Invalid link, something went wrong."
NO_STATUS_FILE_MESSAGE = "Process not found, it might have been cancelled or is still being " \
                         "started."
