function setIsBusy(elementId, isBusy) {
    const element = document.getElementById(elementId);
    element.setAttribute("aria-busy", isBusy);
}

function setDisabled(elementId, isDisabled) {
    const element = document.getElementById(elementId);
    if (isDisabled) {
        element.setAttribute("disabled", "disabled");
    } else {
        element.removeAttribute("disabled");
    }
}

function setDownloadLink(linkElementId, url) {
    const linkElement = document.getElementById(linkElementId);
    linkElement.setAttribute("href", url);
}

export {
    setDisabled,
    setDownloadLink,
    setIsBusy,
};
