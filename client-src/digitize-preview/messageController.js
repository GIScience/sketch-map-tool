import { setDisabled } from "../shared";

export class MessageController {
    constructor() {
        this.activeMessageIds = new Set();
    }

    addWarning(elementId) {
        if (this.activeMessageIds.has(elementId)) return;

        setDisabled("next-button", true);
        document.querySelector("#message-container").hidden = false;
        document.querySelector(`#${elementId}`).hidden = false;
        this.activeMessageIds.add(elementId);
    }

    removeWarning(elementId) {
        this.activeMessageIds.delete(elementId);
        document.querySelector(`#${elementId}`).hidden = true;
        if (this.activeMessageIds.size === 0) {
            setDisabled("next-button", false);
        }
        const messageContainer = document.querySelector("#message-container");
        const shouldHide = [...messageContainer.children].every((child) => child.hidden);
        if (shouldHide) {
            messageContainer.hidden = true;
        }
    }
}
