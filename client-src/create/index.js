import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "@kirtandesai/ol-geocoder/dist/ol-geocoder.css";
import "./geocoder.css";
import "./create.css";

import { createMap, addPrintLayoutControl, addGeocoderControl } from "./map.js";
import { bindFormToPrintLayoutControl } from "./form.js";

const map = createMap();
const printLayoutControl = addPrintLayoutControl(map);
bindFormToPrintLayoutControl(printLayoutControl);
addGeocoderControl(map);
