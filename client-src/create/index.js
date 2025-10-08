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
import { setAllQueryParams, getSanitizedUrlSearchParams } from "../shared";
import { Tile } from "ol/layer";
import { XYZ } from "ol/source";
import { OpenAerialMapService } from "./openaerialmapService";
import { transformExtent } from "ol/proj";
import { intersects } from "ol/extent";


const {
    center, zoom, layer, orientation, format,
} = getSanitizedUrlSearchParams();

setAllQueryParams({
    center, zoom, layer, orientation, format,
});

const map = createMap("map", center, zoom, layer);
const printLayoutControl = addPrintLayoutControl(map, format, orientation);
const messageController = new MessageController();

bindFormToPrintLayoutControl(printLayoutControl, messageController);
addGeocoderControl(map);

const layerSwitcherConfigs = [
    // Info: names must correspond to name properties of the layers added to the Map in createMap()
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
];
const layerSwitcher = addLayerswitcherControl(map, layerSwitcherConfigs);

// add additional layers
if (layer.startsWith("oam:")) {
    const oamItemId = layer.replace("oam:", "");
    addOAMLayer(oamItemId).then(() => {
        layerSwitcher.addLayer(
            {
                name: layer,
                label: "OpenAerialMap",
                class: "esri-world-imagery",
            }
        )
    }
    );
}


bindFormToLayerSwitcherControl(layerSwitcher);

document.getElementById("oam-add-button").addEventListener("click", handleAddOAMLayer);

function handleAddOAMLayer() {
    // read text field
    const oamItemId = document.getElementById("oam-itemId").value;
    addOAMLayer(oamItemId);
}

export async function addOAMLayer(oamItemId) {

    const oamLayerName = `oam:${oamItemId}`;
    try {
        const metadata = await OpenAerialMapService.getMetadata(oamItemId);
        console.log(metadata);

        // add layer to map
        const oamBaselayer = new Tile({
            name: oamLayerName,
            visible: true,
            source: new XYZ({
                url: OpenAerialMapService.getTileUrl(oamItemId),
                attributions: "OAM"
            }),
            background: "slategrey"
        });

        map.addLayer(oamBaselayer);

        const projectedBbox = transformExtent(metadata.bbox, "EPSG:4326", map.getView().getProjection());
        if (!intersects(projectedBbox, map.getView().calculateExtent())) {
            map.getView().fit(projectedBbox);
        }
    } catch (error) {
        alert(`The OpenAerialMap Item ${oamItemId} could not be loaded.`);
        layerSwitcher.activateNextLayer();
    }

}
