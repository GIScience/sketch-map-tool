import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const digitizedResultsUrl = `/api/status/${getUUIDFromURL()}/digitized-data`;

const rasterResultsUrl = `/api/status/${getUUIDFromURL()}/raster-data`;

const qgisResultsUrl = `/api/status/${getUUIDFromURL()}/qgis-data`;

// TODO handle all three results, decide one two or three results

Promise.all([
    poll(rasterResultsUrl, "raster-data"),
    poll(digitizedResultsUrl, "vector-data"),
    poll(qgisResultsUrl, "qgis-data"),
]).then(handleMainMessage);
