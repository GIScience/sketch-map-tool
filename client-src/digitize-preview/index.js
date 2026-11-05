import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";

import { addLayerSwitcherControl, createMap, } from "./map.js";
import {
    getSanitizedLayerParam,
    getUUIDFromURL,
    PollUntilValid,
    setUrlSearchParams
} from "../shared";
import { Tile } from "ol/layer";
import { XYZ } from "ol/source";
import { OpenAerialMapService } from "./openaerialmapService";
import { transformExtent } from "ol/proj";
import { intersects } from "ol/extent";
import { UserLayerControl } from "./userLayerControl/userLayerControl";
import { unit } from "mathjs";
import * as olExtent from "ol/extent";
import VectorSource from "ol/source/Vector";
import { GeoJSON } from "ol/format";
import VectorLayer from "ol/layer/Vector";


/**
 * This is the main script which is invoked after DOM Content of digitize-preview.html is loaded.
 */

// get all relevant params in case a permalink has been used to set the application state
const searchParams = new URLSearchParams(window.location.search);
//TODO check layer names not differ between frontend and backend
console.log("original layer", searchParams.get("layer"))
const layer = getSanitizedLayerParam(searchParams.get("layer"));
const bbox = (searchParams.get("bbox") ?? "-180, -80, 180, 80").split(",").map(Number); //TODO proper sanitize
//TODO transform extent (bbox) to map projection, then init the map there
console.log(layer, bbox);
// invalid params will be replaced by sanitized ones
setUrlSearchParams({
    layer, bbox,
});

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;

const map = await createPreviewMap();
setProcessingOverlay(map, true);
const timer = startProgressTimer();
pollVectorResults(vectorResultsUrl).then(getVectorDownloadUrl).then((href) => addGeoJSONPreviewLayer(map, href))
    .then(() => {
        setProcessingOverlay(map, false);
        stopProgressTimer(timer);
    });

async function pollVectorResults(url) {
    //TODO add error and progress handling
    return PollUntilValid.poll(url, validateFn, 1000, undefined, onProgress);

    function validateFn(response) {
        // valid once the status is 200
        return response.status === 200;
    }

    async function onProgress(response){
        const result = await response.json();
        const { current, total } = result.info;
        showProgress(current, total, result.status);
    }
}

async function getVectorDownloadUrl(response) {
    const result = await response.json();
    const { href } = result;
    return href;
}

async function addAllLayerSwitchers(map) {
    const layerSwitcher = addLayerSwitcherControl(map);

    const layerswitcherSlot = document.querySelector(".layerswitcher #slot");

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

    // bindFormToLayerSwitcherControl(layerSwitcher, userLayerControl);
    // add additional layers
    if (layer.startsWith("oam:")) {
        const oamItemId = layer.replace("oam:", "");
        await addOAMLayer(oamItemId, map, layerSwitcher);
    }

    // OAM Metadata Dialog Handling
    userLayerControl.on("info", handleUserLayerControlInfoEvent);

    document.getElementById("oam-info-ok-button").addEventListener("click", () => {
        document.getElementById("oam-info-dialog").close();
    });

    document.getElementById("oam-info-close-button").addEventListener("click", () => {
        document.getElementById("oam-info-dialog").close();
    });

    // OAM Add Dialog Handling
    document.getElementById("oam-add-button").addEventListener("click", async () => {
        const oamItemIdInput = document.getElementById("oam-item-id-input");
        const oamInvalidIdMessage = document.getElementById("oam-invalid-id-message");
        const oamPrgressBar = document.getElementById("oam-progress-bar");
        try {
            if (oamItemIdInput.value.length === 0) {
                throw Error("Empty input not allowed.")
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

function addGeoJSONPreviewLayer(map, href) {
    const vectorSource = new VectorSource({
        format: new GeoJSON({
            dataProjection: "EPSG:4326", featureProjection: "EPSG:3857"
        }),
        url: href,
    });

    const vectorLayer = new VectorLayer({
        name: "Sketch Map Results",
        source: vectorSource,
        overlay: true,
        zIndex: Infinity
    });

    map.addLayer(vectorLayer);
}

async function createPreviewMap(href) {
    console.log("TODO: CREATE PREVIEW MAP", await href);
    console.log("Layer:", layer);
    const center = olExtent.getCenter(bbox)
    console.log("BBOX:", bbox, center);

    //Base Map from original sketchmap
    const map = createMap("map", center, undefined, layer);

    await addAllLayerSwitchers(map);

    //TODO add AOI / BBOX as layer

    //add GeoJSON Layer
    if (href) addGeoJSONPreviewLayer(map, href);

    return map;
}

function setProcessingOverlay(map, visible) {
    // document.getElementById("map-loading").hidden = !visible;
    document.getElementById("map-loading").classList.toggle("is-hidden", !visible);
    const target = map.getTargetElement();
    target.inert = visible;
    // target.setAttribute("aria-busy", String(visible));
}

function showProgress( parts, total, message ) {
    const progressPercent = (parts/total) * 100;
    console.log(progressPercent, message);
    document.getElementById("load-parts").textContent = `${parts}/${total}`;
    // start with infinite progress bar (without value), after first result switch to percent
    if (typeof progressPercent === "number" && progressPercent > 0) {
        document.getElementById("load-progress").value = progressPercent;
        document.getElementById("load-percent").textContent = `${Math.round(progressPercent)} %`;
    }
    if (message) document.getElementById("load-message").textContent = message;
}

function startProgressTimer(){
    const start = Date.now();
    return setInterval(() => {
        const s = Math.floor((Date.now() - start) / 1000);
        document.getElementById("load-elapsed").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    }, 1000);
}

function stopProgressTimer(timerReference) {
    clearInterval(timerReference);
}

export async function addOAMLayer(oamItemId, map, layerSwitcher) {

    const oamLayerName = `oam:${oamItemId}`;
    try {
        const metadata = await OpenAerialMapService.getMetadata(oamItemId);
        console.log(metadata);
        console.log("layerswitcher", layerSwitcher);
        layerSwitcher.activateNextLayer();
        console.log(">>>>>>>>after activateNextLayer")
        layerSwitcher.suspend();

        const oamBaselayer = new Tile({
            name: oamLayerName,
            visible: true,
            source: new XYZ({
                url: OpenAerialMapService.getTileUrl(oamItemId),
                attributions: OpenAerialMapService.getMapAttributionFromMetadata(metadata),
            }),
            background: "slategrey",
            ulc_visible: true,
            ulc_buttonImageUrl: OpenAerialMapService.getThumbnailUrl(oamItemId, 256),
            // ls_visible: true,
            // ls_label: "OpenAerialMap",
            // ls_class: "esri-world-imagery",
        });

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

document.getElementById("oam-close-button").addEventListener("click", () => {
    closeOamDialog()
});

document.getElementById("oam-cancel-button").addEventListener("click", () => {
    closeOamDialog()
});

function openOamDialog() {
    document.getElementById("oam-dialog").show();
    document.getElementById("oam-item-id-input").focus();
}

function closeOamDialog() {
    // reset state
    document.getElementById("oam-invalid-id-message").classList.add("hidden");
    document.getElementById("oam-item-id-input").removeAttribute("aria-invalid")
    document.getElementById("oam-dialog").close();

}

async function handleUserLayerControlInfoEvent(event) {
    const infoDialog = document.getElementById("oam-info-dialog");
    const oamItemId = event.target.get("activeLayer").get("name").replace("oam:", "");

    // open the dialog
    infoDialog.show();

    // load preview image
    infoDialog.querySelector("img").setAttribute("src", OpenAerialMapService.getThumbnailUrl(oamItemId, 256));

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
    document.getElementById("title").textContent = title;
    document.getElementById("date").textContent = new Date(start_datetime).toLocaleDateString();
    document.getElementById("resolution").textContent = unit(resolution, "m").toBest(["cm", "m"]).format({
        notation: "auto",
        precision: 2
    });
    document.getElementById("provider").textContent = producer;
    document.getElementById("platform").textContent = platform.toUpperCase();
    document.getElementById("license").textContent = license;
    document.getElementById("itemId").textContent = oamItemId;
}
