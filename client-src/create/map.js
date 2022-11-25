import { Map, View } from "ol";
import { Tile } from "ol/layer";
import { fromLonLat } from "ol/proj";
import { OSM } from "ol/source";
import Geocoder from "@kirtandesai/ol-geocoder";
import { PrintLayout, PAPER_FORMAT, ORIENTATION } from "@giscience/ol-print-layout-control";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins.js";

/**
 * Creates an OpenLayers Map to an element
 * @param {string} [target=map] - a div id where the map will be rendered
 * @param {number[]} [lonLat=[8.68, 49.41]] - an Array with two numbers representing
 *     latitude and longitude
 * @param {number} [zoom=15] - the zoomlevel in which the map will be initialized
 * @returns {Map}
 */
function createMap(target = "map", lonLat = [8.68, 49.41], zoom = 15) {
    const map = new Map({
        target,
        view: new View({
            center: fromLonLat(lonLat),
            zoom,
            maxZoom: 20,
        }),
        layers: [
            new Tile({
                source: new OSM(),
            }),
        ],
    });

    return map;
}

/**
 * Add the print-layout-control to an OpenLayers Map
 * @param map - An instance of an OpenLayers Map
 * @returns {PrintLayout}
 */
function addPrintLayoutControl(map) {
    const printLayoutControl = new PrintLayout({
        format: PAPER_FORMAT.A4,
        orientation: ORIENTATION.LANDSCAPE,
        margin: SKETCH_MAP_MARGINS.A4.landscape,
    });
    map.addControl(printLayoutControl);

    return printLayoutControl;
}

/**
 * Add a geocoder (place search) service to an Openlayers Map
 * @param map
 * @returns {Geocoder}
 */
function addGeocoderControl(map) {
    const geocoder = new Geocoder("nominatim", {
        provider: "osm",
        lang: "en-US", // en-US, fr-FR
        placeholder: "Search for ...",
        targetType: "glass-button",
        limit: 10,
        keepOpen: true,
    });
    map.addControl(geocoder);
    return geocoder;
}

export {
    createMap,
    addPrintLayoutControl,
    addGeocoderControl,
};
