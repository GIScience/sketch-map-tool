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
