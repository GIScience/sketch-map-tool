export class OpenAerialMapService {
    //stac api: https://hotosm.github.io/swagger/?url=https://api.imagery.hotosm.org/stac/api
    // --> get metadata from stac api
    //metadataUrl = "https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/59e62beb3d6412ef7220c58e"

    //raster api swagger: https://hotosm.github.io/swagger/?url=https://api.imagery.hotosm.org/raster/api
    // --> get Tiles
    static baseApiUrl = "https://api.imagery.hotosm.org";
    static stacApiUrl = `${this.baseApiUrl}/stac`;
    static rasterApiUrl = `${this.baseApiUrl}/raster`;
    static collectionId = "openaerialmap";
    static tileMatrixSetId = "WebMercatorQuad"

    //itemId = "59e62beb3d6412ef7220c58e" //2015-04-17_bugurunni_merged_transparent_mosaic_group1

    //TileJSON
    // https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/59e62beb3d6412ef7220c58e/WebMercatorQuad/tilejson.json?tile_scale=1&assets=visual
    // contains bbox, center, maxZoom, tileURL
    // can be used for ol.source.TileJSON
    //example: https://openlayers.org/en/latest/examples/tilejson.html


    // itemAssets = "https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/59e62beb3d6412ef7220c58e/assets"
    // -> "visual"
    // templateURL = `${this.apiUrl}/collections/${this.collectionId}/items/${this.itemId}/tiles/${this.tileMatrixSet}/{z}/{x}/{y}.png?assets=visual&nodata=0`
    // exampleURL = "https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/59e62beb3d6412ef7220c58e/tiles/WebMercatorQuad/16/39910/34015.png?assets=visual&nodata=0"


    static getMetadataUrl(itemId: string) {
        return `${this.stacApiUrl}/collections/${this.collectionId}/items/${itemId}`;
    }

    static getTileUrl(itemId: string) {
        return `${this.rasterApiUrl}/collections/${this.collectionId}/items/${itemId}/tiles/${this.tileMatrixSetId}/{z}/{x}/{y}.png?assets=visual&nodata=0`;
    }

    static getTileJsonUrl(itemId: string) {
        return `${this.rasterApiUrl}/collections/${this.collectionId}/items/${itemId}/${this.tileMatrixSetId}/tilejson.json?assets=visual&nodata=0`;
    }

    static async getMetadata(itemId: string) {
        return await this.getJSON(this.getMetadataUrl(itemId));
    }

    static async getTileJson(itemId: string) {
        return await this.getJSON(this.getTileJsonUrl(itemId));
    }

    /**
     * Generic fetch function to get JSON documents
     * @param url
     */
    static async getJSON(url: string) {
        try {
            const response = await fetch(url, {mode: "cors"});

            // Handle non-OK responses (e.g., 404, 500)
            if (!response.ok) {
                // Try to extract server error message if present
                const text = await response.text().catch(() => "");
                throw new Error(`Request failed (${response.status}): ${text || response.statusText}`);
            }

            // Try parsing JSON safely
            return await response.json().catch(() => {
                throw new Error("Invalid JSON response");
            });

        } catch (err) {
            // Handle network or parsing errors
            console.error(`Failed to fetch ${url}:`, err);
            throw err; // rethrow for caller to handle if needed
        }
    }
}