
import { Feature, Map } from "ol";
import VectorSource from "ol/source/Vector";
import { GeoJSON } from "ol/format";
import VectorLayer from "ol/layer/Vector";
import { createSimpleStyleFunction } from "./ol-simplestyle-1.1.0";
import { fromExtent } from "ol/geom/Polygon";
import { Stroke, Style } from "ol/style";
import * as olExtent from "ol/extent";
import { Extent } from "ol/extent";
import { addLayerSwitcherControl, createMap } from "../shared/map/map";
import { addOAMLayer, addUserLayerControl, getOAMItemId, isOAMLayer } from "../shared/map/oamLayer";

function addBboxPreviewLayer(map: Map, bbox: number[]) {
    const vectorSource = new VectorSource({
        features: [new Feature(fromExtent(bbox))]
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource,
        zIndex: Infinity,
        style: new Style({
            stroke: new Stroke({
                color: "#c60427",
                width: 3,
                lineDash: [9, 9],
                lineCap: "butt"
            }),
        })
    });
    vectorLayer.set("name", "Sketch Map Extent", true);
    vectorLayer.set("overlay", true, true);

    map.addLayer(vectorLayer);
    map.getView().fit(bbox, { padding: [30, 30, 30, 30]});
}

export function addGeoJSONPreviewLayer(map: Map, href: string) {
    const vectorSource = new VectorSource({
        format: new GeoJSON({
            dataProjection: "EPSG:4326", featureProjection: "EPSG:3857"
        }),
        url: href,
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource,
        style: createSimpleStyleFunction({
            markerStyle: "pin",
            defaults: { "marker-symbol": "circle" }
        }),
        zIndex: Infinity
    });
    vectorLayer.set("name", "Sketch Map Results", true);
    vectorLayer.set("overlay", true, true);

    map.addLayer(vectorLayer);
    return vectorLayer;
}

export async function createPreviewMap(layer?: string, bbox?: Extent) {
    const center = (bbox) ? olExtent.getCenter(bbox) : undefined;

    //Base Map from original sketchmap
    const map = await createMap("map", center, undefined, layer);

    // add controls
    const layerSwitcher = addLayerSwitcherControl(map);

    if (isOAMLayer(layer)) {
        addUserLayerControl(map, layerSwitcher);
        await addOAMLayer(getOAMItemId(layer), map, layerSwitcher);
    }

    // bbox in EPSG:3857
    if (bbox) addBboxPreviewLayer(map, bbox);

    return map;
}
