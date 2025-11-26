import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;
const rasterResultsUrl = `/api/status/${getUUIDFromURL()}/raster-results`;

Promise.all([
    poll(rasterResultsUrl, "raster-data"),
    poll(vectorResultsUrl, "vector-data"),
]).then(handleMainMessage);
