import './ol-print-layout-control.css';
import Control from 'ol/control/Control';
import { Map, MapEvent, Object as OlObject } from 'ol';
export declare enum ORIENTATION {
    PORTRAIT = "portrait",
    LANDSCAPE = "landscape"
}
export declare const PAPER_FORMAT: {
    readonly A4: "A4";
    readonly A3: "A3";
    readonly A2: "A2";
    readonly A1: "A1";
    readonly A0: "A0";
    readonly LETTER: "LETTER";
    readonly TABLOID: "TABLOID";
    readonly BROADSHEET: "BROADSHEET";
};
export declare type Options = {
    margin?: MarginProps;
    format?: typeof PAPER_FORMAT[keyof typeof PAPER_FORMAT];
    orientation?: typeof ORIENTATION[keyof typeof ORIENTATION];
};
/**
 * The print-layout-control.
 * Add an instance of this to your OpenLayers Map.
 * @param {Options} [{format: 'A4', orientation: 'portrait', margin: {top: 2, bottom: 2, left: 2, right: 2}}] opt_options
 */
export declare class PrintLayout extends Control {
    private printArea;
    private evtKeyMarginChange;
    constructor(opt_options?: Options);
    /**
     * @public
     */
    getOrientation(): any;
    /**
     * @public
     * @param {ORIENTATION} orientation
     */
    setOrientation(orientation: ORIENTATION): void;
    /**
     * @public
     */
    getFormat(): any;
    /**
     * @public
     * @param format
     */
    setFormat(format: typeof PAPER_FORMAT[keyof typeof PAPER_FORMAT]): void;
    /**
     * @public
     */
    getMargin(): Margin;
    /**
     * @public
     * @param {Margin} margin
     */
    setMargin(margin: Margin): void;
    /**
     * @public
     */
    getBbox(): any;
    /**
     * @public
     */
    getBboxAsLonLat(): import("ol/extent").Extent | null;
    protected computeBbox(): number[] | null;
    /**
     * Computes the scale denominator for the printed map
     * @public
     */
    getScaleDenominator(): number | null;
    /**
     * Get the print box size (width, height) in dots (px) for printing.
     *
     * This is useful to determine the OGC-WMS params 'WIDTH' and 'HEIGHT'
     * @public
     * @param dpi {number} the desired print resolution in dots-per-inch (dpi)
     * @returns {{width: number, height: number}}
     */
    getPrintBoxSizeInDots(dpi?: number): {
        width: number;
        height: number;
    };
    /**
     * @public
     */
    getPrintBoxSizeInMM(): {
        width: number;
        height: number;
    };
    protected getPrintMarginsInPx(): MarginProps;
    protected getScreenMapAspectRatio(): number;
    protected getPaperMapAspectRatio(): number;
    protected getRestrictingDimension(): "width" | "height";
    protected setElementSize(): void;
    handleBboxChange(): void;
    _map: Map | null | undefined;
    onRender(_mapEvent: MapEvent): void;
}
/**
 *
 */
declare type MarginProps = {
    top: number;
    bottom: number;
    left: number;
    right: number;
};
/**
 * The Margin Class to set paper margins in cm.
 */
export declare class Margin extends OlObject {
    constructor(marginProps?: Partial<MarginProps>);
    /**
     * @public
     */
    getProperties(): MarginProps;
    /**
     * @public
     */
    getTop(): any;
    /**
     * @public
     * @param topMarginInCm
     */
    setTop(topMarginInCm: number): void;
    /**
     * @public
     */
    getBottom(): any;
    /**
     * @public
     * @param bottomMarginInCm
     */
    setBottom(bottomMarginInCm: number): void;
    /**
     * @public
     */
    getLeft(): any;
    /**
     * @public
     * @param leftMarginInCm
     */
    setLeft(leftMarginInCm: number): void;
    /**
     * @public
     */
    getRight(): any;
    /**
     * @public
     * @param rightMarginInCm
     */
    setRight(rightMarginInCm: number): void;
}
export {};
