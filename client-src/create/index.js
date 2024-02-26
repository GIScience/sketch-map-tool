import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "ol-geocoder/dist/ol-geocoder.css";
import "./geocoder.css";
import "./create.css";

import { addGeocoderControl, addPrintLayoutControl, createMap } from "./map.js";
import { bindFormToPrintLayoutControl } from "./form.js";
import { MessageController } from "./messageController";

// Retrieve potentially given map center from URL (e.g. from a bookmarked selection)
const searchParams = new URLSearchParams(window.location.search);
const centerArg = searchParams.get("center");

let center = [966253.1800856147, 6344703.99262965];
if (centerArg != null) {
    const centerCoords = centerArg.split(",");
    center = [parseFloat(centerCoords[0]), parseFloat(centerCoords[1])];
}

const map = createMap("map", center, 15);

const printLayoutControl = addPrintLayoutControl(map);
const messageController = new MessageController();

bindFormToPrintLayoutControl(printLayoutControl, messageController);
addGeocoderControl(map);
