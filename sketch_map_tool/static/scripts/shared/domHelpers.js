/**
 * This function will return the first UUID v4 string that can be found in the current location URL
 * @returns {string}
 */
function getUUIDFromURL() {
    const UUID_V4_PATTERN = /[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/i;
    return location.pathname.match(UUID_V4_PATTERN)[0];
}

/**
 * set the aria-busy HTMLAttribute on the given HTMLElement
 * @param elementId
 * @param isBusy
 */
function setIsBusy(elementId, isBusy) {
    const element = document.getElementById(elementId);
    element.setAttribute("aria-busy", isBusy);
}

/**
 * set the disabled HTMLAttribute on the given HTMLElement
 * @param elementId
 * @param isDisabled
 */
function setDisabled(elementId, isDisabled) {
    const element = document.getElementById(elementId);
    if (isDisabled) {
        element.setAttribute("disabled", "disabled");
    } else {
        element.removeAttribute("disabled");
    }
}

/**
 * Sets the href HTMLAttribute on a link element
 * @param linkElementId
 * @param url
 */
function setDownloadLink(linkElementId, url) {
    const linkElement = document.getElementById(linkElementId);
    linkElement.setAttribute("href", url);
}

export {
    getUUIDFromURL,
    setDisabled,
    setDownloadLink,
    setIsBusy,
};
