import { getUUIDFromURL, poll, handleMainMessage } from "../shared";

const digitizedResultsUrl = `/api/status/${getUUIDFromURL()}/digitized-data`;

// TODO handle all three results
poll(digitizedResultsUrl, "vector-data").then(handleMainMessage);
