import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";

import { addLayerSwitcherControl, createMap, } from "../shared/map/map.js";
import {
    getSanitizedLayerParam,
    getUUIDFromURL,
    NetworkError,
    PollUntilValid,
    setListItems,
    setUrlSearchParams
} from "../shared";
import * as olExtent from "ol/extent";
import { addOAMLayer, addUserLayerControl, getOAMItemId, isOAMLayer } from "../shared/map/oamLayer";
import VectorSource from "ol/source/Vector";
import { GeoJSON } from "ol/format";
import VectorLayer from "ol/layer/Vector";
import { Feature, Map } from "ol";
import { fromExtent } from "ol/geom/Polygon";
import { Stroke, Style } from "ol/style";
import { createSimpleStyleFunction } from "./ol-simplestyle-1.1.0";
import { groupByMessageCount } from "../shared/errorHelpers";


/**
 * This is the main script which is invoked after DOM Content of digitize-preview.html is loaded.
 */

// get all relevant params in case a permalink has been used to set the application state
const searchParams = new URLSearchParams(window.location.search);
const layer = getSanitizedLayerParam(searchParams.get("layer"));
const bbox = (searchParams.get("bbox") ?? "-20037508.34, -15538711.10, 20037508.34, 15538711.10").split(",").map(Number); //TODO proper sanitize

// invalid params will be replaced by sanitized ones
setUrlSearchParams({
    layer, bbox,
});

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;

const previewMap = await createPreviewMap();
await pollVectorResults(vectorResultsUrl, previewMap);

/** JSON body of the /api/status/{uuid}/vector-results endpoint */
interface VectorResultsStatusResponseJson {
    id: string;
    status: string;
    type: "vector-results";
    info: { current: number; total: number };
    errors?: string[];
    href?: string;
    msg?: string;
}

const enum ResultStatus {
    Success = "SUCCESS",
    PartialSuccess = "PARTIAL_SUCCESS",
    Failure = "FAILURE"
    //TODO add all others
}

async function pollVectorResults(url: string, map: Map) {
    setProcessingOverlay(map, true);
    const progressTimer = startProgressTimer();
    try {
        // retries with backoff of 1, 2, 4, 8, 16 s: gives up after ~30 s without connection
        return await PollUntilValid.poll(url, validateFn, 1000, onValid, onProgress, onError, {
            maxNetworkRetries: 5,
            onNetworkRetry,
        });
    } catch (error) {
        console.error(error);
        stopProgressTimer(progressTimer);
        // NetworkError: no response was received at all after all retries
        // (offline, DNS failure, server not reachable, connection reset, request blocked by browser/extension).
        // Other errors are thrown in the callbacks (e.g. invalid JSON body or a bug).
        showProcessingError(error instanceof NetworkError
            ? "Network error.\nPlease check your internet connection."
            : "Unexpected error.\nThis may be a bug.");
    }

    function onNetworkRetry(retry: number, maxRetries: number) {
        const message = `Connection lost, retrying (${retry}/${maxRetries})…`
        showLoadErrorRows([createErrorRow(message)], false);
    }

    function validateFn(response: Response) {
        // valid once the status is 200
        return response.status === 200;
    }

    function onProgress(response: Response, result: VectorResultsStatusResponseJson) {
        // show only a summary (error type + count), the details are listed below the map when finished
        showLoadErrorSummary(result.errors ?? []);
        const { current, total } = result.info;
        updateProgress(current, total, result.status);
    }

    function onValid(response: Response, result: VectorResultsStatusResponseJson) {
        setProcessingOverlay(map, false);
        stopProgressTimer(progressTimer);
        if (result.href) addGeoJSONPreviewLayer(map, result.href);

        // partial success: keep the errors visible below the map after the overlay is gone
        if (result.status === ResultStatus.PartialSuccess) {
            showProcessingErrorsBelowMap(result.errors ?? [], result.msg, false);
        }

    }

    function onError(response: Response, result?: Partial<VectorResultsStatusResponseJson>) {
        if (result?.status) updateProgress(result?.info?.current ?? 0, result?.info?.total ?? 0, result.status);
        // 422 (task failed), 500 or others: only show the HTTP status in a single line in the overlay
        stopProgressTimer(progressTimer);
        // showProcessingError(`${response.status} ${response.statusText}`.trim());

        if (String(response.status).startsWith("4")) {
            // all sketch maps failed
            // remove error messages in map-loading error-box
            showProcessingError();
            // list the errors below the map with a hint to check the uploads
            showProcessingErrorsBelowMap(result?.errors ?? [], result?.msg, true);
        } else /*if (response.status >= 500)*/ {
            showProcessingError();
            // unexpected server error: show details the user can send to the support
            showServerErrorDetails(response);
        }
    }
}

// eslint-disable-next-line @typescript-eslint/no-shadow
function addBboxPreviewLayer(map: Map, bbox: number[]) {
    const vectorSource = new VectorSource({
        features: [new Feature(fromExtent(bbox))]
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource,
        zIndex: Infinity,
        style: new Style({
            stroke: new Stroke({
                color: "#c60427",
                width: 3,
                lineDash: [9, 9],
                lineCap: "butt"
            }),
        })
    });
    vectorLayer.set("name", "Sketch Map Extent", true);
    vectorLayer.set("overlay", true, true);

    map.addLayer(vectorLayer);
    map.getView().fit(bbox, { padding:[30,30,30,30]});
}

function addGeoJSONPreviewLayer(map: Map, href: string) {
    const vectorSource = new VectorSource({
        format: new GeoJSON({
            dataProjection: "EPSG:4326", featureProjection: "EPSG:3857"
        }),
        url: href,
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource,
        style: createSimpleStyleFunction({ markerStyle: "pin", defaults: { "marker-symbol": "circle" }}),
        zIndex: Infinity
    });
    vectorLayer.set("name", "Sketch Map Results", true);
    vectorLayer.set("overlay", true, true);

    map.addLayer(vectorLayer);
}

async function createPreviewMap() {
    console.log("Layer:", layer);
    const center = olExtent.getCenter(bbox)
    console.log("BBOX:", bbox, center);

    //Base Map from original sketchmap
    const map = await createMap("map", center, undefined, layer);

    // add controls
    const layerSwitcher = addLayerSwitcherControl(map);
    addUserLayerControl(map, layerSwitcher);

    if (isOAMLayer(layer)) {
        await addOAMLayer(getOAMItemId(layer), map, layerSwitcher);
    }

    // bbox in EPSG:3857
    if (bbox) addBboxPreviewLayer(map, bbox);

    return map;
}

function setProcessingOverlay(map: Map, visible: boolean) {
    // document.querySelector<HTMLElement>("#map-loading")!.hidden = !visible;
    document.querySelector<HTMLElement>("#map-loading")!.classList.toggle("is-hidden", !visible);
    const target = map.getTargetElement()!;
    target.inert = visible;
    // target.setAttribute("aria-busy", String(visible));
}

function updateProgress(parts: number, total: number, message?: string) {
    const progressPercent = (parts/total) * 100;
    document.querySelector<HTMLElement>("#load-parts")!.textContent = `${parts}/${total}`;
    // start with infinite progress bar (without value), after first result switch to percent
    if (typeof progressPercent === "number" && progressPercent > 0) {
        document.querySelector<HTMLProgressElement>("#load-progress")!.value = progressPercent;
        document.querySelector<HTMLElement>("#load-percent")!.textContent = `${Math.round(progressPercent)} %`;
    }
    if (message) document.querySelector<HTMLElement>("#load-message")!.textContent = message;
}

/**
 * Turns the loading card into an error message. The overlay stays visible,
 * as there are no results to show on the map.
 */
function showProcessingError(message?: string) {
    const overlay = document.querySelector<HTMLElement>("#map-loading")!;
    overlay.classList.add("has-error");
    overlay.setAttribute("role", "alert");
    overlay.querySelector<HTMLElement>(".loading-title")!.textContent = "Marking Detection Failed";

    //clear error messages
    document.querySelector<HTMLElement>("#load-errors-box")!.hidden = true;

    // single line without count and without the hint
    if (message) {
        showLoadErrorRows([createErrorRow(message)], false);
    }
}

/**
 * Shows a summary of the errors in the loading card: one row per error type with its count
 * and a hint that the full list is shown below the map once processing has finished.
 * The error type is the part of the message before the first colon (or the whole message).
 */
function showLoadErrorSummary(messages: string[]) {
    const messageSummaryCount = groupByMessageCount(messages);
    const rows = [...messageSummaryCount].map(([name, count]) => createErrorRow(name, count));
    showLoadErrorRows(rows, true);
}

/**
 * Replaces the rows of the error box in the loading card (hidden if there are no rows).
 */
function showLoadErrorRows(rows: HTMLElement[], showHint: boolean) {
    document.querySelector<HTMLElement>("#load-errors")!.replaceChildren(...rows);
    document.querySelector<HTMLElement>("#load-error-hint")!.hidden = !showHint;
    document.querySelector<HTMLElement>("#load-errors-box")!.hidden = rows.length === 0;
}

/**
 * Creates a row like the ones in .loading-meta: the (truncated) error name left, the count right.
 */
function createErrorRow(name: string, count?: number) {
    const row = document.createElement("div");
    row.className = "row";
    const nameEl = document.createElement("span");
    nameEl.className = "error-name";
    nameEl.textContent = name;
    nameEl.title = name;
    row.append(nameEl);
    if (count !== undefined) {
        const countEl = document.createElement("span");
        countEl.textContent = String(count);
        row.append(countEl);
    }
    return row;
}

/**
 * Shows the errors in a message box below the map.
 * If `allFailed` is true (no sketch map could be processed) the box is shown with a hint
 * to check the uploaded sketch maps, even if there are no error messages.
 * Otherwise, the box is hidden if there are no errors.
 */
function showProcessingErrorsBelowMap(errors: string[], message?: string, allFailed = false) {
    // message to help user
    if (message) document.querySelector<HTMLElement>("#processing-error-msg")!.textContent = message;
    // error details
    setListItems(document.querySelector<HTMLUListElement>("#processing-errors-list")!, errors);
    // hide/show error-box
    document.querySelector<HTMLElement>("#processing-errors")!.hidden = errors.length === 0 && !allFailed;
}

/**
 * Shows a message box below the map with details about the failed request,
 * which the user can send to the Sketch Map Tool support (also as prefilled mailto link).
 * Used to display 500 or any other unhanled error
 */
function showServerErrorDetails(response: Response) {
    const details = [
        `Request: ${response.url}`,
        `Status: ${response.status} ${response.statusText}`.trim(),
    ].join("\n");

    document.querySelector<HTMLElement>("#server-error-details")!.textContent = details;

    const mailLink = document.querySelector<HTMLAnchorElement>("#server-error-mail")!;
    const mailAddress = mailLink.href.replace(/^mailto:/, "").split("?")[0];
    const subject = `Sketch Map Tool: Error ${response.status} during Marking Detection`;
    mailLink.href = `mailto:${mailAddress}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(details)}`;

    document.querySelector<HTMLElement>("#server-error")!.hidden = false;
}

function startProgressTimer(){
    const start = Date.now();
    return setInterval(() => {
        const s = Math.floor((Date.now() - start) / 1000);
        document.querySelector<HTMLElement>("#load-elapsed")!.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    }, 1000);
}

function stopProgressTimer(timerReference: ReturnType<typeof setInterval>) {
    clearInterval(timerReference);
}
