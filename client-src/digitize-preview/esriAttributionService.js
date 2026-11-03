// import { ViewStateLayerStateExtent } from "ol/View";
import { transformExtent } from "ol/proj";
import { intersects } from "ol/extent";

export class EsriAttributionService {
    constructor() {
        this.attributionURL = "https://static.arcgis.com/attribution/World_Imagery?f=json";
        this.fallBackAttribution = "Satellite Layer \"World_Imagery\" powered by Esri. Source: ESRI, Maxar, Earthstar Geographics, and the GIS User Community";
        this.attributions = undefined;
        this.serviceAvailable = true;
    }

    async initialize() {
        try {
            const response = await fetch(this.attributionURL);
            if (response.ok) {
                this.attributions = await response.json();
            } else {
                this.serviceAvailable = false;
            }
        } catch (e) {
            this.serviceAvailable = false;
        }
    }

    /**
     * This funtion implements an ol.Source Attribution() function
     * @param {ol.view.ViewStateLayerStateExtent} viewStateLayerStateExtent this param is provided
     *          by the ol.Source attributions property when used as Attribution callback function
     *          see: {@link https://openlayers.org/en/latest/apidoc/module-ol_View.html#~ViewStateLayerStateExtent ViewStateLayerStateExtent}
     */
    getAttributionsByZoomAndExtent(viewStateLayerStateExtent) {
        // initialize when calling for the first time
        if (this.attributions === undefined) {
            this.initialize();
            if (!this.serviceAvailable) {
                return this.fallBackAttribution;
            }
        }

        const { zoom } = viewStateLayerStateExtent.viewState;
        const extent = transformExtent(viewStateLayerStateExtent.extent, viewStateLayerStateExtent.viewState.projection, "EPSG:4326");

        const contributors = this.attributions?.contributors;
        if (!(contributors instanceof Array)) {
            return this.fallBackAttribution;
        }

        // checks if a contributor has any valid coverageArea within the current map view
        const contributorFilter = (contributor) => {
            // change of image sources is between full zoomlevels
            // this is important as openlayers can use fractional zoomlevels like 11.48
            const zoomFilter = (coverageArea) => (
                zoom >= coverageArea.zoomMin - 0.5
                && zoom < coverageArea.zoomMax + 0.5
            );
            const extentFilter = (coverageArea) => {
                // esri coverageArea bboxes have flipped coords
                // to compare with ol map extent we have to flip again
                const [y1, x1, y2, x2] = coverageArea.bbox;
                return intersects(extent, [x1, y1, x2, y2]);
            };

            const validCoverageAreas = contributor.coverageAreas
                .filter(zoomFilter)
                .filter(extentFilter);

            // has valid coverageAreas?
            return validCoverageAreas.length > 0;
        };

        // every contributor can have multiple coverageAreas.
        // These are defined by zoomMin, zoomMax and bbox with LonLat Coords
        const currentContributors = contributors
            .filter(contributorFilter)
            .map((contributor) => contributor.attribution)
            .join(",");

        return `Satellite layer powered by ESRI. Source: ${currentContributors}`;
    }

    createAttributionFunction() {
        return this.getAttributionsByZoomAndExtent.bind(this);
    }
}
