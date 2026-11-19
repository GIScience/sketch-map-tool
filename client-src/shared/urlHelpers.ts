import { ORIENTATION, PAPER_FORMAT } from "@giscience/ol-print-layout-control";
import type { Coordinate } from "ol/coordinate";
import type { Extent } from "ol/extent";

export type BaselayerType = "OSM" | "ESRI:World_Imagery" | `oam:${string}`;
export type PaperFormat = typeof PAPER_FORMAT[keyof typeof PAPER_FORMAT];

declare const uuid4Brand: unique symbol;

/** A string validated as an RFC 9562 version-4 UUID. */
export type UUID4 = `${string}-${string}-${string}-${string}-${string}` & {
    readonly [uuid4Brand]: true;
};

const UUID4_REGEX =
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** Type guard: narrows `value` to `UUID4` if it is a valid v4 UUID. */
export function isUUID4(value: string): value is UUID4 {
    return UUID4_REGEX.test(value);
}

/** Values are serialized with `String()`, e.g. arrays become comma separated lists */
type UrlParamValue = string | number | readonly number[] | UUID4;

/**
 * This function will return the first UUID v4 string that can be found in the current location URL
 */
function getUUIDFromURL(): string {
    const UUID_V4_PATTERN = /[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/i;
    const match = location.pathname.match(UUID_V4_PATTERN);
    if (!match) throw new Error(`No UUID found in URL path: ${location.pathname}`);
    return match[0];
}

function getUUIDFromSearchParam(param: string): UUID4 {
    const url = new URL(window.location.href);
    const value = url.searchParams.get(param);
    if (!value) throw new Error(`Parameter '${param}' is not present in the URL.)`);
    if (!isUUID4(value)) {
        throw new Error("Parameter value is not a valid UUID4.")
    }
    return value;
}

const setUrlSearchParams = (params: Record<string, UrlParamValue>) => {
    const url = new URL(window.location.href);
    Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, String(value));
    });
    window.history.replaceState({}, "", url);
};

const updateQueryParam = (paramName: string, newValue: UrlParamValue) => {
    const url = new URL(window.location.href);
    url.searchParams.set(paramName, String(newValue));
    window.history.replaceState({}, "", url);
};

let lastChangeTime = 0;
let debounceTimeout: ReturnType<typeof setTimeout> | undefined;

const updateQueryParamWithConditionalDebounce = (paramName: string, value: UrlParamValue) => {
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

function getSanitizedLayerParam(baselayerArg: string | null | undefined): BaselayerType {
    if (baselayerArg === "ESRI:World_Imagery") return baselayerArg;
    if (baselayerArg?.startsWith("oam:")) return baselayerArg as `oam:${string}`;
    return "OSM"; // default
}

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

    let center: Coordinate = [966253.1800856147, 6344703.99262965];
    if (centerArg != null) {
        const centerCoords = centerArg.split(",").map(Number.parseFloat);
        if (centerCoords.length === 2 && centerCoords.every(Number.isFinite)) {
            center = centerCoords;
        }
    }

    let zoom = 15;
    if (zoomArg != null) {
        zoom = Number(zoomArg) || zoom;
    }

    const layer = getSanitizedLayerParam(baselayerArg);

    let orientation: ORIENTATION = ORIENTATION.LANDSCAPE;
    if (orientationArg != null) {
        orientation = ORIENTATION[orientationArg.toUpperCase() as keyof typeof ORIENTATION] || orientation;
    }

    let format: PaperFormat = PAPER_FORMAT.A4;
    if (formatArg != null) {
        const key = formatArg.toUpperCase();
        // TODO: enable A0. Blocker is backend support of A0
        if (key !== "A0" && key in PAPER_FORMAT) {
            format = PAPER_FORMAT[key as keyof typeof PAPER_FORMAT];
        }
    }
    return {
        center, zoom, layer, orientation, format,
    };
}


/**
 * Parses a bbox URL parameter of the form "minX,minY,maxX,maxY" in EPSG:3857.
 * Returns the fallback if the parameter is missing, does not consist of exactly four numbers,
 * any value lies outside the EPSG:3857 extent, or the values are not ordered (min < max).
 */
function getSanitizedBboxParam(bboxArg: string | null | undefined): Extent {
    /** Half the circumference of the WGS84 ellipsoid: the bounds of EPSG:3857 on both axes */
    const WEB_MERCATOR_MAX = 20037508.342789244;
    const fallback: Extent = [-WEB_MERCATOR_MAX, -WEB_MERCATOR_MAX, WEB_MERCATOR_MAX, WEB_MERCATOR_MAX];

    if (!bboxArg) return fallback;

    const parts = bboxArg.split(",").map((part) => part.trim());
    // reject empty parts: Number("") would silently become 0
    if (parts.length !== 4 || parts.includes("")) return fallback;

    const values = parts.map(Number);
    if (!values.every((value) => Number.isFinite(value) && Math.abs(value) <= WEB_MERCATOR_MAX)) return fallback;

    const [minX, minY, maxX, maxY] = values;
    if (minX >= maxX || minY >= maxY) return fallback;

    return [minX, minY, maxX, maxY];
}

export {
    getSanitizedLayerParam,
    getSanitizedBboxParam,
    getSanitizedUrlSearchParams,
    getUUIDFromURL,
    getUUIDFromSearchParam,
    setUrlSearchParams,
    updateQueryParam,
    updateQueryParamWithConditionalDebounce,
};
