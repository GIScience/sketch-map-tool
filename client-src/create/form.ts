import { Margin, ORIENTATION, PAPER_FORMAT, type PrintLayout } from "@giscience/ol-print-layout-control";
import type { Extent } from "ol/extent";
import { SKETCH_MAP_MARGINS } from "../shared/map/sketchMapMargins";
import {
    fillSelectOptions,
    isPaperFormat,
    type PaperFormat,
    updateQueryParam,
    updateQueryParamWithConditionalDebounce
} from "../shared";
import { createAntiMeridianLayer } from "../shared/map/map";
import type { LayerSwitcher } from "../shared/map/ol-LayerSwitcherControl";
import type { UserLayerControl } from "../shared/map/userLayerControl/userLayerControl";
import type { MessageController } from "./messageController";

/** DPI of the WMS request for the map image (width and height params). */
const WMS_DPI = 192;

function bindFormToPrintLayoutControl(printLayoutControl: PrintLayout, messageController: MessageController) {
    // the application's paper formats (without BROADSHEET and LEGAL)
    // TODO: A0 is temporarily disabled. Add it again once A0 works.
    const paperFormats = Object.fromEntries(
        Object.entries(PAPER_FORMAT).filter(([, format]) => isPaperFormat(format) && format !== PAPER_FORMAT.A0),
    );

    // property: format
    fillSelectOptions("format", paperFormats);

    // set initial form value from ol-control
    document.querySelector<HTMLSelectElement>("#format")!.value = printLayoutControl.getFormat();

    // bind listeners to update ol-control from form
    document.querySelector<HTMLSelectElement>("#format")!
        .addEventListener("change", (event) => {
            const format = (event.target as HTMLSelectElement).value;
            if (!isPaperFormat(format)) return;
            const orientation: ORIENTATION = printLayoutControl.getOrientation();
            printLayoutControl.setFormat(format);
            printLayoutControl.setMargin(new Margin(SKETCH_MAP_MARGINS[format][orientation]));
            updateQueryParamWithConditionalDebounce("format", format);
        });

    // property: orientation
    fillSelectOptions("orientation", ORIENTATION);

    // set initial form value from ol-control
    document.querySelector<HTMLSelectElement>("#orientation")!.value = printLayoutControl.getOrientation();

    // bind listeners to update ol-control from form
    document.querySelector<HTMLSelectElement>("#orientation")!
        .addEventListener("change", (event) => {
            const orientation = (event.target as HTMLSelectElement).value as ORIENTATION;
            const format: PaperFormat = printLayoutControl.getFormat();
            printLayoutControl.setOrientation(orientation);
            printLayoutControl.setMargin(new Margin(SKETCH_MAP_MARGINS[format][orientation]));
            updateQueryParamWithConditionalDebounce("orientation", orientation);
        });

    // properties: bbox (in webmercator) and bboxWGS84 (in wgs84)
    // The control normalizes both: minx lies inside the world (even when the map is panned
    // into a neighboring world copy), see https://github.com/GIScience/sketch-map-tool/issues/250
    const updateBboxInputs = () => {
        document.querySelector<HTMLInputElement>("#bbox")!.value = JSON.stringify(printLayoutControl.getBbox());
        document.querySelector<HTMLInputElement>("#bboxWGS84")!.value = JSON.stringify(printLayoutControl.getBboxAsLonLat());
    };
    updateBboxInputs();
    printLayoutControl.on("change:bbox", updateBboxInputs);

    // property: size (WMS request - width and height params)
    document.querySelector<HTMLInputElement>("#size")!.value = JSON.stringify(printLayoutControl.getPrintBoxSizeInDots(WMS_DPI));
    printLayoutControl.on("change", () => {
        document.querySelector<HTMLInputElement>("#size")!.value = JSON.stringify(printLayoutControl.getPrintBoxSizeInDots(WMS_DPI));
    });

    // property: scale denominator
    document.querySelector<HTMLInputElement>("#scale")!.value = JSON.stringify(printLayoutControl.getScaleDenominator());
    printLayoutControl.on("change", () => {
        document.querySelector<HTMLInputElement>("#scale")!.value = JSON.stringify(printLayoutControl.getScaleDenominator());
    });

    const antimeridianLayer = createAntiMeridianLayer();
    antimeridianLayer.setMap(printLayoutControl.getMap());

    function handleAntimeridian(bboxWgs84: Extent | null) {
        if (!bboxWgs84) return;
        // the control keeps minLon in [-180, 180), so the bbox crosses the antimeridian when maxLon exceeds 180
        const [, , maxLon] = bboxWgs84;

        if (maxLon > 180) {
            messageController.addWarning("antimeridian-info");
            antimeridianLayer.setVisible(true);
        } else {
            messageController.removeWarning("antimeridian-info");
            antimeridianLayer.setVisible(false);
        }
    }

    // initialize form state
    const view = printLayoutControl.getMap()!.getView();
    const updateZoomParam = () => {
        const zoom = view.getZoom();
        if (zoom !== undefined) updateQueryParamWithConditionalDebounce("zoom", zoom);
    };
    updateZoomParam();
    handleAntimeridian(printLayoutControl.getBboxAsLonLat());

    // update form state on zoomchange
    view.on("change:resolution", updateZoomParam);

    // make sure that bbox values are up-to-date before submitting the form
    // (NEXT button in the page setup panel on desktop, in the bottom navigation bar on mobile)
    for (const nextButton of document.querySelectorAll("#next-button, #mobile-next-button")) {
        nextButton.addEventListener("click", () => {
            printLayoutControl.handleBboxChange();
            document.querySelector<HTMLFormElement>("#page-setup-form")!.submit();
        });
    }

    printLayoutControl.on("change:bbox", () => {
        // update the URL when the selection is changed  (e.g. to bookmark the current selection)
        const center = view.getCenter();
        if (center) updateQueryParamWithConditionalDebounce("center", center);
        // show warning and disable form if bbox crosses the antimeridian
        handleAntimeridian(printLayoutControl.getBboxAsLonLat());
    });
}

function bindFormToLayerSwitcherControl(layerSwitcherControl: LayerSwitcher, userLayerControl: UserLayerControl) {
    // TODO: Refactor to accept only a single control and call it twice in index.js

    function handleLayerSwitch(control: LayerSwitcher | UserLayerControl) {
        const activeLayerName: string = control.get("activeLayer").get("name");
        document.querySelector<HTMLInputElement>("#layer")!.value = activeLayerName;
        updateQueryParam("layer", activeLayerName);
    }
    layerSwitcherControl.on("change:activeLayer", () => handleLayerSwitch(layerSwitcherControl));
    userLayerControl.on("change:activeLayer", () => handleLayerSwitch(userLayerControl));
}

export {
    bindFormToPrintLayoutControl,
    bindFormToLayerSwitcherControl,
};
