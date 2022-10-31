import { PAPER_FORMAT, ORIENTATION, Margin } from "@giscience/ol-print-layout-control";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins";
import { fillSelectOptions } from "../shared";

function bindFormToPrintLayoutControl(printLayoutControl) {
    // property: format
    fillSelectOptions("format", PAPER_FORMAT);

    // set initial form value from ol-control
    document.getElementById("format").value = printLayoutControl.getFormat();

    // bind listeners to update ol-control from form
    document.getElementById("format")
        .addEventListener("change", (event) => {
            const format = event.target.value;
            const orientation = printLayoutControl.getOrientation();
            printLayoutControl.setFormat(format);
            printLayoutControl.setMargin(
                new Margin(SKETCH_MAP_MARGINS[format][orientation]),
            );
        });

    // property: orientation
    fillSelectOptions("orientation", ORIENTATION);

    // set initial form value from ol-control
    document.getElementById("orientation").value = printLayoutControl.getOrientation();

    // bind listeners to update ol-control from form
    document.getElementById("orientation")
        .addEventListener("change", (event) => {
            const orientation = event.target.value;
            const format = printLayoutControl.getFormat();
            printLayoutControl.setOrientation(orientation);
            printLayoutControl.setMargin(
                new Margin(SKETCH_MAP_MARGINS[format][orientation]),
            );
        });

    // property: bbox (in webmercator)
    document.getElementById("bbox").value = JSON.stringify(printLayoutControl.getBbox());
    printLayoutControl.on("change:bbox", (event) => {
        const newBbox = event.target.getBbox();
        document.getElementById("bbox").value = JSON.stringify(newBbox);
    });

    // property: size (WMS request - width and height params)
    document.getElementById("size").value = JSON.stringify(printLayoutControl.getPrintBoxSizeInDots(192));
    printLayoutControl.on("change", (event) => {
        const newSize = event.target.getPrintBoxSizeInDots(192);
        document.getElementById("size").value = JSON.stringify(newSize);
    });
}

export {
    bindFormToPrintLayoutControl,
};
