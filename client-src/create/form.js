import { PAPER_FORMAT, ORIENTATION, Margin } from "@giscience/ol-print-layout-control";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins";
import { fillSelectOptions, setDisabled } from "../shared";

function bindFormToPrintLayoutControl(printLayoutControl) {
    const paperFormats = { ...PAPER_FORMAT };
    delete paperFormats.BROADSHEET;

    // TODO: This is temporary. Delete once A0 works
    delete paperFormats.A0;

    // property: format
    fillSelectOptions("format", paperFormats);

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

    // property: bboxWGS84 (in wgs84)
    document.getElementById("bboxWGS84").value = JSON.stringify(printLayoutControl.getBboxAsLonLat());
    printLayoutControl.on("change:bbox", (event) => {
        const newBbox = event.target.getBboxAsLonLat();
        document.getElementById("bboxWGS84").value = JSON.stringify(newBbox);
    });

    // property: size (WMS request - width and height params)
    document.getElementById("size").value = JSON.stringify(printLayoutControl.getPrintBoxSizeInDots(192));
    printLayoutControl.on("change", (event) => {
        const newSize = event.target.getPrintBoxSizeInDots(192);
        document.getElementById("size").value = JSON.stringify(newSize);
    });

    // property: scale denominator
    document.getElementById("scale").value = JSON.stringify(printLayoutControl.getScaleDenominator());
    printLayoutControl.on("change", (event) => {
        const newScale = event.target.getScaleDenominator();
        document.getElementById("scale").value = JSON.stringify(newScale);
    });

    // disable form submit and display info if zoom is lower than 9
    function handleZoomChange(zoom) {
        if (zoom < 9) {
            setDisabled("next-button", true);
            document.querySelector("#infobox")
                .classList
                .remove("invisible");
        } else {
            setDisabled("next-button", false);
            document.querySelector("#infobox")
                .classList
                .add("invisible");
        }
    }

    // initialize form state
    const view = printLayoutControl.getMap()
        .getView();
    const initialZoom = view.getZoom();
    handleZoomChange(initialZoom);

    // update form state on zoomchange
    printLayoutControl.getMap()
        .getView()
        .on("change:resolution", (event) => {
            const currentZoom = event.target.getZoom();
            handleZoomChange(currentZoom);
        });

    // make sure that bbox values are up-to-date before submitting the form
    document.getElementById("next-button")
        .addEventListener("click", () => {
            printLayoutControl.handleBboxChange();
            document.querySelector("#page-setup-form").submit();
        });

    // update the URL when the selection is changed  (e.g. to bookmark the current selection)
    printLayoutControl.on("change:bbox", (event) => {
        const newCenter = printLayoutControl.getMap().getView().getCenter();
        window.history.replaceState({}, document.title, `?center=${newCenter}`);
    });
}

export {
    bindFormToPrintLayoutControl,
};
