import { setDisabled } from "../shared";

const NEXT_BUTTON_IDS = ["next-button", "mobile-next-button"];

export class MessageController {
    constructor() {
        this.activeMessageIds = new Set();
    }

    /** Disables the NEXT buttons while there are warnings, shows their number on the page setup toggle (mobile). */
    #update() {
        const hasWarnings = this.activeMessageIds.size > 0;
        for (const id of NEXT_BUTTON_IDS) setDisabled(id, hasWarnings);
        const count = document.querySelector("#page-setup-warnings-count");
        if (count) count.textContent = hasWarnings ? String(this.activeMessageIds.size) : "";
    }

    addWarning(elementId) {
        if (this.activeMessageIds.has(elementId)) return;

        document.querySelector("#message-container").hidden = false;
        document.querySelector(`#${elementId}`).hidden = false;
        this.activeMessageIds.add(elementId);
        this.#update();
    }

    removeWarning(elementId) {
        this.activeMessageIds.delete(elementId);
        document.querySelector(`#${elementId}`).hidden = true;
        this.#update();
        const messageContainer = document.querySelector("#message-container");
        const shouldHide = [...messageContainer.children].every((child) => child.hidden);
        if (shouldHide) {
            messageContainer.hidden = true;
        }
    }
}
