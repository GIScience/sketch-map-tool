import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "ol-geocoder/dist/ol-geocoder.css";
import "./geocoder.css";
import "./create.css";

import {
    addGeocoderControl,
    addLayerSwitcherControl,
    addPrintLayoutControl,
    createMap,
} from "./map.js";
import { bindFormToLayerSwitcherControl, bindFormToPrintLayoutControl } from "./form.js";
import { MessageController } from "./messageController";
import { getSanitizedUrlSearchParams, setUrlSearchParams } from "../shared";
import { Tile } from "ol/layer";
import { XYZ } from "ol/source";
import { OpenAerialMapService } from "./openaerialmapService";
import { transformExtent } from "ol/proj";
import { intersects } from "ol/extent";
import { UserLayerControl } from "./userLayerControl/userLayerControl";


/**
 * This is the main script which is invoked after DOM Content of create.html is loaded.
 */

// get all relevant params in case a permalink has been used to set the application state
const {
    center, zoom, layer, orientation, format,
} = getSanitizedUrlSearchParams();

// invalid params will be replaced by sanitized ones
setUrlSearchParams({
    center, zoom, layer, orientation, format,
});

const map = createMap("map", center, zoom, layer);
const printLayoutControl = addPrintLayoutControl(map, format, orientation);
const messageController = new MessageController();

bindFormToPrintLayoutControl(printLayoutControl, messageController);
addGeocoderControl(map);

const layerSwitcher = addLayerSwitcherControl(map);
// add additional layers
if (layer.startsWith("oam:")) {
    const oamItemId = layer.replace("oam:", "");
    await addOAMLayer(oamItemId);
}
bindFormToLayerSwitcherControl(layerSwitcher);

const layerswitcherSlot = document.querySelector(".layerswitcher #slot");

const userLayerControl = new UserLayerControl({ target: layerswitcherSlot });
map.addControl(userLayerControl);
userLayerControl.on("new-layer", openOamDialog);

// document.getElementById("oam-add-button").addEventListener("click", handleAddOAMLayer);
//
// function handleAddOAMLayer() {
//     // read text field
//     const oamItemId = document.getElementById("oam-itemId").value;
//
//     addOAMLayer(oamItemId);
// }

export async function addOAMLayer(oamItemId) {

    const oamLayerName = `oam:${oamItemId}`;
    try {
        const metadata = await OpenAerialMapService.getMetadata(oamItemId);
        console.log(metadata);

        const oamBaselayer = new Tile({
            name: oamLayerName,
            visible: true,
            source: new XYZ({
                url: OpenAerialMapService.getTileUrl(oamItemId),
                attributions: "OAM"
            }),
            background: "slategrey",
            userlayer: true,
            ls_visible: true,
            ls_label: "OpenAerialMap",
            ls_class: "esri-world-imagery",
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

document.getElementById("oam-add-button").addEventListener("click", async () => {
    const oamItemIdInput = document.getElementById("oam-item-id-input");
    const oamInvalidIdMessage = document.getElementById("oam-invalid-id-message");
    const oamPrgressBar = document.getElementById("oam-progress-bar");
    try {
        oamPrgressBar.classList.remove("hidden");
        await addOAMLayer(oamItemIdInput.value);
        closeOamDialog();
    } catch (error) {
        console.error(error);
        oamInvalidIdMessage.classList.remove("hidden");
        oamItemIdInput.setAttribute("aria-invalid", "true");
    } finally {
        oamPrgressBar.classList.add("hidden");
    }
});

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
