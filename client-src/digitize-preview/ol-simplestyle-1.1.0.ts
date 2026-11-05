/**
 * OpenLayers 10 style function implementing the simplestyle-spec 1.1.0
 * https://github.com/mapbox/simplestyle-spec/tree/master/1.1.0
 *
 * Usage:
 *   import VectorLayer from 'ol/layer/Vector';
 *   import VectorSource from 'ol/source/Vector';
 *   import GeoJSON from 'ol/format/GeoJSON';
 *   import simpleStyleFunction from './ol-simplestyle-1.1.0';
 *
 *   new VectorLayer({
 *     source: new VectorSource({ url: 'data.geojson', format: new GeoJSON() }),
 *     style: simpleStyleFunction,
 *   });
 *
 * Or with options:
 *   style: createSimpleStyleFunction({ markerStyle: 'shape', markerSymbolUrl: (s) => `/icons/${s}.svg` })
 *
 * marker-symbol values:
 *   "0"–"9", "a"–"z"   drawn as text
 *   circle, square, triangle, star, cross, x-cross   built-in shapes (SLD-like)
 *   anything else      passed to `markerSymbolUrl` (if given)
 *
 * Marker styles (layer option `markerStyle`):
 *   "pin"    a pin in marker-color with the symbol inside its head (simplestyle default)
 *   "shape"  the shape itself filled with marker-color; digits, letters and icons
 *            sit in a round badge. Without a symbol, `defaultShape` is drawn.
 */
import type { FeatureLike } from "ol/Feature";
import type { StyleFunction } from "ol/style/Style";
import Style from "ol/style/Style";
import Stroke from "ol/style/Stroke";
import Fill from "ol/style/Fill";
import Icon from "ol/style/Icon";
import Text from "ol/style/Text";
import CircleStyle from "ol/style/Circle";
import RegularShape from "ol/style/RegularShape";
import type ImageStyle from "ol/style/Image";
import MultiPoint from "ol/geom/MultiPoint";
import type Geometry from "ol/geom/Geometry";
import type GeometryCollection from "ol/geom/GeometryCollection";
import type Point from "ol/geom/Point";

export type MarkerSize = "small" | "medium" | "large";
export type MarkerStyle = "pin" | "shape";

/**
 * Built-in shapes for `marker-symbol`, modelled on the OGC SLD WellKnownNames.
 * SLD's "x" is a single letter, which simplestyle reserves for letter symbols,
 * so the diagonal cross is called "x-cross" here.
 */
export const MARKER_SHAPES = ["circle", "square", "triangle", "star", "cross", "x-cross"] as const;
export type MarkerShape = (typeof MARKER_SHAPES)[number];

/** The simplestyle 1.1.0 feature properties. */
export interface SimpleStyleProperties {
  title?: string;
  description?: string;
  "marker-size"?: MarkerSize;
  "marker-symbol"?: string;
  "marker-color"?: string;
  stroke?: string;
  "stroke-opacity"?: number;
  "stroke-width"?: number;
  fill?: string;
  "fill-opacity"?: number;
}

export interface SimpleStyleOptions {
  /** How point features are drawn: 'pin' (default) or 'shape'. */
  markerStyle?: MarkerStyle;
  /** Pin width in CSS pixels per marker size (height is 1.5 × width). */
  markerSizes?: Partial<Record<MarkerSize, number>>;
  /** Shape diameter in CSS pixels per marker size, for the 'shape' style. */
  shapeSizes?: Partial<Record<MarkerSize, number>>;
  /** Shape drawn in the 'shape' style when a feature has no (usable) marker-symbol. Default 'circle'. */
  defaultShape?: MarkerShape;
  /**
   * Resolves a `marker-symbol` icon ID to an image URL. Called for any symbol
   * that is not a digit, a lowercase letter or one of the built-in
   * MARKER_SHAPES. Receives the contrast color ('#000000' or '#ffffff') that
   * fits the marker color, so you can serve a matching icon.
   * Return `undefined` to draw no symbol for that ID.
   * Default: none.
   */
  markerSymbolUrl?: ((symbol: string, contrastColor: string) => string | undefined) | null;
  /** `crossOrigin` for symbol images (needed for hit detection on foreign hosts). Default 'anonymous'. */
  crossOrigin?: string | null;
  /** Font family for digit/letter symbols. */
  fontFamily?: string;
  /** Override the spec defaults (e.g. a different default marker color). */
  defaults?: Partial<SimpleStyleProperties>;
}

/** Defaults as defined by simplestyle-spec 1.1.0. */
export const SIMPLESTYLE_DEFAULTS = {
    "marker-size": "medium",
    "marker-symbol": "",
    "marker-color": "#7e7e7e",
    stroke: "#555555",
    "stroke-opacity": 1.0,
    "stroke-width": 2,
    fill: "#555555",
    "fill-opacity": 0.6,
} as const satisfies Required<Omit<SimpleStyleProperties, "title" | "description">>;

const DEFAULT_PIN_SIZES: Record<MarkerSize, number> = { small: 20, medium: 27, large: 34 };
const DEFAULT_SHAPE_SIZES: Record<MarkerSize, number> = { small: 12, medium: 18, large: 24 };

const isMarkerShape = (s: string): s is MarkerShape => (MARKER_SHAPES as readonly string[]).includes(s);
const isTextSymbol = (s: string) => /^([0-9]|[a-z])$/.test(s);

type RGB = [number, number, number];

/** Parses a simplestyle color ("#ace", "aaccee", ...). Returns null if invalid. */
export function parseColor(value: unknown): RGB | null {
    if (typeof value !== "string") return null;
    const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value.trim());
    if (!m) return null;
    let hex = m[1];
    if (hex.length === 3) hex = hex.replace(/./g, (c) => c + c);
    const n = Number.parseInt(hex, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function toNumber(value: unknown, fallback: number, min: number, max = Infinity): number {
    const n = typeof value === "number" ? value : typeof value === "string" && value.trim() !== "" ? Number(value) : NaN;
    return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
}

const hex = ([r, g, b]: RGB): string =>
    `#${  [r, g, b].map((c) => c.toString(16).padStart(2, "0")).join("")}`;

/**
 * The color for symbols drawn on top of the marker color: black on light
 * colors, white on dark ones (based on relative luminance).
 */
function contrastColor([r, g, b]: RGB): string {
    const lin = (c: number) => {
        const s = c / 255;
        return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    };
    const l = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    // 0.4 instead of the strict WCAG crossover (0.179): favours white on mid-tones like blue, red, grey
    return l > 0.4 ? "#000000" : "#ffffff";
}

function darken([r, g, b]: RGB, f = 0.7): RGB {
    return [Math.round(r * f), Math.round(g * f), Math.round(b * f)];
}

function pinSvg(color: RGB, width: number): string {
    const height = width * 1.5;
    const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 20 30">` +
    "<path d=\"M10 0.75C4.9 0.75 0.75 4.85 0.75 9.9 0.75 16.6 10 29 10 29S19.25 16.6 19.25 9.9C19.25 4.85 15.1 0.75 10 0.75Z\" " +
    `fill="${hex(color)}" stroke="${hex(darken(color))}" stroke-width="1.5"/></svg>`;
    return `data:image/svg+xml;charset=utf-8,${  encodeURIComponent(svg)}`;
}

/**
 * Draws a built-in shape of nominal diameter `d`, centred `dy` pixels above the point.
 * With `outline`, the shape gets a darker border (used for the 'shape' style).
 * Drawn locally by OpenLayers, no network access.
 */
function shapeImages(shape: MarkerShape, d: number, color: string, dy: number, outline?: string): ImageStyle[] {
    const r = d / 2;
    const fill = new Fill({ color });
    const stroke = outline ? new Stroke({ color: outline, width: 1.5 }) : undefined;
    switch (shape) {
        case "circle":
            return [new CircleStyle({ radius: r, fill, stroke, displacement: [0, dy]})];
        case "square":
            return [new RegularShape({ points: 4, radius: r * 1.2, angle: Math.PI / 4, fill, stroke, displacement: [0, dy]})];
        case "triangle": {
            // apex at +R, base at -R/2: shift down by R/4 to centre the bounding box
            const R = r * 1.3;
            return [new RegularShape({ points: 3, radius: R, fill, stroke, displacement: [0, dy - R / 4]})];
        }
        case "star": {
            const R = r * 1.3;
            return [new RegularShape({ points: 5, radius: R, radius2: R * 0.42, fill, stroke, displacement: [0, dy - R * 0.1]})];
        }
        case "cross":
        case "x-cross": {
            const angle = shape === "cross" ? 0 : Math.PI / 4;
            const w = Math.max(2, d * 0.26);
            const cross = (c: string, width: number) =>
                new RegularShape({
                    points: 4,
                    radius: r * 1.05,
                    radius2: 0,
                    angle,
                    stroke: new Stroke({ color: c, width, lineCap: "square" }),
                    displacement: [0, dy],
                });
            // outline: a wider cross in the outline color underneath
            return outline ? [cross(outline, w + 3), cross(color, w)] : [cross(color, w)];
        }
    }
}

/** Extracts all point coordinates of a GeometryCollection as one MultiPoint. */
function collectionPoints(feature: FeatureLike): Geometry | undefined {
    const geom = feature.getGeometry() as Geometry | undefined;
    if (geom?.getType() !== "GeometryCollection") return undefined;
    const coords: number[][] = [];
    const walk = (g: Geometry) => {
        const t = g.getType();
        if (t === "Point") coords.push((g as Point).getCoordinates());
        else if (t === "MultiPoint") coords.push(...(g as MultiPoint).getCoordinates());
        else if (t === "GeometryCollection") (g as GeometryCollection).getGeometriesArray().forEach(walk);
    };
    walk(geom);
    return coords.length ? new MultiPoint(coords) : undefined;
}

/** Creates an OpenLayers style function that renders features according to simplestyle-spec 1.1.0. */
export function createSimpleStyleFunction(options: SimpleStyleOptions = {}): StyleFunction {
    const mode: MarkerStyle = options.markerStyle ?? "pin";
    const pinSizes = { ...DEFAULT_PIN_SIZES, ...options.markerSizes };
    const shapeSizes = { ...DEFAULT_SHAPE_SIZES, ...options.shapeSizes };
    const defaultShape: MarkerShape = options.defaultShape ?? "circle";
    const symbolUrl = options.markerSymbolUrl ?? null;
    const crossOrigin = options.crossOrigin ?? "anonymous";
    const fontFamily = options.fontFamily ?? "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif";
    const defaults = { ...SIMPLESTYLE_DEFAULTS, ...options.defaults };
    const defaultMarkerColor = parseColor(defaults["marker-color"]) ?? [126, 126, 126];
    const defaultStroke = parseColor(defaults.stroke) ?? [85, 85, 85];
    const defaultFill = parseColor(defaults.fill) ?? [85, 85, 85];

    const markerCache = new Map<string, Style[]>();
    const pathCache = new Map<string, Style>();

    /** Text, icon or nothing for a non-shape symbol, centred `dy` pixels above the point. */
    function symbolStyle(symbol: string, size: number, fg: string, dy: number, geometry?: typeof collectionPoints) {
        if (isTextSymbol(symbol)) {
            return new Style({
                geometry,
                text: new Text({
                    text: symbol,
                    font: `bold ${Math.round(size)}px ${fontFamily}`,
                    fill: new Fill({ color: fg }),
                    offsetY: -dy,
                    textAlign: "center",
                    textBaseline: "middle",
                    overflow: true,
                }),
            });
        }
        const src = symbol && symbolUrl ? symbolUrl(symbol, fg) : undefined;
        if (!src) return undefined;
        const s = Math.round(size);
        return new Style({
            geometry,
            image: new Icon({ src, width: s, height: s, anchor: [0.5, 0.5], displacement: [0, dy], crossOrigin }),
        });
    }

    /** Styles for a marker; for collections they are restricted to the point members. */
    function markerStyles(feature: FeatureLike, forCollection: boolean): Style[] {
        const sizeProp = feature.get("marker-size");
        const size: MarkerSize =
      typeof sizeProp === "string" && Object.hasOwn(DEFAULT_PIN_SIZES, sizeProp)
          ? (sizeProp as MarkerSize)
          : (defaults["marker-size"] as MarkerSize);
        const color = parseColor(feature.get("marker-color")) ?? defaultMarkerColor;
        const rawSymbol = feature.get("marker-symbol");
        const symbol =
      rawSymbol === undefined || rawSymbol === null ? String(defaults["marker-symbol"]) : String(rawSymbol).trim();

        const key = `${size}|${hex(color)}|${symbol}|${forCollection}`;
        let styles = markerCache.get(key);
        if (styles) return styles;

        const geometry = forCollection ? collectionPoints : undefined;
        const fg = contrastColor(color);
        const fromImages = (images: ImageStyle[]) => images.map((image) => new Style({ geometry, image }));

        if (mode === "pin") {
            const width = pinSizes[size];
            const height = width * 1.5;
            // centre of the pin head, measured upwards from the tip (head centre is at y=10 of 30)
            const head = height * (20 / 30);
            styles = fromImages([new Icon({ src: pinSvg(color, width), width, height, anchor: [0.5, 1]})]);
            if (isMarkerShape(symbol)) {
                styles.push(...fromImages(shapeImages(symbol, width * 0.46, fg, head)));
            } else {
                const s = symbolStyle(symbol, width * 0.55, fg, head, geometry);
                if (s) styles.push(s);
            }
        } else {
            const d = shapeSizes[size];
            const outline = hex(darken(color));
            const badge = isTextSymbol(symbol) ? symbolStyle(symbol, d * 0.75, fg, 0, geometry) : undefined;
            const icon = !badge && !isMarkerShape(symbol) ? symbolStyle(symbol, d * 0.75, fg, 0, geometry) : undefined;
            if (badge || icon) {
                // digits, letters and icons sit in a round badge in the marker color
                styles = [...fromImages(shapeImages("circle", d * 1.25, hex(color), 0, outline)), (badge ?? icon)!];
            } else {
                styles = fromImages(shapeImages(isMarkerShape(symbol) ? symbol : defaultShape, d, hex(color), 0, outline));
            }
        }

        markerCache.set(key, styles);
        return styles;
    }

    function pathStyle(feature: FeatureLike, isLine: boolean): Style {
        const stroke = parseColor(feature.get("stroke")) ?? defaultStroke;
        const strokeOpacity = toNumber(feature.get("stroke-opacity"), defaults["stroke-opacity"], 0, 1);
        const strokeWidth = toNumber(feature.get("stroke-width"), defaults["stroke-width"], 0);
        const fill = parseColor(feature.get("fill")) ?? defaultFill;
        const fillOpacity = toNumber(feature.get("fill-opacity"), defaults["fill-opacity"], 0, 1);

        const key = `${hex(stroke)}|${strokeOpacity}|${strokeWidth}|${hex(fill)}|${fillOpacity}|${isLine}`;
        let style = pathCache.get(key);
        if (style) return style;

        style = new Style({
            // A zero width would be ignored by canvas (keeping the previous width), so omit the stroke instead.
            stroke:
        strokeWidth > 0 && strokeOpacity > 0
            ? new Stroke({ color: [...stroke, strokeOpacity], width: strokeWidth, lineCap: "round", lineJoin: "round" })
            : undefined,
            // Spec: fill on LineStrings is undefined; OL never fills lines anyway.
            // A fully transparent fill is kept so polygons stay hit-detectable.
            fill: isLine ? undefined : new Fill({ color: [...fill, fillOpacity]}),
        });
        pathCache.set(key, style);
        return style;
    }

    return (feature: FeatureLike): Style | Style[] | undefined => {
        const type = feature.getGeometry()?.getType();
        switch (type) {
            case "Point":
            case "MultiPoint":
                return markerStyles(feature, false);
            case "LineString":
            case "MultiLineString":
            case "LinearRing":
                return pathStyle(feature, true);
            case "Polygon":
            case "MultiPolygon":
            case "Circle":
                return pathStyle(feature, false);
            case "GeometryCollection":
                // The path style ignores point members; the marker styles only draw the point members.
                return [pathStyle(feature, false), ...markerStyles(feature, true)];
            default:
                return undefined;
        }
    };
}

/** Ready-to-use style function with default options. */
export const simpleStyleFunction: StyleFunction = createSimpleStyleFunction();

export default simpleStyleFunction;
