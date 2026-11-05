// margins as defined in python: https://github.com/GIScience/sketch-map-tool/blob/add-sketchmap-generation/sketch_map_tool/printer/modules/paper_formats/paper_formats.py
const MAP_MARGINS = {
    A0: 1.0,
    A1: 1.0,
    A2: 1.0,
    A3: 1.0,
    A4: 1.0,
    LEGAL: 1.0,
    TABLOID: 1.0,
    LETTER: 1.0,
};
const SKETCH_MAP_MARGINS = {
    A0: {
        landscape: {
            right: 15 + MAP_MARGINS.A0,
            bottom: MAP_MARGINS.A0,
            left: MAP_MARGINS.A0,
            top: MAP_MARGINS.A0,
        },
        portrait: {
            right: MAP_MARGINS.A0,
            bottom: 15 + MAP_MARGINS.A0,
            left: MAP_MARGINS.A0,
            top: MAP_MARGINS.A0,
        },
    },
    A1: {
        landscape: {
            right: 12 + MAP_MARGINS.A1,
            bottom: MAP_MARGINS.A1,
            left: MAP_MARGINS.A1,
            top: MAP_MARGINS.A1,
        },
        portrait: {
            right: MAP_MARGINS.A1,
            bottom: 12 + MAP_MARGINS.A1,
            left: MAP_MARGINS.A1,
            top: MAP_MARGINS.A1,
        },
    },
    A2: {
        landscape: {
            right: 7.5 + MAP_MARGINS.A2,
            bottom: MAP_MARGINS.A2,
            left: MAP_MARGINS.A2,
            top: MAP_MARGINS.A2,
        },
        portrait: {
            right: MAP_MARGINS.A2,
            bottom: 7.5 + MAP_MARGINS.A2,
            left: MAP_MARGINS.A2,
            top: MAP_MARGINS.A2,
        },
    },
    A3: {
        landscape: {
            right: 7 + MAP_MARGINS.A3,
            bottom: MAP_MARGINS.A3,
            left: MAP_MARGINS.A3,
            top: MAP_MARGINS.A3,
        },
        portrait: {
            right: MAP_MARGINS.A3,
            bottom: 7 + MAP_MARGINS.A3,
            left: MAP_MARGINS.A3,
            top: MAP_MARGINS.A3,
        },
    },
    A4: {
        landscape: {
            right: 5 + MAP_MARGINS.A4,
            bottom: MAP_MARGINS.A4,
            left: MAP_MARGINS.A4,
            top: MAP_MARGINS.A4,
        },
        portrait: {
            right: MAP_MARGINS.A4,
            bottom: 5 + MAP_MARGINS.A4,
            left: MAP_MARGINS.A4,
            top: MAP_MARGINS.A4,
        },
    },
    // A5 is currently not supported by ol-print-layout-control
    // "A5": {
    //     "landscape": {right: 3},
    //     "portrait": {bottom: 3}
    // },
    LEGAL: {
        landscape: {
            right: 5 + MAP_MARGINS.LEGAL,
            bottom: MAP_MARGINS.LEGAL,
            left: MAP_MARGINS.LEGAL,
            top: MAP_MARGINS.LEGAL,
        },
        portrait: {
            right: MAP_MARGINS.LEGAL,
            bottom: 5 + MAP_MARGINS.LEGAL,
            left: MAP_MARGINS.LEGAL,
            top: MAP_MARGINS.LEGAL,
        },
    },
    // TABLOID is the same as LEDGER
    TABLOID: {
        landscape: {
            right: 7 + MAP_MARGINS.TABLOID,
            bottom: MAP_MARGINS.TABLOID,
            left: MAP_MARGINS.TABLOID,
            top: MAP_MARGINS.TABLOID,
        },
        portrait: {
            right: MAP_MARGINS.TABLOID,
            bottom: 7 + MAP_MARGINS.TABLOID,
            left: MAP_MARGINS.TABLOID,
            top: MAP_MARGINS.TABLOID,
        },
    },
    LETTER: {
        landscape: {
            right: 5 + MAP_MARGINS.LETTER,
            bottom: MAP_MARGINS.LETTER,
            left: MAP_MARGINS.LETTER,
            top: MAP_MARGINS.LETTER,
        },
        portrait: {
            right: MAP_MARGINS.LETTER,
            bottom: 5 + MAP_MARGINS.LETTER,
            left: MAP_MARGINS.LETTER,
            top: MAP_MARGINS.LETTER,
        },
    },
};

export {
    SKETCH_MAP_MARGINS,
};
