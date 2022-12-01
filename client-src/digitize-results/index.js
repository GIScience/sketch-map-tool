import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;

const rasterResultsUrl = `/api/status/${getUUIDFromURL()}/raster-results`;

const qgisResultsUrl = `/api/status/${getUUIDFromURL()}/qgis-data`;

// TODO handle all three results, decide one two or three results

Promise.all([
    poll(rasterResultsUrl, "raster-data"),
    poll(vectorResultsUrl, "vector-data"),
    poll(qgisResultsUrl, "qgis-data"),
]).then(handleMainMessage);
