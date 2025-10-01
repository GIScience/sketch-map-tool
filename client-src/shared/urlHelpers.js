// TODO: move UUID URL thingy from DOM helper to here

import { PAPER_FORMAT, ORIENTATION } from "@giscience/ol-print-layout-control";


const setAllQueryParam = (params) => {
    const url = new URL(window.location);
    Object.keys(params).forEach((key) => {
        url.searchParams.set(key, params[key]);
    });
    window.history.replaceState({}, "", url);
};

const updateQueryParam = (paramName, newValue) => {
    const url = new URL(window.location);
    url.searchParams.set(paramName, newValue);
    window.history.replaceState({}, "", url);
};

let lastChangeTime = 0;
let debounceTimeout = null;

const updateQueryParamWithConditionalDebounce = (paramName, value) => {
    const now = Date.now();
    const timeSinceLastChange = now - lastChangeTime;

    if (timeSinceLastChange < 300) {
        // If last change was recent, debounce
        // to avoid making too many calls to Location or History APIs within a short timeframe
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            updateQueryParam(paramName, value);
            lastChangeTime = Date.now();
        }, 300);
    } else {
        // Otherwise, update immediately
        updateQueryParam(paramName, value);
        lastChangeTime = now;
    }
};


function getSanitizedUrlSearchParams() {
    // Retrieve potentially given map and print layout parameter from URL
    // (e.g. from a bookmarked selection)
    //
    // TODO: Move default values to own module or configuration file
    //
    const searchParams = new URLSearchParams(window.location.search);

    const centerArg = searchParams.get("center");
    const zoomArg = searchParams.get("zoom");
    const baselayerArg = searchParams.get("layer");
    const orientationArg = searchParams.get("orientation");
    const formatArg = searchParams.get("format");

    let center = [966253.1800856147, 6344703.99262965];
    if (centerArg != null) {
        const centerCoords = centerArg.split(",");
        if (centerCoords.length === 2) {
            center = [parseFloat(centerCoords[0]), parseFloat(centerCoords[1])] || center;
        }
    }

    let zoom = 15;
    if (zoomArg != null) {
        zoom = Number(zoomArg) || zoom;
    }

    // type BaselayerType = "OSM" | "ESRI:World_Imagery"
    let layer = "OSM";
    if (baselayerArg != null) {
        switch (baselayerArg) {
            case "ESRI:World_Imagery":
                layer = baselayerArg;
                break;
            default:
                layer = "OSM";
        }
    }

    let orientation = ORIENTATION.LANDSCAPE;
    if (orientationArg != null) {
        orientation = ORIENTATION[orientationArg.toUpperCase()] || orientation;
    }

    let format = PAPER_FORMAT.A4;
    if (formatArg != null) {
        format = PAPER_FORMAT[formatArg.toUpperCase()] || format;
        // TODO handle A0
    }
    return {
        center, zoom, layer, orientation, format,
    };
}

export {
    updateQueryParamWithConditionalDebounce,
    updateQueryParam,
    setAllQueryParam,
    getSanitizedUrlSearchParams,
};
