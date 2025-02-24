/**
 * This function will return the first UUID v4 string that can be found in the current location URL
 * @returns {string}
 */
function getUUIDFromURL() {
    const UUID_V4_PATTERN = /[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/i;
    // eslint-disable-next-line no-restricted-globals
    return location.pathname.match(UUID_V4_PATTERN)[0];
}

/**
 * Fills the options of an HTMLSelectElement with the values of a simple key-value Object
 * @param {string} selectElementId - the id of an HTMLSelectElement
 * @param { {[key:string] : string|number}} optionsMap - a key-value Object, values will be used as
 *     options text and value
 */
function fillSelectOptions(selectElementId, optionsMap) {
    const selectElement = document.getElementById(selectElementId);
    Object.values(optionsMap)
        .forEach((paperformatValue) => {
            const option = document.createElement("option");
            option.text = paperformatValue;
            option.value = paperformatValue;
            selectElement.appendChild(option);
        });
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

function setTaskStatus(elementId, taskStatus) {
    const element = document.getElementById(elementId);
    element.innerHTML = taskStatus;
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

/**
 * Recursivley open all DETAILElements towards parent direction in the DOM tree starting with the
 * given element.
 * This can, but must not, be a DETAILSElement.
 *
 * @param {HTMLElement} element
 */
function openDetailsParents(element) {
    if (!element) return;

    if (element.nodeName === "DETAILS") {
        element.setAttribute("open", true);
        openDetailsParents(element.parentElement.closest("details"));
    } else {
        openDetailsParents(element.closest("details"));
    }
}

/**
 * Close all existing DETAILSElements
 */
function closeAllDetailsElements() {
    [...document.querySelectorAll("details")]
        .forEach((details) => {
            details.removeAttribute("open");
        });
}

/**
 * Close all existing DETAILSElements
 */
function openAllDetailsElements() {
    [...document.querySelectorAll("details")]
        .forEach((details) => {
            details.setAttribute("open", true);
        });
}

export {
    getUUIDFromURL,
    fillSelectOptions,
    setTaskStatus,
    setDisabled,
    setDownloadLink,
    setIsBusy,
    openDetailsParents,
    closeAllDetailsElements,
    openAllDetailsElements,
};
