// TODO: move UUID URL thingy from DOM helper to here

import { PAPER_FORMAT, ORIENTATION } from "@giscience/ol-print-layout-control";

/**
 * This function will return the first UUID v4 string that can be found in the current location URL
 * @returns {string}
 */
function getUUIDFromURL() {
    const UUID_V4_PATTERN = /[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/i;
    // eslint-disable-next-line no-restricted-globals
    return location.pathname.match(UUID_V4_PATTERN)[0];
}

const setUrlSearchParams = (params) => {
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

    // type BaselayerType = "OSM" | "ESRI:World_Imagery" | `oam:${string}`
    let layer = "OSM";
    if (baselayerArg != null) {
        switch (true) {
            case baselayerArg === "ESRI:World_Imagery":
                layer = baselayerArg;
                break;
            case baselayerArg.startsWith("oam:"):
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
        // TODO: enable A0. Blocker is backend support of A0
        delete PAPER_FORMAT.A0
        format = PAPER_FORMAT[formatArg.toUpperCase()] || format;
    }
    return {
        center, zoom, layer, orientation, format,
    };
}

export {
    getSanitizedUrlSearchParams,
    getUUIDFromURL,
    setUrlSearchParams,
    updateQueryParam,
    updateQueryParamWithConditionalDebounce,
};
