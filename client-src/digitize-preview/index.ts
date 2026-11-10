import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";

import { addLayerSwitcherControl, createMap, } from "../shared/map/map.js";
import {
    getSanitizedLayerParam,
    getUUIDFromURL,
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
    //TODO add error handling
    setProcessingOverlay(map, true);
    const progressTimer = startProgressTimer();
    return PollUntilValid.poll(url, validateFn, 1000, onValid, onProgress);

    function validateFn(response: Response) {
        // valid once the status is 200
        return response.status === 200;
    }

    function onProgress(response: Response, result: VectorResultsStatusResponseJson) {
        if (result.errors) console.log(">>> PROGRESS ERRORS", result.errors);
        const { current, total } = result.info;
        showProgress(current, total, result.status);
    }

    function onValid(response: Response, result: VectorResultsStatusResponseJson) {
        if (result.errors) console.log(">>> FINAL ERRORS", result.errors);
        if (result.href) addGeoJSONPreviewLayer(map, result.href);
        setProcessingOverlay(map, false);
        stopProgressTimer(progressTimer);
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
    const map = createMap("map", center, undefined, layer);

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
