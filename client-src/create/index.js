import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "ol-geocoder/dist/ol-geocoder.css";
import "./geocoder.css";
import "./create.css";

import {
    addGeocoderControl,
    addLayerswitcherControl,
    addPrintLayoutControl,
    createMap,
} from "./map.js";
import { bindFormToLayerSwitcherControl, bindFormToPrintLayoutControl } from "./form.js";
import { MessageController } from "./messageController";

// Retrieve potentially given map center and baselayer from URL (e.g. from a bookmarked selection)
const searchParams = new URLSearchParams(window.location.search);
const centerArg = searchParams.get("center");
const baselayerArg = searchParams.get("layer");

let center = [966253.1800856147, 6344703.99262965];
if (centerArg != null) {
    const centerCoords = centerArg.split(",");
    center = [parseFloat(centerCoords[0]), parseFloat(centerCoords[1])];
}

// type BaselayerType = "OSM" | "ESRI:World_Imagery"
let activeBaselayer;
if (baselayerArg != null) {
    switch (baselayerArg) {
        case "ESRI:World_Imagery":
            activeBaselayer = baselayerArg;
            break;
        default:
            activeBaselayer = "OSM";
    }
}

const map = createMap("map", center, 15, activeBaselayer);

const printLayoutControl = addPrintLayoutControl(map);
const messageController = new MessageController();

bindFormToPrintLayoutControl(printLayoutControl, messageController);
addGeocoderControl(map);
const layerSwitcher = addLayerswitcherControl(map, [
    // Info: names must correspont to name properties of the layers added to the Map in createMap()
    {
        name: "OSM",
        label: "OSM",
        class: "osm",
    },
    {
        name: "ESRI:World_Imagery",
        label: "Satellite",
        class: "esri-world-imagery",
    },
]);
bindFormToLayerSwitcherControl(layerSwitcher);
