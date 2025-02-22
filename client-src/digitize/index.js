import "filebokz/dist/filebokz.css";
import "filebokz/dist/filebokz-theme.css";
import "./index.css";

import filebokz from "filebokz";
import { setDisabled, setIsBusy } from "../shared";

// initialize the drag and drop enabled file-uploader
filebokz();

// initialize consent to be on reject
const consentField = document.getElementById("consent");
consentField.value = "False";

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

document.forms.namedItem("upload").onsubmit = (event) => {
    // disable the submit button after submit to prevent multiple submissions
    setDisabled("agreeSubmitBtn", true);
    setDisabled("rejectSubmitBtn", true);

    // get the button which triggered the form submit
    const buttonId = event.submitter.id;

    // set the button that was pushed to be busy
    setIsBusy(buttonId, true);

    const consentDescisionMap = {
        agreeSubmitBtn: "True",
        rejectSubmitBtn: "False",
    };

    // set the consent value to the form field
    consentField.value = consentDescisionMap[buttonId];
};

// In case the page is newly loaded, reset the upload button, the spinner, and the upload field.
// This prevents unexpected behaviour when clicking the back button after an upload.
window.addEventListener("pageshow", () => {
    consentField.checked = false;
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
