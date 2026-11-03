import { Control } from "ol/control";
import { CLASS_CONTROL, CLASS_UNSELECTABLE } from "ol/css";
import "./ol-LayerSwitcherControl.css";
import BaseLayer from "ol/layer/Base";

/**
 * This layerSwitcher control is made to switch between one of 2 or more other baselayers.
 * The ol Map can have more other overlay layers which are not affected by this control.
 * There will be one button iterating through all configured layers and then start from the
 * beginning again.
 *
 * How to use:
 * 1. The layers that should be handled by this control must have the following properties set
 *      in the options object when creating the layers:
 *
 *      "ls_visible" {boolean} - determines whether a layer should be managed by the LayerSwitcher or not
 *
 *      "ls_label" {string} - The text to be displayed on the LayerSwitcher-Button
 *
 *      "ls_class" {string} - A css className to style the LayerSwitcher-Button (see 3.)
 *
 *      "name" {string} - give your layer a name such that we can identify it with the LayerSwitcher
 *
 *      "visible" {boolean} -   only one of your baselayers should be visible when the control is
 *                              added to the map and initialized
 *
 *
 * 2. When instantiating the new LayerSwitcher(options) pass an options Object
 *      with the following properties:
 *
 *      "target" - optional. If you don't specify a different DIV it will be shown in the Map
 *
 * 3. Add css "classes" to your code to style the LayerSwitcher-Button for each Layer differently
 *      @example
 *      .ol-control.layerswitcher button.osm {
 *        background-color: palegoldenrod;
 *      }
 *      .ol-control.layerswitcher button.satellite {
 *        background-color: darkolivegreen;
 *      }
 *
 * 4. Add it to the map as usual with map.addControl(layerSwitcher);
 *
 * 5. run layerSwitcher.initialize() once after adding it to the map.
 *      The LayerSwitcher will iterate over the Layers already attached to the map and link those
 *      to the LayerSwitcher which at least have a "ls_visible" {boolean} property set as a layer property
 *
 * 6. If you need to react on a layer switch event you can register one like:
 *      @example
 *      layerSwitcherControl.on("change:activeLayer", handleLayerSwitch);
 *      function handleLayerSwitch(event){
 *          const layer = event.target.get("activeLayer");
 *          console.log(layer.get("name"));
 *      }
 */
export class LayerSwitcher extends Control {

    baseCssClassName;
    button; //: HTMLButtonElement;

    activeLayerIdx = -1; //: number;

    ls_layers: BaseLayer[];

    constructor(options) {
        const {
            target,
        } = options;

        const element = document.createElement("div");
        const baseCssClassName = "layerswitcher";
        element.className = `${baseCssClassName} ${CLASS_CONTROL} ${CLASS_UNSELECTABLE}`;

        const button = document.createElement("button");
        button.className = `${baseCssClassName}-btn`;

        button.setAttribute("type", "button");
        element.appendChild(button);

        const slot = document.createElement("div");
        slot.setAttribute("id", `slot`);
        element.appendChild(slot);

        super({
            element,
            target,
        });

        this.baseCssClassName = baseCssClassName;
        this.button = button;

        this.ls_layers = [];
    }

    initialize() {

        //register already added layers in layerswitcher
        const existingLayers = this.getMap().getAllLayers();
        existingLayers.forEach(this.addLayer.bind(this));

        // register map event to check whether a future layer should be added to layerswitcher or not
        this.getMap().getLayers().on('add', (event) => {
            this.addLayer(event.element);
        });

        this.getMap().getLayers().on('remove', (event) => {
            console.log('onremove from layerswitcher');
            const removedLayer = event.element;
            //check if removed layer is managed by layerswitcher and remove it
            this.removeLayer(removedLayer);
        });


        //activate first layer if none was set to visible
        const mapHasNoVisibleLayers = this.getMap().getAllLayers()
            .map((layer) => layer.getVisible())
            .every((isVisible) => isVisible === false)

        if (mapHasNoVisibleLayers) {
            this.activateLayerAtIndex(0);
        }

        this.button.addEventListener("click", this.activateNextLayer.bind(this));
    }

    removeLayer(layer: BaseLayer) {
        const layerIndexToRemove = this.ls_layers.findIndex(value => {
            console.log(layer.get("name"), value.get("name"), value === layer);
            return value === layer;
        });
        console.log("layerIndex", layerIndexToRemove)
        if (layerIndexToRemove === -1) {
            console.warn('Removed Layer was not managed by LayerSwitcher.', layer);
            return;
        }

        //update active layerIndex
        if (layerIndexToRemove < this.activeLayerIdx) {
            this.activeLayerIdx--;
        }

        // remove from layerswitcher layers
        this.ls_layers.splice(layerIndexToRemove, 1);

        // refresh layer and button
        this.activateLayerAtIndex(this.activeLayerIdx);

    }

    addLayer(layer: BaseLayer) {

        //check whether this layer should be managed by the layerswitcher
        if (!layer.get("ls_visible")) {
            console.warn('Layer has no "ls_visible" property and thus will not be added to the LayerSwitcher.', layer)
            return;
        }

        const currentLayerIsLast = this.activeLayerIdx === this.ls_layers.length - 1;

        this.ls_layers.push(layer)

        if (layer.getVisible()) {
            // store current layer
            this.activeLayerIdx = this.ls_layers.length - 1;

            //update button
            this.updateNextLayerButton();

            // update map
            // deactivate all layers and activate next
            this.ls_layers.forEach((layer) => layer.setVisible(false));
            layer.setVisible(true);

            // update observable property
            this.set("activeLayer", layer);

        } else if (currentLayerIsLast) {
            // set class
            this.setNextLayersButtonClass(layer.get("ls_class") ?? "default");
            // set label
            this.button.innerText = layer.get("ls_label") ?? layer.get("name") ?? "Layer has no 'ls_label' property";
        }
    }

    activateLayerAtIndex(index) {
        // next layer to activate
        this.activeLayerIdx = index % this.ls_layers.length;

        const newLayer = this.ls_layers[this.activeLayerIdx];
        newLayer.setVisible(true);
        this.set("activeLayer", newLayer);

        this.updateNextLayerButton();
    }

    updateNextLayerButton() {
        //set class
        this.setNextLayersButtonClass(this.getNextLayersButtonClass());

        // set label
        this.button.innerText = this.getNextLayersButtonLabel();
    }

    activateNextLayer() {
        // deactivate all layers and activate next
        // this.ls_layers.forEach((layer) => layer.setVisible(false));
        this.getMap().getAllLayers().forEach((layer) => layer.setVisible(false));
        this.activateLayerAtIndex(this.activeLayerIdx + 1);
    }

    getNextLayersButtonClass() {
        return this.getNextLayersProperty("ls_class");
    }

    getNextLayersButtonLabel() {
        return this.getNextLayersProperty("ls_label");
    }

    getNextLayersProperty(property) {
        const nextLayersIndex = (this.activeLayerIdx + 1) % this.ls_layers.length;
        return this.ls_layers[nextLayersIndex].get(property);
    }

    setNextLayersButtonClass(className) {
        this.button.className = `${this.baseCssClassName}-btn ${className}`;
    }

    suspend() {
        this.ls_layers.forEach((layer) => layer.setVisible(false));
    }

}
