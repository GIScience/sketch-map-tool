/**
 * Fills the options of an HTMLSelectElement with the values of a simple key-value Object
 * @param selectElementId - the id of an HTMLSelectElement
 * @param optionsMap - a key-value Object, values will be used as options text and value
 */
function fillSelectOptions(selectElementId: string, optionsMap: Record<string, string | number>) {
    const selectElement = document.getElementById(selectElementId) as HTMLSelectElement;
    Object.values(optionsMap)
        .forEach((optionValue) => {
            const option = document.createElement("option");
            option.text = String(optionValue);
            option.value = String(optionValue);
            selectElement.appendChild(option);
        });
}

/**
 * Sets the aria-busy HTMLAttribute on the given HTMLElement
 * @param elementId - the id of the HTMLElement
 * @param isBusy
 */
function setIsBusy(elementId: string, isBusy: boolean) {
    const element = document.getElementById(elementId)!;
    element.setAttribute("aria-busy", String(isBusy));
}

/**
 * Sets the task status (HTML) as content of the given HTMLElement
 * @param elementId - the id of the HTMLElement
 * @param taskStatus - the status text, may contain HTML
 */
function setTaskStatus(elementId: string, taskStatus: string) {
    const element = document.getElementById(elementId)!;
    element.innerHTML = taskStatus;
}

/**
 * Sets or removes the disabled HTMLAttribute on the given HTMLElement
 * @param elementId - the id of the HTMLElement
 * @param isDisabled
 */
function setDisabled(elementId: string, isDisabled: boolean) {
    const element = document.getElementById(elementId)!;
    element.toggleAttribute("disabled", isDisabled);
}

/**
 * Sets the href HTMLAttribute on a link element
 * @param linkElementId - the id of the link element
 * @param url
 */
function setDownloadLink(linkElementId: string, url: string) {
    const linkElement = document.getElementById(linkElementId)!;
    linkElement.setAttribute("href", url);
}

/**
 * Recursively opens all DETAILSElements towards parent direction in the DOM tree starting with the
 * given element.
 * This can, but must not, be a DETAILSElement.
 *
 * @param element - the start element, nothing happens if it is null
 */
function openDetailsParents(element: Element | null | undefined) {
    if (!element) return;

    if (element instanceof HTMLDetailsElement) {
        element.open = true;
        openDetailsParents(element.parentElement?.closest("details"));
    } else {
        openDetailsParents(element.closest("details"));
    }
}

/**
 * Closes all existing DETAILSElements
 */
function closeAllDetailsElements() {
    document.querySelectorAll("details")
        .forEach((details) => {
            details.open = false;
        });
}

/**
 * Opens all existing DETAILSElements
 */
function openAllDetailsElements() {
    document.querySelectorAll("details")
        .forEach((details) => {
            details.open = true;
        });
}

export {
    fillSelectOptions,
    setTaskStatus,
    setDisabled,
    setDownloadLink,
    setIsBusy,
    openDetailsParents,
    closeAllDetailsElements,
    openAllDetailsElements,
};

/**
 * Replaces the items of the list with one <li> per message.
 */
export function setListItems(list: HTMLUListElement, messages: string[]) {
    console.log(list);
    list.replaceChildren(...messages.map((message) => {
        const item = document.createElement("li");
        item.textContent = message;
        return item;
    }));
}
