import { Tile } from "ol/layer";
import { XYZ } from "ol/source";
import { transformExtent } from "ol/proj";
import { intersects } from "ol/extent";
import type { Map } from "ol";
import type BaseEvent from "ol/events/Event";
import { unit } from "mathjs";
import { OpenAerialMapService } from "./openaerialmapService";
import { UserLayerControl } from "./userLayerControl/userLayerControl";
import type { LayerSwitcher } from "./ol-LayerSwitcherControl";

const OAM_PREFIX = "oam:";

export function isOAMLayer(layerName: string): boolean {
    return layerName.startsWith(OAM_PREFIX);
}

export function getOAMItemId(layerName: string): string {
    return layerName.replace(OAM_PREFIX, "");
}

/**
 * Adds an OpenAerialMap item as base layer to the map and suspends the layer switcher.
 * Zooms to the item's extent if it is not visible in the current view.
 */
export async function addOAMLayer(oamItemId: string, map: Map, layerSwitcher: LayerSwitcher) {
    try {
        const metadata = await OpenAerialMapService.getMetadata(oamItemId);
        console.log(metadata);
        layerSwitcher.activateNextLayer();
        layerSwitcher.suspend();

        const oamBaselayer = new Tile({
            visible: true,
            source: new XYZ({
                url: OpenAerialMapService.getTileUrl(oamItemId),
                attributions: OpenAerialMapService.getMapAttributionFromMetadata(metadata),
            }),
            background: "slategrey",
        });
        oamBaselayer.set("name", `${OAM_PREFIX}${oamItemId}`, true);
        oamBaselayer.set("ulc_visible", true, true);
        oamBaselayer.set("ulc_buttonImageUrl", OpenAerialMapService.getThumbnailUrl(oamItemId, 256), true);

        map.addLayer(oamBaselayer);

        const projectedBbox = transformExtent(metadata.bbox, "EPSG:4326", map.getView().getProjection());
        if (!intersects(projectedBbox, map.getView().calculateExtent())) {
            map.getView().fit(projectedBbox);
        }
    } catch (error) {
        console.log(`The OpenAerialMap Item ${oamItemId} could not be loaded.`, error);
        throw error;
    }
}

/**
 * Creates the UserLayerControl inside the layer switcher, wires it to the layer switcher
 * and binds the OAM add and info dialogs.
 */
export function addUserLayerControl(map: Map, layerSwitcher: LayerSwitcher): UserLayerControl {
    const layerswitcherSlot = document.querySelector<HTMLElement>(".layerswitcher #slot")!;

    const userLayerControl = new UserLayerControl({ target: layerswitcherSlot });
    map.addControl(userLayerControl);
    userLayerControl.initialize();

    userLayerControl.on("new-layer", openOamDialog);

    // keep the current layer in layerswitcher to toggle back from OAM Layer
    userLayerControl.on("beforeactivate", () => {
        layerSwitcher.activateNextLayer();
    });
    // switch back to the layer you came from when removing OAM Layer
    userLayerControl.on("close", () => {
        layerSwitcher.activateNextLayer();
    });

    initOAMDialogs(map, layerSwitcher, userLayerControl);

    return userLayerControl;
}

function initOAMDialogs(map: Map, layerSwitcher: LayerSwitcher, userLayerControl: UserLayerControl) {
    // OAM Metadata Dialog Handling
    userLayerControl.on("info", showOamInfo);

    const oamInfoDialog = document.querySelector<HTMLDialogElement>("#oam-info-dialog")!;
    document.querySelector<HTMLButtonElement>("#oam-info-ok-button")!.addEventListener("click", () => {
        oamInfoDialog.close();
    });
    document.querySelector<HTMLButtonElement>("#oam-info-close-button")!.addEventListener("click", () => {
        oamInfoDialog.close();
    });

    // OAM Add Dialog Handling
    document.querySelector<HTMLButtonElement>("#oam-add-button")!.addEventListener("click", async () => {
        const oamItemIdInput = document.querySelector<HTMLInputElement>("#oam-item-id-input")!;
        const oamInvalidIdMessage = document.querySelector<HTMLElement>("#oam-invalid-id-message")!;
        const oamProgressBar = document.querySelector<HTMLProgressElement>("#oam-progress-bar")!;
        try {
            if (oamItemIdInput.value.length === 0) {
                throw new Error("Empty input not allowed.");
            }
            oamProgressBar.classList.remove("hidden");
            await addOAMLayer(oamItemIdInput.value, map, layerSwitcher);
            closeOamDialog();
        } catch (error) {
            console.error(error);
            oamInvalidIdMessage.classList.remove("hidden");
            oamItemIdInput.setAttribute("aria-invalid", "true");
        } finally {
            oamProgressBar.classList.add("hidden");
        }
    });

    document.querySelector<HTMLButtonElement>("#oam-close-button")!.addEventListener("click", closeOamDialog);
    document.querySelector<HTMLButtonElement>("#oam-cancel-button")!.addEventListener("click", closeOamDialog);
}

function openOamDialog() {
    document.querySelector<HTMLDialogElement>("#oam-dialog")!.show();
    document.querySelector<HTMLInputElement>("#oam-item-id-input")!.focus();
}

function closeOamDialog() {
    // reset state
    document.querySelector<HTMLElement>("#oam-invalid-id-message")!.classList.add("hidden");
    document.querySelector<HTMLInputElement>("#oam-item-id-input")!.removeAttribute("aria-invalid");
    document.querySelector<HTMLDialogElement>("#oam-dialog")!.close();
}

async function showOamInfo(event: BaseEvent) {
    const infoDialog = document.querySelector<HTMLDialogElement>("#oam-info-dialog")!;
    const oamItemId = getOAMItemId((event.target as UserLayerControl).get("activeLayer").get("name"));

    // open the dialog
    infoDialog.show();

    // load preview image
    infoDialog.querySelector("img")!.setAttribute("src", OpenAerialMapService.getThumbnailUrl(oamItemId, 256));

    // load and show the metadata properties
    const metadata = await OpenAerialMapService.getMetadata(oamItemId);
    const {
        title,
        start_datetime,
        gsd: resolution,
        "oam:producer_name": producer,
        "oam:platform_type": platform,
        license,
    } = metadata.properties;

    //set table properties
    document.querySelector<HTMLTableCellElement>("#title")!.textContent = title;
    document.querySelector<HTMLTableCellElement>("#date")!.textContent = new Date(start_datetime).toLocaleDateString();
    document.querySelector<HTMLTableCellElement>("#resolution")!.textContent = unit(resolution, "m").toBest(["cm", "m"]).format({
        notation: "auto",
        precision: 2
    });
    document.querySelector<HTMLTableCellElement>("#provider")!.textContent = producer;
    document.querySelector<HTMLTableCellElement>("#platform")!.textContent = platform.toUpperCase();
    document.querySelector<HTMLTableCellElement>("#license")!.textContent = license;
    document.querySelector<HTMLTableCellElement>("#itemId")!.textContent = oamItemId;
}
