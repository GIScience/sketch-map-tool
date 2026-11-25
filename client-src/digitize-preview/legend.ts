import type { FeatureLike } from "ol/Feature";
import Point from "ol/geom/Point";
import Polygon from "ol/geom/Polygon";
import { toContext } from "ol/render";
import Style, { type StyleFunction } from "ol/style/Style";

export type LegendGeometryType = "point" | "polygon";

/** Features grouped by color and geometry type (internal, holds an OpenLayers feature). */
export interface RawLegendEntry {
    /** color name, e.g. "blue" (the "color" property of the features) */
    color: string;
    /** hex value of the color, e.g. "#0E6EB8" ("marker-color" for points, "fill" for polygons) */
    hex: string;
    type: LegendGeometryType;
    /** number of features with this color and geometry type */
    count: number;
    /** the first feature of this group, used to draw the legend symbol with the layer's style function */
    feature: FeatureLike;
}

/**
 * Serializable legend entry: used to render the legend in the preview and sent as JSON
 * with the results form ("legend-entries") to the backend (keep in sync with LegendEntry in
 * sketch_map_tool/models.py).
 */
export interface LegendEntry {
    color: string;
    hex: string;
    type: LegendGeometryType;
    count: number;
    /** display name, initially the color name */
    label: string;
    /** legend symbol as PNG data URL ("data:image/png;base64,..."), empty if it could not be drawn */
    image: string;
    /** size of the symbol in CSS pixels, the image is drawn at LEGEND_PIXEL_RATIO times this size */
    width: number;
    height: number;
}

/**
 * Fixed order of the marking colors in the legend, the same for points and polygons
 * (order of the color codes in COLORS, sketch_map_tool/definitions.py).
 * Unknown colors follow in alphabetical order.
 */
const COLOR_ORDER = ["black", "blue", "green", "orange", "pink", "red", "yellow"];

function colorRank(color: string): number {
    const index = COLOR_ORDER.indexOf(color);
    return index === -1 ? COLOR_ORDER.length : index;
}

/** Size of the square drawn for polygons, in CSS pixels. */
const POLYGON_SYMBOL_SIZE = 16;

/** Fixed pixel ratio of the symbol images (independent of the screen), sharp enough for print. */
const LEGEND_PIXEL_RATIO = 4;

function getLegendGeometryType(feature: FeatureLike): LegendGeometryType | undefined {
    switch (feature.getGeometry()?.getType()) {
        case "Point":
        case "MultiPoint":
            return "point";
        case "Polygon":
        case "MultiPolygon":
            return "polygon";
        default:
            return undefined;
    }
}

/**
 * Counts the features per color and geometry type (points and polygons, other geometries are ignored).
 * Points come first, then polygons, each in the fixed color order (COLOR_ORDER).
 */
export function summarizeFeatures(features: FeatureLike[]): RawLegendEntry[] {
    const entries = new Map<string, RawLegendEntry>();
    for (const feature of features) {
        const type = getLegendGeometryType(feature);
        const color = feature.get("color");
        if (!type || typeof color !== "string") continue;

        const key = `${type}|${color}`;
        const entry = entries.get(key);
        if (entry) {
            entry.count++;
        } else {
            const hex = feature.get(type === "point" ? "marker-color" : "fill");
            entries.set(key, { color, hex: typeof hex === "string" ? hex : "", type, count: 1, feature });
        }
    }
    const typeOrder: Record<LegendGeometryType, number> = { point: 0, polygon: 1 };
    return [...entries.values()].sort((a, b) =>
        typeOrder[a.type] - typeOrder[b.type] || colorRank(a.color) - colorRank(b.color) || a.color.localeCompare(b.color));
}

function toStyleArray(styles: Style | Style[] | void): Style[] {
    if (!styles) return [];
    return Array.isArray(styles) ? styles : [styles];
}

/** Waits until all icon images of the styles are loaded (shapes and text are drawn synchronously). */
async function loadImages(styles: Style[]) {
    await Promise.all(styles.map((style) => {
        const image = style.getImage();
        if (!image) return undefined;
        image.load();
        return image.ready();
    }));
}

/**
 * The box (in CSS pixels, relative to the point) covered by all image styles,
 * as placed by OpenLayers: top left at `point - anchor * scale`, size `size * scale`.
 * `getAnchor()` already includes the style's displacement (e.g. a symbol moved into a pin head).
 * Text styles are not measured, the marker styles draw them inside an image (pin head or badge).
 */
function getImagesExtent(styles: Style[]): [number, number, number, number] | undefined {
    let extent: [number, number, number, number] | undefined;
    for (const style of styles) {
        const image = style.getImage();
        const size = image?.getSize();
        const anchor = image?.getAnchor();
        if (!image || !size || !anchor) continue;
        const [scaleX, scaleY] = image.getScaleArray();
        const minX = -anchor[0] * scaleX;
        const minY = -anchor[1] * scaleY;
        const maxX = minX + size[0] * scaleX;
        const maxY = minY + size[1] * scaleY;
        extent = extent
            ? [Math.min(extent[0], minX), Math.min(extent[1], minY), Math.max(extent[2], maxX), Math.max(extent[3], maxY)]
            : [minX, minY, maxX, maxY];
    }
    return extent;
}

/**
 * Draws the legend symbol of a group onto a canvas the same way OpenLayers draws the feature
 * on the map: the layer's style function is called with the entry's feature and each returned
 * style is rendered onto the canvas (for points e.g. the pin icon plus its marker-symbol on top).
 * Points are placed so that all their images fit the canvas, whatever their anchor
 * (pin tip for markerStyle "pin", center for "shape"); polygons are drawn as a square
 * with the same fill and stroke as on the map.
 * Returns the size of the symbol in CSS pixels.
 */
async function drawLegendSymbol(
    canvas: HTMLCanvasElement,
    group: RawLegendEntry,
    styleFunction: StyleFunction,
): Promise<[number, number]> {
    // resolution is not used by the simplestyle function
    const styles = toStyleArray(styleFunction(group.feature, 1));
    await loadImages(styles);

    let size: [number, number];
    let geometry: Point | Polygon;
    if (group.type === "point") {
        const [minX, minY, maxX, maxY] = getImagesExtent(styles) ?? [-10, -10, 10, 10];
        size = [Math.ceil(maxX - minX), Math.ceil(maxY - minY)];
        geometry = new Point([-minX, -minY]);
    } else {
        const s = POLYGON_SYMBOL_SIZE;
        size = [s, s];
        // inset by the stroke, so it is not cut off at the canvas border
        geometry = new Polygon([[[1, 1], [s - 1, 1], [s - 1, s - 1], [1, s - 1], [1, 1]]]);
    }

    // sets the canvas to `size` CSS pixels, drawn in LEGEND_PIXEL_RATIO resolution
    const vectorContext = toContext(canvas.getContext("2d")!, { size, pixelRatio: LEGEND_PIXEL_RATIO });
    for (const style of styles) {
        vectorContext.setStyle(style);
        vectorContext.drawGeometry(geometry);
    }
    return size;
}

/**
 * Turns the feature groups into serializable legend entries, drawing each symbol
 * (with the layer's style function) into a PNG data URL.
 */
export async function buildLegendEntries(groups: RawLegendEntry[], styleFunction: StyleFunction): Promise<LegendEntry[]> {
    return Promise.all(groups.map(async (group) => {
        const { color, hex, type, count } = group;
        const entry: LegendEntry = { color, hex, type, count, label: color, image: "", width: 0, height: 0 };
        try {
            const canvas = document.createElement("canvas");
            [entry.width, entry.height] = await drawLegendSymbol(canvas, group, styleFunction);
            entry.image = canvas.toDataURL("image/png");
        } catch (error) {
            console.error("Could not draw legend symbol", color, type, error);
        }
        return entry;
    }));
}

/**
 * The legend of the preview: holds the entries (the single source of truth), renders them into
 * a list element and serializes them (`JSON.stringify(legend)`) for the backend.
 */
export class Legend {
    private legendEntries: LegendEntry[] = [];

    constructor(private readonly list: HTMLUListElement) {}

    /** Copies of the entries: changing them does not change the legend (use the setters for that). */
    getLegendEntries(): LegendEntry[] {
        return this.legendEntries.map((entry) => ({ ...entry }));
    }

    setLegendEntries(entries: LegendEntry[]) {
        this.legendEntries = entries.map((entry) => ({ ...entry }));
        this.render();
    }

    /** Groups the features and draws their symbols with the layer's style function. */
    async fromFeatures(features: FeatureLike[], styleFunction: StyleFunction) {
        this.setLegendEntries(await buildLegendEntries(summarizeFeatures(features), styleFunction));
    }

    /** Changes the display name of the entry at `index`. */
    setLabel(index: number, label: string) {
        const entry = this.legendEntries[index];
        if (!entry) throw new RangeError(`No legend entry at index ${index}`);
        entry.label = label;
        this.render();
    }

    /** Used by `JSON.stringify(legend)`: the entries as sent to the backend. */
    toJSON(): LegendEntry[] {
        return this.getLegendEntries();
    }

    /** Adds the entries as JSON to the data of `form` whenever it is submitted. */
    attachToForm(form: HTMLFormElement, name = "legend-entries") {
        form.addEventListener("formdata", (event) => {
            event.formData.set(name, JSON.stringify(this));
        });
    }

    /** Fills the list with one item per entry: symbol image, label and count, e.g. "📍 blue (3)". */
    render() {
        this.list.replaceChildren(...this.legendEntries.map(renderEntry));
    }
}

function renderEntry(entry: LegendEntry): HTMLLIElement {
    const item = document.createElement("li");
    item.title = `${entry.color} ${entry.type === "point" ? "points" : "areas"}: ${entry.count}`;

    const symbol = document.createElement("span");
    symbol.className = `legend-symbol legend-${entry.type}`;
    if (entry.image) {
        const image = document.createElement("img");
        image.src = entry.image;
        image.width = entry.width;
        image.height = entry.height;
        image.alt = `${entry.color} ${entry.type}`;
        symbol.append(image);
    }

    const count = document.createElement("span");
    count.className = "legend-count";
    count.textContent = `(${entry.count})`;

    item.append(symbol, entry.label, " ", count);
    return item;
}

export function initLegendInfo() {
    const infoButton = document.querySelector("#legend-info-btn") as HTMLButtonElement | null;
    const infoPanel = document.querySelector("#legend-info-panel") as HTMLDivElement | null;

    infoButton?.addEventListener("click", () => infoPanel?.toggleAttribute("hidden"));
    infoButton?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            // Prevent Space from scrolling the page down
            event.preventDefault();
            infoPanel?.toggleAttribute("hidden");
        }
    })
}

/**
 * Editable legend title: the textarea grows with its content (CSS field-sizing, with a fallback
 * for browsers without it).
 */
export function initLegendTitle() {
    const textarea = document.getElementById("legend-title") as HTMLTextAreaElement | null;
    if (!textarea || CSS.supports("field-sizing", "content")) return;

    const fitHeight = () => {
        textarea.style.height = "auto";
        const borders = textarea.offsetHeight - textarea.clientHeight;
        textarea.style.height = `${textarea.scrollHeight + borders}px`;
    };
    textarea.addEventListener("input", fitHeight);
    new ResizeObserver(fitHeight).observe(textarea.parentElement!); // re-wrap on width changes
    fitHeight();
}
