/**
 * Reusable bottom sheet component, styles in bottom-sheet.css.
 *
 * Markup: an element with class "bottom-sheet" and an id, toggled by any `button[aria-controls="<id>"]`
 * (usually inside a `.bottom-nav`). A `.bottom-sheet-handle` button inside the sheet closes it.
 * Below 992px sheets slide up above the bottom navigation bar and are non-modal (no backdrop);
 * from 992px on they stay in the normal page flow and the functions in this module do nothing.
 */

const MOBILE_QUERY = "(width < 992px)";

const mobileMediaQuery = window.matchMedia(MOBILE_QUERY);
let lastToggleButton: HTMLElement | null = null;
let initialized = false;

function getSheets(): HTMLElement[] {
    return Array.from(document.querySelectorAll<HTMLElement>(".bottom-sheet"));
}

function getToggleButtons(sheetId: string): HTMLElement[] {
    return Array.from(document.querySelectorAll<HTMLElement>(`button[aria-controls="${CSS.escape(sheetId)}"]`));
}

function isSheet(element: Element | null): element is HTMLElement {
    return element instanceof HTMLElement && element.classList.contains("bottom-sheet");
}

/** Closed sheets are off-screen on mobile and must not be reachable via keyboard. */
function updateInert() {
    for (const sheet of getSheets()) {
        sheet.inert = mobileMediaQuery.matches && !sheet.classList.contains("is-open");
    }
}

function setOpenState(sheet: HTMLElement, isOpen: boolean) {
    sheet.classList.toggle("is-open", isOpen);
    for (const button of getToggleButtons(sheet.id)) {
        button.setAttribute("aria-expanded", String(isOpen));
    }
}

/**
 * Opens the bottom sheet with the given id (and closes any other open sheet). Does nothing on desktop.
 * @param sheetId - the id of an element with class "bottom-sheet"
 */
export function openBottomSheet(sheetId: string) {
    const sheet = document.getElementById(sheetId);
    if (!isSheet(sheet) || !mobileMediaQuery.matches) return;

    // remember where to return the focus on close (toggle buttons set it on click,
    // as e.g. Safari does not focus buttons on click; switching sheets keeps it)
    const activeElement = document.activeElement;
    const focusIsInSheet = getSheets().some(s => s.contains(activeElement));
    if (!lastToggleButton && activeElement instanceof HTMLElement && !focusIsInSheet && activeElement !== document.body) {
        lastToggleButton = activeElement;
    }

    for (const other of getSheets()) {
        if (other !== sheet) setOpenState(other, false);
    }
    setOpenState(sheet, true);
    updateInert();

    // focus the sheet itself, so screen readers announce it without jumping to the first link
    sheet.tabIndex = -1;
    sheet.focus({ preventScroll: true });
}

/**
 * Closes the bottom sheet with the given id and returns the focus to the element that opened it.
 * @param sheetId - the id of an element with class "bottom-sheet"
 */
export function closeBottomSheet(sheetId: string) {
    const sheet = document.getElementById(sheetId);
    if (!isSheet(sheet) || !sheet.classList.contains("is-open")) return;

    const hadFocus = sheet.contains(document.activeElement);
    setOpenState(sheet, false);
    updateInert();

    if (hadFocus && lastToggleButton?.isConnected) lastToggleButton.focus();
    lastToggleButton = null;
}

/**
 * Opens the bottom sheet with the given id if it is closed, closes it otherwise.
 * @param sheetId - the id of an element with class "bottom-sheet"
 */
export function toggleBottomSheet(sheetId: string) {
    const sheet = document.getElementById(sheetId);
    if (sheet?.classList.contains("is-open")) {
        closeBottomSheet(sheetId);
    } else {
        openBottomSheet(sheetId);
    }
}

function closeAllBottomSheets() {
    for (const sheet of getSheets()) closeBottomSheet(sheet.id);
}

/**
 * Wires up all bottom sheets on the page: toggle buttons (`button[aria-controls]` pointing to a
 * `.bottom-sheet`), handles (`.bottom-sheet-handle` inside a sheet), the Esc key and the switch
 * between mobile and desktop layout. Call once after the DOM is loaded.
 */
export function initBottomSheets() {
    if (initialized) return;
    initialized = true;

    for (const button of document.querySelectorAll<HTMLButtonElement>("button[aria-controls]")) {
        const sheetId = button.getAttribute("aria-controls")!;
        if (!isSheet(document.getElementById(sheetId))) continue;
        button.setAttribute("aria-expanded", "false");
        button.addEventListener("click", () => {
            const isOpen = document.getElementById(sheetId)!.classList.contains("is-open");
            if (!isOpen) lastToggleButton = button;
            toggleBottomSheet(sheetId);
        });
    }

    for (const sheet of getSheets()) {
        for (const handle of sheet.querySelectorAll<HTMLElement>(".bottom-sheet-handle")) {
            handle.addEventListener("click", () => closeBottomSheet(sheet.id));
        }
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeAllBottomSheets();
    });

    mobileMediaQuery.addEventListener("change", () => {
        if (!mobileMediaQuery.matches) {
            for (const sheet of getSheets()) setOpenState(sheet, false);
            lastToggleButton = null;
        }
        updateInert();
    });

    updateInert();
}
