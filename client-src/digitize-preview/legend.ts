import type { FeatureLike } from "ol/Feature";
import Point from "ol/geom/Point";
import Polygon from "ol/geom/Polygon";
import { toContext } from "ol/render";
import Style, { type StyleFunction } from "ol/style/Style";

export type LegendGeometryType = "point" | "polygon";

export interface LegendEntry {
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
export function summarizeFeatures(features: FeatureLike[]): LegendEntry[] {
    const entries = new Map<string, LegendEntry>();
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
 * Draws the legend symbol of an entry onto a canvas the same way OpenLayers draws the feature
 * on the map: the layer's style function is called with the entry's feature and each returned
 * style is rendered onto the canvas (for points e.g. the pin icon plus its marker-symbol on top).
 * Points are placed so that all their images fit the canvas, whatever their anchor
 * (pin tip for markerStyle "pin", center for "shape"); polygons are drawn as a square
 * with the same fill and stroke as on the map.
 */
async function drawLegendSymbol(canvas: HTMLCanvasElement, entry: LegendEntry, styleFunction: StyleFunction) {
    // resolution is not used by the simplestyle function
    const styles = toStyleArray(styleFunction(entry.feature, 1));
    await loadImages(styles);

    let size: [number, number];
    let geometry: Point | Polygon;
    if (entry.type === "point") {
        const [minX, minY, maxX, maxY] = getImagesExtent(styles) ?? [-10, -10, 10, 10];
        size = [Math.ceil(maxX - minX), Math.ceil(maxY - minY)];
        geometry = new Point([-minX, -minY]);
    } else {
        const s = POLYGON_SYMBOL_SIZE;
        size = [s, s];
        // inset by the stroke, so it is not cut off at the canvas border
        geometry = new Polygon([[[1, 1], [s - 1, 1], [s - 1, s - 1], [1, s - 1], [1, 1]]]);
    }

    // sets the canvas to `size` CSS pixels (drawn in device resolution), large symbols are scaled down via CSS
    const vectorContext = toContext(canvas.getContext("2d")!, { size, pixelRatio: window.devicePixelRatio });
    for (const style of styles) {
        vectorContext.setStyle(style);
        vectorContext.drawGeometry(geometry);
    }
}

/**
 * Fills the legend list (`#legend-list`) with one entry per color and geometry type:
 * symbol (drawn with the layer's style function), color name and count, e.g. "📍 blue (3)".
 */
export function renderLegend(entries: LegendEntry[], styleFunction: StyleFunction) {
    const items = entries.map((entry) => {
        const item = document.createElement("li");
        item.title = `${entry.color} ${entry.type === "point" ? "points" : "areas"}: ${entry.count}`;

        const symbol = document.createElement("span");
        symbol.className = `legend-symbol legend-${entry.type}`;
        symbol.setAttribute("aria-hidden", "true");
        const canvas = document.createElement("canvas");
        symbol.append(canvas);
        drawLegendSymbol(canvas, entry, styleFunction).catch((error) => {
            console.error("Could not draw legend symbol", entry, error);
        });

        const count = document.createElement("span");
        count.className = "legend-count";
        count.textContent = `(${entry.count})`;

        item.append(symbol, entry.color, " ", count);
        return item;
    });
    document.querySelector<HTMLUListElement>("#legend-list")!.replaceChildren(...items);
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
