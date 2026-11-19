import { getUUIDFromURL, poll, handleMainMessage, getUUIDFromSearchParam } from "../shared";

const pdfMapResultUrl = `/api/status/${getUUIDFromSearchParam("pdf-map")}/pdf-map-result`;
const vectorResultsUrl = `/api/status/${getUUIDFromURL()}/vector-results`;
const rasterResultsUrl = `/api/status/${getUUIDFromURL()}/raster-results`;

await Promise.all([
    poll(pdfMapResultUrl, "pdf-map"),
    poll(vectorResultsUrl, "vector-data"),
    poll(rasterResultsUrl, "raster-data"),
]).then(handleMainMessage);
