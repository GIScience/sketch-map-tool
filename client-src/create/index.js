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
} from "../shared/map/map.js";
import { bindFormToLayerSwitcherControl, bindFormToPrintLayoutControl } from "./form.js";
import { MessageController } from "./messageController";
import { getSanitizedUrlSearchParams, setUrlSearchParams } from "../shared";
import { addOAMLayer, addUserLayerControl, getOAMItemId, isOAMLayer } from "../shared/map/oamLayer";


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

const map = await createMap("map", center, zoom, layer);
const printLayoutControl = addPrintLayoutControl(map, format, orientation);
const messageController = new MessageController();

bindFormToPrintLayoutControl(printLayoutControl, messageController);
addGeocoderControl(map);

const layerSwitcher = addLayerSwitcherControl(map);
const userLayerControl = addUserLayerControl(map, layerSwitcher);

bindFormToLayerSwitcherControl(layerSwitcher, userLayerControl);
// add additional layers
if (isOAMLayer(layer)) {
    await addOAMLayer(getOAMItemId(layer), map, layerSwitcher);
} else {
    // set initial form value from ol-control
    document.getElementById("layer").value = layerSwitcher.get("activeLayer").get("name");
}
