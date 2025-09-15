import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "ol-geocoder/dist/ol-geocoder.css";
import "./geocoder.css";
import "./create.css";

import { PAPER_FORMAT, ORIENTATION } from "@giscience/ol-print-layout-control";
import {
    addGeocoderControl,
    addLayerswitcherControl,
    addPrintLayoutControl,
    createMap,
} from "./map.js";
import { bindFormToLayerSwitcherControl, bindFormToPrintLayoutControl } from "./form.js";
import { MessageController } from "./messageController";
import { setAllQueryParam } from "../shared";

function getSanitizedUrlSearchParams() {
    // Retrieve potentially given map and print layout parameter from URL
    // (e.g. from a bookmarked selection)
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
    let activeBaselayer = "OSM";
    if (baselayerArg != null) {
        switch (baselayerArg) {
            case "ESRI:World_Imagery":
                activeBaselayer = baselayerArg;
                break;
            default:
                activeBaselayer = "OSM";
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
        center, zoom, activeBaselayer, orientation, format,
    };
}

const {
    center, zoom, activeBaselayer, orientation, format,
} = getSanitizedUrlSearchParams();

setAllQueryParam({
    center, zoom, orientation, format,
});

const map = createMap("map", center, zoom, activeBaselayer);
const printLayoutControl = addPrintLayoutControl(map, format, orientation);
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
