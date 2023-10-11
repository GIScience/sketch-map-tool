import { Feature, Map, View } from "ol";
import { Tile } from "ol/layer";
import { OSM } from "ol/source";
import Geocoder from "@kirtandesai/ol-geocoder";
import { PrintLayout, PAPER_FORMAT, ORIENTATION } from "@giscience/ol-print-layout-control";
import { fromLonLat } from "ol/proj";
import { LineString } from "ol/geom";
import VectorSource from "ol/source/Vector";
import VectorLayer from "ol/layer/Vector";
import {
    Fill, Stroke, Style, Text,
} from "ol/style";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins.js";

function createAntiMeridianLayer() {
    // Create a LineString feature
    const lineString = new LineString([
        fromLonLat([180, -90]), // Start point just to the east of the antimeridian
        fromLonLat([180, 90]), // End point just to the west of the antimeridian
    ]);

    // Create a vector source and add the LineString feature to it
    const vectorSource = new VectorSource({
        features: [new Feature({
            geometry: lineString,
        })],
    });

    // Create a vector layer and set the source
    return new VectorLayer({
        name: "Antimeridian",
        source: vectorSource,
        visible: false,
        style: new Style({
            stroke: new Stroke({
                color: "red",
                width: 3,
            }),
            text: new Text({
                text: "Antimeridian",
                placement: "line",
                offsetY: -10,
                fill: new Fill({ color: "red" }),
                font: "20px sans-serif",
                repeat: 200,
            }),
        }),
    });
}

/**
 * Creates an OpenLayers Map to an element
 * @param {string} [target=map] - a div id where the map will be rendered
 * @param {number[]} [lonLat=[8.68, 49.41]] - an Array with two numbers representing
 *     latitude and longitude
 * @param {number} [zoom=15] - the zoomlevel in which the map will be initialized
 * @returns {Map}
 */
function createMap(target = "map", lonLat = [966253.1800856147, 6344703.99262965], zoom = 15) {
    const map = new Map({
        target,
        view: new View({
            center: lonLat,
            zoom,
            maxZoom: 20,
            enableRotation: false,
        }),
        layers: [
            new Tile({
                source: new OSM(),
            }),
            createAntiMeridianLayer(),
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
