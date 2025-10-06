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
import {Tile} from "ol/layer";
import {XYZ} from "ol/source";


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

document.getElementById("oam-add-button").addEventListener("click", addOAMLayer);

function addOAMLayer(){
    // read text field
    const oamURL = document.getElementById("oam-tms-url").value;

    // add layer to map
    const oamBaselayer = new Tile({
        name: oamURL,
        visible: true,
        source: new XYZ({
            url: oamURL,
            attributions: "OAM"
        }),
        background: "slategrey"
    });

    map.addLayer(oamBaselayer);

    // add layer to layerswitcher
    const layerSwitcherLayer = {
        name: oamURL,
        label: "OpenAerialMap",
        class: "esri-world-imagery",
    };

    layerSwitcher.addLayer(layerSwitcherLayer);
}
