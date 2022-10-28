import { getUUIDFromURL, poll, handleMainMessage } from "../shared/index.js";

const sketchMapUrl = `/api/status/${getUUIDFromURL()}/sketch-map`;
const qualityReportUrl = `/api/status/${getUUIDFromURL()}/quality-report`;

Promise.all([
    poll(sketchMapUrl, "sketch-map"),
    poll(qualityReportUrl, "quality-report"),
]).then(handleMainMessage);
