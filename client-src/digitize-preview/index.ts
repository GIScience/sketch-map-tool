import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";
import { getSanitizedBboxParam, getSanitizedLayerParam, getUUIDFromURL, setUrlSearchParams } from "../shared";
import { pollVectorResults } from "./pollVectorResults";
import { createPreviewMap } from "./map";


/**
 * This is the main script which is invoked after DOM Content of digitize-preview.html is loaded.
 */

// get all relevant params in case a permalink has been used to set the application state
const searchParams = new URLSearchParams(window.location.search);
const layer = getSanitizedLayerParam(searchParams.get("layer"));
const bbox = getSanitizedBboxParam(searchParams.get("bbox"));

// invalid params will be replaced by sanitized ones
setUrlSearchParams({
    layer, bbox,
});

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;

const previewMap = await createPreviewMap(layer, bbox);
// show progress status, show errors, download vector-results and display them on the map
await pollVectorResults(vectorResultsUrl, previewMap);

