import { Control } from "ol/control";
import { CLASS_CONTROL, CLASS_UNSELECTABLE } from "ol/css";
import "./olLayerswitcherControl.css";

/**
 * This layerswitcher control is made to switch between one of 2 or more other baselayers.
 * The ol Map can have more other overlay layers which are not affected by this control.
 * There will be one button iterating through all configured layers and then start from the
 * beginning again.
 *
 * How to use:
 * 1. The layers that should be handled by this control must have the following properties set
 *      in the options object when creating the layers:
 *
 *      "name" {string} - give your layer a name such that we can identify it with the LayerSwitcher
 *
 *      "visible" {boolean} -   only one of your baselayers should be visible when the control is
 *                              added to the map and initialized
 * 2. When initializing the new LayerSwitcher(options) pass an options Object
 *      with the following properties:
 *
 *      "target" - optional. If you don't specify a different DIV it will be shown in the Map
 *      "layers" - required. An array of objects {Array<LSLayerConfig>}
 *
 *      @example
 *      {layers: [
 *        {
 *          name: "OSM Basemap",
 *          label: "OSM",
 *          class: "osm"
 *        },
 *        {
 *          name: "Some Satellite Layer Provider",
 *          label: "Satellite",
 *          class: "satellite"
 *        }
 *      ]}
 * 3. Add css "classes" to your code to style the LayerSwitcher Button for each Layer differently
 *      @example:
 *      .ol-control.layerswitcher button.osm {
 *        background-color: palegoldenrod;
 *      }
 *      .ol-control.layerswitcher button.satellite {
 *        background-color: darkolivegreen;
 *      }
 * 4. Add it to the map as usual with map.addControl(layerswitcher);
 * 5. run layerswitcher.initialize() once after adding it to the map.
 *      The Layerswitcher will iterate over the Layers already attached to the map an link them by
 *      their "name" property to the LayerSwitcher
 */
export class LayerSwitcher extends Control {
    constructor(options = {}) {
        const {
            layers,
            target,
        } = options;

        const element = document.createElement("div");
        const className = "layerswitcher";
        element.className = `${className} ${CLASS_CONTROL} ${CLASS_UNSELECTABLE}`;

        const button = document.createElement("button");
        button.className = `${className}-btn`;

        button.setAttribute("type", "button");
        element.appendChild(button);
        super({
            element,
            target,
        });

        this.button = button;
        this.layers = layers.reduce((previousValue, currentValue) => ({
            ...previousValue,
            [currentValue.name]: currentValue,
        }), {});
        this.layersList = Object.keys(this.layers);
    }

    initialize() {
        this.getMap()
            .getLayers()
            .forEach((layer) => {
                const name = layer.get("name");
                if (this.layersList.includes(name)) {
                    this.layers[name].layerRef = layer;
                    if (layer.getVisible()) {
                        // store current layer
                        this.activeLayerIdx = this.layersList.indexOf(name);
                        // set class
                        const nextLayersButtonClass = this.getNextLayersButtonClass();
                        this.button.classList.add(nextLayersButtonClass);
                        // set label
                        this.button.innerText = this.getNextLayersButtonLabel();
                    }
                }
            });
        this.button.addEventListener("click", this.activateNextLayer.bind(this));
    }

    activateNextLayer() {
        // deactivate all layers and activate next
        Object.values(this.layers)
            .forEach((layer) => layer.layerRef.setVisible(false));

        // get old Class before updating active layer
        const oldClass = this.getNextLayersButtonClass();

        // next layer to activate
        this.activeLayerIdx = ++this.activeLayerIdx % this.layersList.length;

        this.layers[this.layersList[this.activeLayerIdx]].layerRef.setVisible(true);

        // update css class
        // remove old class
        this.button.classList.remove(oldClass);

        // add new class
        const newClass = this.getNextLayersButtonClass();
        this.button.classList.add(newClass);

        // set label
        this.button.innerText = this.getNextLayersButtonLabel();
    }

    getNextLayersButtonClass() {
        return this.getNextLayersProperty("class");
    }

    getNextLayersButtonLabel() {
        return this.getNextLayersProperty("label");
    }

    getNextLayersProperty(property) {
        const nextLayersIndex = (this.activeLayerIdx + 1) % this.layersList.length;
        return this.layers[this.layersList[nextLayersIndex]][property];
    }
}
