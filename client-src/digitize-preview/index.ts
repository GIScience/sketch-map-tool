import "ol/ol.css";
import "@giscience/ol-print-layout-control/dist/ol-print-layout-control.css";
import "./index.css";
import { getSanitizedBboxParam, getSanitizedLayerParam, getUUIDFromURL, setUrlSearchParams } from "../shared";
import { pollVectorResults, ResultStatus } from "./pollVectorResults";
import { addGeoJSONPreviewLayer, createPreviewMap } from "./map";
import { showProcessingErrorsBelowMap } from "./error-handling";

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
// show progress status, show errors
const { response, jsonBody } = await pollVectorResults(vectorResultsUrl, previewMap);

if (response.status == 200 && jsonBody) {

    // partial success: keep the errors visible below the map after the overlay is gone
    if (jsonBody.status === ResultStatus.PartialSuccess) {
        showProcessingErrorsBelowMap(jsonBody.errors ?? [], jsonBody.msg, false);
    }
    // download vector-results and display them on the map
    const resultLayer = addGeoJSONPreviewLayer(previewMap, jsonBody.href);
    const vectorSource = resultLayer.getSource()!;

    // TODO access result layer to create a default legend
    vectorSource.on("featuresloadend", (event) => {
        console.log("Finished loading GeoJSON!", event.features!.map(f=> f.get("name")));
    });


}
