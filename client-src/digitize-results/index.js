import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;
const centroidsResultsUrl = `/api/status/${getUUIDFromURL()}/centroid-results`;
const rasterResultsUrl = `/api/status/${getUUIDFromURL()}/raster-results`;

Promise.all([
    poll(rasterResultsUrl, "raster-data"),
    poll(vectorResultsUrl, "vector-data"),
    poll(centroidsResultsUrl, "centroid-data"),
]).then(handleMainMessage);
