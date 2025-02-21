import "filebokz/dist/filebokz.css";
import "filebokz/dist/filebokz-theme.css";
import "./index.css";

import filebokz from "filebokz";
import { setDisabled, setIsBusy } from "../shared";

// initialize the drag and drop enabled file-uploader
filebokz();

// initialize consent to be on reject
const consentCheckbox = document.getElementById("consent");
consentCheckbox.checked = false;

// disable submit...
setDisabled("agreeSubmitBtn", true);
setDisabled("rejectSubmitBtn", true);

// ...until files are added
const fileElement = document.querySelector(".filebokz");
fileElement.addEventListener("file-added", () => {
    setDisabled("agreeSubmitBtn", false);
    setDisabled("rejectSubmitBtn", false);
});

// disable it again when all files are removed
fileElement.addEventListener("file-removed", (e) => {
    if (!e.target.classList.contains("has-files")) {
        setDisabled("agreeSubmitBtn", true);
        setDisabled("rejectSubmitBtn", true);
    }
});

// disable the submit button after submit to prevent multiple submissions
document.forms.namedItem("upload").onsubmit = (event) => {

    // get the button which triggered the form submit
    const buttonId = event.submitter.id;

    const consentDescisionMap = {
        agreeSubmitBtn: true,
        rejectSubmitBtn: false,
    };

    // set the consent
    consentCheckbox.checked = consentDescisionMap[buttonId];

    setDisabled("agreeSubmitBtn", true);
    setDisabled("rejectSubmitBtn", true);
    setIsBusy(buttonId, true);
};

// In case the page is newly loaded, reset the upload button, the spinner, and the upload field.
// This prevents unexpected behaviour when clicking the back button after an upload.
window.addEventListener("pageshow", () => {
    consentCheckbox.checked = false;
    setDisabled("agreeSubmitBtn", true);
    setDisabled("rejectSubmitBtn", true);
    setIsBusy("agreeSubmitBtn", false);
    setIsBusy("rejectSubmitBtn", false);

    // Remove all previously selected files. The used file selector (filebokz) seems not to
    // provide a working solution to remove all selected files at once.
    const removeButtons = document.getElementsByClassName("remove");
    for (let i = removeButtons.length - 1; i >= 0; i--) {
        removeButtons[i].click();
    }
});
