import { openBottomSheet, setListItems } from "../shared";

/**
 * Turns the loading card into an error message. The overlay stays visible,
 * as there are no results to show on the map.
 */
export function showProcessingError(message?: string) {
    const overlay = document.querySelector<HTMLElement>("#map-loading")!;
    overlay.classList.add("has-error");
    overlay.setAttribute("role", "alert");
    overlay.querySelector<HTMLElement>(".loading-title")!.textContent = "Marking Detection Failed";

    //clear error messages
    document.querySelector<HTMLElement>("#load-errors-box")!.hidden = true;

    // single line without count and without the hint
    if (message) {
        showLoadErrorRows([createErrorRow(message)], false);
    }
}

/**
 * Groups messages by their name and counts how often each name occurs.
 * The name is the part of a message before the first separator (trimmed),
 * or the whole message if it contains no separator.
 *
 * @example
 * groupByMessageCount(["QRCodeError: not found", "QRCodeError: unreadable", "Timeout"]);
 * // Map { "QRCodeError" => 2, "Timeout" => 1 }
 *
 * @param messages - The messages to group, e.g. error messages like "ErrorName: details".
 * @param separator - Separates the name from the rest of the message. Defaults to ":".
 * @returns A Map from name to count, in order of first occurrence.
 */
export function groupByMessageCount(messages: string[], separator = ":") {
    const messageSummaryCount = new Map<string, number>();
    for (const message of messages) {
        const separatorIndex = message.indexOf(separator);
        const name = (separatorIndex === -1 ? message : message.slice(0, separatorIndex)).trim();
        messageSummaryCount.set(name, (messageSummaryCount.get(name) ?? 0) + 1);
    }
    return messageSummaryCount;
}

/**
 * Shows a summary of the errors in the loading card: one row per error type with its count
 * and a hint that the full list is shown below the map once processing has finished.
 * The error type is the part of the message before the first colon (or the whole message).
 */
export function showLoadErrorSummary(messages: string[]) {
    const messageSummaryCount = groupByMessageCount(messages);
    const rows = [...messageSummaryCount].map(([name, count]) => createErrorRow(name, count));
    showLoadErrorRows(rows, true);
}

/**
 * Replaces the rows of the error box in the loading card (hidden if there are no rows).
 */
export function showLoadErrorRows(rows: HTMLElement[], showHint: boolean) {
    document.querySelector<HTMLElement>("#load-errors")!.replaceChildren(...rows);
    document.querySelector<HTMLElement>("#load-error-hint")!.hidden = !showHint;
    document.querySelector<HTMLElement>("#load-errors-box")!.hidden = rows.length === 0;
}

/**
 * Creates a row like the ones in .loading-meta: the (truncated) error name left, the count right.
 */
export function createErrorRow(name: string, count?: number) {
    const row = document.createElement("div");
    row.className = "row";
    const nameEl = document.createElement("span");
    nameEl.className = "error-name";
    nameEl.textContent = name;
    nameEl.title = name;
    row.append(nameEl);
    if (count !== undefined) {
        const countEl = document.createElement("span");
        countEl.textContent = String(count);
        row.append(countEl);
    }
    return row;
}

/**
 * Shows the errors in a message box below the map.
 * If `allFailed` is true (no sketch map could be processed) the box is shown with a hint
 * to check the uploaded sketch maps, even if there are no error messages.
 * Otherwise, the box is hidden if there are no errors.
 */
export function showProcessingErrorsBelowMap(errors: string[], message?: string, allFailed = false) {
    // message to help user
    if (message) document.querySelector<HTMLElement>("#processing-error-msg")!.textContent = message;
    // error details
    setListItems(document.querySelector<HTMLUListElement>("#processing-errors-list")!, errors);
    // hide/show error-box
    document.querySelector<HTMLElement>("#processing-errors")!.hidden = errors.length === 0 && !allFailed;

    updateErrorsToggle();
    // nothing to see on the map: show the errors right away (only has an effect on mobile)
    if (allFailed) openBottomSheet("errors-panel");
}

/**
 * Shows a message box below the map with details about the failed request,
 * which the user can send to the Sketch Map Tool support (also as prefilled mailto link).
 * Used to display 500 or any other unhanled error
 */
export function showServerErrorDetails(response: Response) {
    const details = [
        `Request: ${response.url}`,
        `Status: ${response.status} ${response.statusText}`.trim(),
    ].join("\n");

    document.querySelector<HTMLElement>("#server-error-details")!.textContent = details;

    const mailLink = document.querySelector<HTMLAnchorElement>("#server-error-mail")!;
    const mailAddress = mailLink.href.replace(/^mailto:/, "").split("?")[0];
    const subject = `Sketch Map Tool: Error ${response.status} during Marking Detection`;
    mailLink.href = `mailto:${mailAddress}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(details)}`;

    document.querySelector<HTMLElement>("#server-error")!.hidden = false;

    updateErrorsToggle();
    openBottomSheet("errors-panel"); // only has an effect on mobile
}

/**
 * Updates the "Errors" button in the bottom navigation bar (mobile only):
 * the badge shows the number of processing errors plus 1 for a server error.
 * The button is hidden if no error box is visible, and shown without a badge
 * if an error box is visible but has no listed errors (e.g. all sketch maps failed without details).
 */
export function updateErrorsToggle() {
    const processingErrorsBox = document.querySelector<HTMLElement>("#processing-errors")!;
    const serverErrorBox = document.querySelector<HTMLElement>("#server-error")!;
    const listedErrors = document.querySelectorAll("#processing-errors-list li").length;

    const count = (processingErrorsBox.hidden ? 0 : listedErrors) + (serverErrorBox.hidden ? 0 : 1);
    const hasErrors = !processingErrorsBox.hidden || !serverErrorBox.hidden;

    document.querySelector<HTMLElement>("#errors-count")!.textContent = count > 0 ? String(count) : "";
    document.querySelector<HTMLElement>("#errors-toggle")!.hidden = !hasErrors;
}
