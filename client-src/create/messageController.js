import { setDisabled } from "../shared";

export class MessageController {
    constructor() {
        this.activeMessageIds = new Set();
    }

    addWarning(elementId) {
        if (this.activeMessageIds.has(elementId)) return;

        setDisabled("next-button", true);
        document.querySelector(`#${elementId}`)
            .classList
            .remove("hidden");

        this.activeMessageIds.add(elementId);
    }

    removeWarning(elementId) {
        this.activeMessageIds.delete(elementId);
        document.querySelector(`#${elementId}`)
            .classList
            .add("hidden");
        if (this.activeMessageIds.size === 0) {
            setDisabled("next-button", false);
        }
    }
}
