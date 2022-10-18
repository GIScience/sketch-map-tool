// margins as defined in python: https://github.com/GIScience/sketch-map-tool/blob/add-sketchmap-generation/sketch_map_tool/printer/modules/paper_formats/paper_formats.py
const SKETCH_MAP_MARGINS = {
    "A0": {
        "landscape": {right: 15},
        "portrait": {bottom: 15}
    },
    "A1": {
        "landscape": {right: 12},
        "portrait": {bottom: 12}
    },
    "A2": {
        "landscape": {right: 7.5},
        "portrait": {bottom: 7.5}
    },
    "A3": {
        "landscape": {right: 7},
        "portrait": {bottom: 7}
    },
    "A4": {
        "landscape": {right: 5},
        "portrait": {bottom: 5}
    },
    // A5 is currently not supported by ol-print-layout-control
    //"A5": {
    //     "landscape": {right: 3},
    //     "portrait": {bottom: 3}
    // },
    "LEGAL": {
        "landscape": {right: 5},
        "portrait": {bottom: 5}
    },
// TABLOID is the same as LEDGER
    "TABLOID": {
        "landscape": {right: 7},
        "portrait": {bottom: 7}
    },
    "LETTER": {
        "landscape": {right: 5},
        "portrait": {bottom: 5}
    }
};