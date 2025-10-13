import { Margin, ORIENTATION, PAPER_FORMAT } from "@giscience/ol-print-layout-control";
import { get as getProjection, toLonLat, transformExtent } from "ol/proj";
import { SKETCH_MAP_MARGINS } from "./sketchMapMargins";
import { fillSelectOptions, updateQueryParamWithConditionalDebounce } from "../shared";
import { createAntiMeridianLayer } from "./map";

function bindFormToPrintLayoutControl(printLayoutControl, messageController) {
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
            updateQueryParamWithConditionalDebounce("format", format);
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
            updateQueryParamWithConditionalDebounce("orientation", orientation);
        });

    // property: bbox (in webmercator)
    document.getElementById("bbox").value = JSON.stringify(printLayoutControl.getBbox());
    printLayoutControl.on("change:bbox", (event) => {
        let newBbox = event.target.getBbox();
        newBbox = toLonLat(newBbox.slice(0, 2)).concat(toLonLat(newBbox.slice(2, 4))); // See https://github.com/GIScience/sketch-map-tool/issues/250
        document.getElementById("bbox").value = JSON.stringify(
            transformExtent(newBbox, getProjection("EPSG:4326"), getProjection("EPSG:3857")),
        );
    });

    // property: bboxWGS84 (in wgs84)
    document.getElementById("bboxWGS84").value = JSON.stringify(printLayoutControl.getBboxAsLonLat());
    printLayoutControl.on("change:bbox", (event) => {
        let newBbox = event.target.getBbox();
        newBbox = toLonLat(newBbox.slice(0, 2)).concat(toLonLat(newBbox.slice(2, 4))); // See https://github.com/GIScience/sketch-map-tool/issues/250
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
        updateQueryParamWithConditionalDebounce("zoom", zoom);

        if (zoom < 9) {
            messageController.addWarning("zoom-info");
        } else {
            messageController.removeWarning("zoom-info");
        }
    }

    const antimeridianLayer = createAntiMeridianLayer();
    antimeridianLayer.setMap(printLayoutControl.getMap());

    function handleAntimeridian(bboxWgs84) {
        // normalizeLon uses mathematic modulo like in R, not % symetric modulo like in Java
        // or Javascript
        const normalizeLon = (x) => ((((x + 180) % 360) + 360) % 360) - 180;

        if (!bboxWgs84) return;
        // check if antimeridian is within extent -> when left (x1) is bigger than right (x2)
        const [left, , right] = bboxWgs84;

        if (normalizeLon(left) > normalizeLon(right)) {
            messageController.addWarning("antimeridian-info");
            antimeridianLayer.setVisible(true);
        } else {
            messageController.removeWarning("antimeridian-info");
            antimeridianLayer.setVisible(false);
        }
    }

    // initialize form state
    const view = printLayoutControl.getMap()
        .getView();
    const initialZoom = view.getZoom();
    handleZoomChange(initialZoom);
    handleAntimeridian(printLayoutControl.getBboxAsLonLat());

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

    printLayoutControl.on("change:bbox", (event) => {
        // update the URL when the selection is changed  (e.g. to bookmark the current selection)
        const center = printLayoutControl.getMap().getView().getCenter();
        updateQueryParamWithConditionalDebounce("center", center);
        // show warning and disable form if bbox crosses the antimeridian
        handleAntimeridian(event.target.getBboxAsLonLat());
    });
}

function bindFormToLayerSwitcherControl(layerSwitcherControl) {
    // set initial form value from ol-control
    document.getElementById("layer").value = layerSwitcherControl.get("activeLayer").name;
    function handleLayerSwitch(event) {
        const activeLayerName = event.target.get("activeLayer").get("name");
        document.getElementById("layer").value = activeLayerName;
        updateQueryParamWithConditionalDebounce("layer", activeLayerName);
    }
    layerSwitcherControl.on("change:activeLayer", handleLayerSwitch);
}
export {
    bindFormToPrintLayoutControl,
    bindFormToLayerSwitcherControl,
};
