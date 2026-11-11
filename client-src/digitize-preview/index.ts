import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";

import { addLayerSwitcherControl, createMap, } from "../shared/map/map.js";
import {
    getSanitizedLayerParam,
    getUUIDFromURL,
    NetworkError,
    PollUntilValid,
    setUrlSearchParams
} from "../shared";
import { Tile } from "ol/layer";
import { XYZ } from "ol/source";
import { OpenAerialMapService } from "../shared/map/openaerialmapService";
import { transformExtent } from "ol/proj";
import * as olExtent from "ol/extent";
import { intersects } from "ol/extent";
import { UserLayerControl } from "../shared/map/userLayerControl/userLayerControl";
import { unit } from "mathjs";
import VectorSource from "ol/source/Vector";
import { GeoJSON } from "ol/format";
import VectorLayer from "ol/layer/Vector";
import { Feature, Map } from "ol";
import { fromExtent } from "ol/geom/Polygon";
import { Stroke, Style } from "ol/style";
import { createSimpleStyleFunction } from "./ol-simplestyle-1.1.0";
import type BaseEvent from "ol/events/Event";
import type { LayerSwitcher } from "../shared/map/ol-LayerSwitcherControl";


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
        document.querySelector<HTMLElement>("#load-message")!.textContent = `Connection lost, retrying (${retry}/${maxRetries})…`;
    }

    function validateFn(response: Response) {
        // valid once the status is 200
        return response.status === 200;
    }

    function onProgress(response: Response, result: VectorResultsStatusResponseJson) {
        // show only a summary (error type + count), the details are listed below the map when finished
        showLoadErrorSummary(result.errors ?? []);
        const { current, total } = result.info;
        showProgress(current, total, result.status);
    }

    function onValid(response: Response, result: VectorResultsStatusResponseJson) {
        // partial success: keep the errors visible below the map after the overlay is gone
        showProcessingErrorsBelowMap(result.errors ?? []);
        if (result.href) addGeoJSONPreviewLayer(map, result.href);
        setProcessingOverlay(map, false);
        stopProgressTimer(progressTimer);
    }

    async function onError(response: Response) {
        // 422 (task failed), 500 or others: only show the HTTP status in a single line in the overlay
        stopProgressTimer(progressTimer);
        showProcessingError(`${response.status} ${response.statusText}`.trim());

        if (response.status === 422) {
            // all sketch maps failed: list the errors below the map with a hint to check the uploads
            let errors: string[] = [];
            if (response.headers.get("Content-Type")?.includes("application/json")) {
                const result: Partial<VectorResultsStatusResponseJson> = await response.json();
                errors = result.errors ?? [];
            }
            showProcessingErrorsBelowMap(errors, true);
        } else if (response.status >= 500) {
            // unexpected server error: show details the user can send to the support
            showServerErrorDetails(response);
        }
    }
}

async function addAllLayerSwitchers(map: Map) {
    const layerSwitcher = addLayerSwitcherControl(map);

    const layerswitcherSlot = document.querySelector<HTMLElement>(".layerswitcher #slot")!;

    const userLayerControl = new UserLayerControl({ target: layerswitcherSlot });
    map.addControl(userLayerControl);
    userLayerControl.initialize();

    userLayerControl.on("new-layer", openOamDialog);

    // keep the current layer in layerswitcher to toggle back from OAM Layer
    userLayerControl.on("beforeactivate", () => {
        layerSwitcher.activateNextLayer();
    });
    // switch back to the layer you came from when removing OAM Layer
    userLayerControl.on("close", () => {
        layerSwitcher.activateNextLayer();
    })

    // add additional layers
    if (layer.startsWith("oam:")) {
        const oamItemId = layer.replace("oam:", "");
        await addOAMLayer(oamItemId, map, layerSwitcher);
    }

    // OAM Metadata Dialog Handling
    userLayerControl.on("info", handleUserLayerControlInfoEvent);

    const oamInfoDialog = document.querySelector<HTMLDialogElement>("#oam-info-dialog")!;

    document.querySelector<HTMLButtonElement>("#oam-info-ok-button")!.addEventListener("click", () => {
        oamInfoDialog.close();
    });

    document.querySelector<HTMLButtonElement>("#oam-info-close-button")!.addEventListener("click", () => {
        oamInfoDialog.close();
    });

    // OAM Add Dialog Handling
    document.querySelector<HTMLButtonElement>("#oam-add-button")!.addEventListener("click", async () => {
        const oamItemIdInput = document.querySelector<HTMLInputElement>("#oam-item-id-input")!;
        const oamInvalidIdMessage = document.querySelector<HTMLElement>("#oam-invalid-id-message")!;
        const oamPrgressBar = document.querySelector<HTMLProgressElement>("#oam-progress-bar")!;
        try {
            if (oamItemIdInput.value.length === 0) {
                throw new Error("Empty input not allowed.")
            }
            oamPrgressBar.classList.remove("hidden");
            await addOAMLayer(oamItemIdInput.value, map, layerSwitcher);
            closeOamDialog();
        } catch (error) {
            console.error(error);
            oamInvalidIdMessage.classList.remove("hidden");
            oamItemIdInput.setAttribute("aria-invalid", "true");
        } finally {
            oamPrgressBar.classList.add("hidden");
        }
    });

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
        style: createSimpleStyleFunction({ markerStyle: "pin", defaultShape: "circle" }),
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

    await addAllLayerSwitchers(map);

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

function showProgress(parts: number, total: number, message?: string) {
    const progressPercent = (parts/total) * 100;
    console.log(progressPercent, message);
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
function showProcessingError(message: string) {
    const overlay = document.querySelector<HTMLElement>("#map-loading")!;
    overlay.classList.add("has-error");
    overlay.setAttribute("role", "alert");
    overlay.querySelector<HTMLElement>(".loading-title")!.textContent = "Marking Detection failed";

    // single line without count and without the hint
    showLoadErrorRows([createErrorRow(message)], false);
}

/**
 * Shows a summary of the errors in the loading card: one row per error type with its count
 * and a hint that the full list is shown below the map once processing has finished.
 * The error type is the part of the message before the first colon (or the whole message).
 */
function showLoadErrorSummary(messages: string[]) {
    const counts = new globalThis.Map<string, number>();
    for (const message of messages) {
        const colon = message.indexOf(":");
        const name = (colon === -1 ? message : message.slice(0, colon)).trim();
        counts.set(name, (counts.get(name) ?? 0) + 1);
    }
    const rows = [...counts].map(([name, count]) => createErrorRow(name, count));
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
function showProcessingErrorsBelowMap(messages: string[], allFailed = false) {
    setListItems(document.querySelector<HTMLUListElement>("#processing-errors-list")!, messages);
    document.querySelector<HTMLElement>("#processing-errors-partial")!.hidden = allFailed;
    document.querySelector<HTMLElement>("#processing-errors-all-failed")!.hidden = !allFailed;
    document.querySelector<HTMLElement>("#processing-errors")!.hidden = messages.length === 0 && !allFailed;
}

/**
 * Shows a message box below the map with details about the failed request,
 * which the user can send to the Sketch Map Tool support (also as prefilled mailto link).
 */
function showServerErrorDetails(response: Response) {
    const details = [
        `ID: ${getUUIDFromURL()}`,
        `Request: ${response.url}`,
        `Status: ${response.status} ${response.statusText}`.trim(),
        `Time: ${new Date().toISOString()}`,
        `Page: ${window.location.href}`,
        `Browser: ${navigator.userAgent}`,
    ].join("\n");

    document.querySelector<HTMLElement>("#server-error-details")!.textContent = details;

    const mailLink = document.querySelector<HTMLAnchorElement>("#server-error-mail")!;
    const mailAddress = mailLink.href.replace(/^mailto:/, "").split("?")[0];
    const subject = `Sketch Map Tool: Error ${response.status} during Marking Detection`;
    mailLink.href = `mailto:${mailAddress}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(details)}`;

    document.querySelector<HTMLElement>("#server-error")!.hidden = false;
}

/**
 * Replaces the items of the list with one <li> per message.
 */
function setListItems(list: HTMLUListElement, messages: string[]) {
    list.replaceChildren(...messages.map((message) => {
        const item = document.createElement("li");
        item.textContent = message;
        return item;
    }));
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

export async function addOAMLayer(oamItemId: string, map: Map, layerSwitcher: LayerSwitcher) {

    const oamLayerName = `oam:${oamItemId}`;
    try {
        const metadata = await OpenAerialMapService.getMetadata(oamItemId);
        console.log(metadata);
        layerSwitcher.activateNextLayer();
        layerSwitcher.suspend();

        const oamBaselayer = new Tile({
            visible: true,
            source: new XYZ({
                url: OpenAerialMapService.getTileUrl(oamItemId),
                attributions: OpenAerialMapService.getMapAttributionFromMetadata(metadata),
            }),
            background: "slategrey",
        });
        oamBaselayer.set("name", oamLayerName, true);
        oamBaselayer.set("ulc_visible", true, true);
        oamBaselayer.set("ulc_buttonImageUrl", OpenAerialMapService.getThumbnailUrl(oamItemId, 256), true);

        map.addLayer(oamBaselayer);

        const projectedBbox = transformExtent(metadata.bbox, "EPSG:4326", map.getView().getProjection());
        if (!intersects(projectedBbox, map.getView().calculateExtent())) {
            map.getView().fit(projectedBbox);
        }
    } catch (error) {
        console.log(`The OpenAerialMap Item ${oamItemId} could not be loaded.`, error);
        throw error;
    }

}

document.querySelector<HTMLButtonElement>("#oam-close-button")!.addEventListener("click", () => {
    closeOamDialog()
});

document.querySelector<HTMLButtonElement>("#oam-cancel-button")!.addEventListener("click", () => {
    closeOamDialog()
});

function openOamDialog() {
    document.querySelector<HTMLDialogElement>("#oam-dialog")!.show();
    document.querySelector<HTMLInputElement>("#oam-item-id-input")!.focus();
}

function closeOamDialog() {
    // reset state
    document.querySelector<HTMLElement>("#oam-invalid-id-message")!.classList.add("hidden");
    document.querySelector<HTMLInputElement>("#oam-item-id-input")!.removeAttribute("aria-invalid");
    document.querySelector<HTMLDialogElement>("#oam-dialog")!.close();

}

async function handleUserLayerControlInfoEvent(event: BaseEvent) {
    const infoDialog = document.querySelector<HTMLDialogElement>("#oam-info-dialog")!;
    const oamItemId = event.target.get("activeLayer").get("name").replace("oam:", "");

    // open the dialog
    infoDialog.show();

    // load preview image
    infoDialog.querySelector("img")!.setAttribute("src", OpenAerialMapService.getThumbnailUrl(oamItemId, 256));

    // load and show the metadata properties
    const metadata = await OpenAerialMapService.getMetadata(oamItemId);
    const {
        title,
        start_datetime,
        gsd: resolution,
        "oam:producer_name": producer,
        "oam:platform_type": platform,
        license,
    } = metadata.properties;

    //set table properties
    document.querySelector<HTMLTableCellElement>("#title")!.textContent = title;
    document.querySelector<HTMLTableCellElement>("#date")!.textContent = new Date(start_datetime).toLocaleDateString();
    document.querySelector<HTMLTableCellElement>("#resolution")!.textContent = unit(resolution, "m").toBest(["cm", "m"]).format({
        notation: "auto",
        precision: 2
    });
    document.querySelector<HTMLTableCellElement>("#provider")!.textContent = producer;
    document.querySelector<HTMLTableCellElement>("#platform")!.textContent = platform.toUpperCase();
    document.querySelector<HTMLTableCellElement>("#license")!.textContent = license;
    document.querySelector<HTMLTableCellElement>("#itemId")!.textContent = oamItemId;
}
