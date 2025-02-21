import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const sketchMapUrl = `/api/status/${getUUIDFromURL()}/sketch-map`;

Promise.all([
    poll(sketchMapUrl, "sketch-map"),
]).then(handleMainMessage);
