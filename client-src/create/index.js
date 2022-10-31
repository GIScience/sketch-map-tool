import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./create.css";

import { createMap, addPrintLayoutControl } from "./map.js";
import { bindFormToPrintLayoutControl } from "./form.js";

const map = createMap();
const printLayoutControl = addPrintLayoutControl(map);
bindFormToPrintLayoutControl(printLayoutControl);
