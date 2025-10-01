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
import { setAllQueryParam, getSanitizedUrlSearchParams } from "../shared";


const {
    center, zoom, layer, orientation, format,
} = getSanitizedUrlSearchParams();

setAllQueryParam({
    center, zoom, layer, orientation, format,
});

const map = createMap("map", center, zoom, layer);
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
