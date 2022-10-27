/**
 * This function will return the first UUID v4 string that can be found in the current location URL
 * @returns {string}
 */
function getUUIDFromURL() {
    const UUID_V4_PATTERN = /[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/i;
    return location.pathname.match(UUID_V4_PATTERN)[0];
}

export { getUUIDFromURL };
