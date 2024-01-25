import { Feature, Map, View } from "ol";
import { Tile } from "ol/layer";
import { OSM, XYZ } from "ol/source";
import Geocoder from "ol-geocoder";
import { ORIENTATION, PAPER_FORMAT, PrintLayout } from "@giscience/ol-print-layout-control";
import { fromLonLat } from "ol/proj";
import { LineString } from "ol/geom";
import VectorSource from "ol/source/Vector";
import VectorLayer from "ol/layer/Vector";
import {
    Fill, Stroke, Style, Text,
} from "ol/style";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins.js";
import { LayerSwitcher } from "./olLayersitcherControl";

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
                text: "Antimeridian\nPlease move it out of the map",
                placement: "line",
                offsetY: 2,
                fill: new Fill({ color: "red" }),
                font: "16px sans-serif",
                repeat: 400,
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
 * @param {string} [baselayer="OSM"] - the baselayer to be displayed 'OSM' | 'ESRI:World_Imagery'
 * @returns {Map}
 */
function createMap(target = "map", lonLat = [966253.1800856147, 6344703.99262965], zoom = 15, baselayer = "OSM") {
    const osmBaselayer = new Tile({
        name: "OSM Baselayer",
        visible: baselayer !== "ESRI:World_Imagery",
        source: new OSM(),
    });

    const esriWorldImageryLayer = new Tile({
        name: "ESRI:World_Imagery",
        visible: baselayer === "ESRI:World_Imagery",
        source: new XYZ({
            // esriApiKey seems to be undefined, but:
            // esriApiKey will be injected by flask template into create.html
            // and is defined in config.toml to avoid pushing it to a repository

            // eslint-disable-next-line no-undef
            url: `https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}?token=${esriApiKey}`,
            // TODO attribution
        }),
    });

    const map = new Map({
        target,
        view: new View({
            center: lonLat,
            zoom,
            maxZoom: 20,
            enableRotation: false,
        }),
        layers: [
            osmBaselayer,
            esriWorldImageryLayer,
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

/**
 * Add a layerswitcher to an Openlayers Map
 * @param map
 * @param layers an array of objects of type {name: string; label: string; class: string}.
 *
 *              "name" is used to identify switchable layers from th ol-Map so this should
 *              correspond to a name property set to the ol-layers.
 *
 *              "label" is a string that will be rendered as text on the layerswitcher button
 *
 *              "class" a custom class name that will be added to the button to indicate what is the
 *              next layer when a user clicks on the button, e.g. to specify a background image etc
 * @returns {LayerSwitcher}
 */
function addLayerswitcherControl(map, layers) {
    const layerswitcher = new LayerSwitcher({
        layers,
    });
    map.addControl(layerswitcher);
    layerswitcher.initialize();
    return layerswitcher;
}

export {
    createMap,
    addPrintLayoutControl,
    addGeocoderControl,
    addLayerswitcherControl,
};
