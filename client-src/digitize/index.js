import "filebokz/dist/filebokz.css";
import "filebokz/dist/filebokz-theme.css";
import "./index.css";

import filebokz from "filebokz";
import { setDisabled, setIsBusy } from "../shared";

// initialize the drag and drop enabled file-uploader
filebokz();

// disable submit...
setDisabled("submitBtn", true);

// ...until files are added
const fileElement = document.querySelector(".filebokz");
fileElement.addEventListener("file-added", (e) => {
    setDisabled("submitBtn", false);
});

// disable it again when all files are removed
fileElement.addEventListener("file-removed", (e) => {
    if (!e.target.classList.contains("has-files")) {
        setDisabled("submitBtn", true);
    }
});

// disable the submit button after submit to prevent multiple submissions
document.forms.namedItem("upload").onsubmit = () => {
    setDisabled("submitBtn", true);
    setIsBusy("submitBtn", true);
};

// In case the page is newly loaded, reset the upload button, the spinner, and the upload field.
// This prevents unexpected behaviour when clicking the back button after an upload.
window.addEventListener("pageshow", () => {
    setDisabled("submitBtn", true);
    setIsBusy("submitBtn", false);

    // Remove all previously selected files. The used file selector (filebokz) seems not to
    // provide a working solution to remove all selected files at once.
    const removeButtons = document.getElementsByClassName("remove");
    for (let i = removeButtons.length - 1; i >= 0; i--) {
        removeButtons[i].click();
    }
});
