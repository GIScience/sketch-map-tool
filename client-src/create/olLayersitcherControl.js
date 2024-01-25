import { Control } from "ol/control";
import { CLASS_CONTROL, CLASS_UNSELECTABLE } from "ol/css";
import "./olLayerswitcherControl.css";

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
        const nextLayersIndex = (this.activeLayerIdx + 1) % this.layersList.length;
        return this.layers[this.layersList[nextLayersIndex]].class;
    }

    getNextLayersButtonLabel() {
        return this.getNextLayersProperty("label");
    }

    getNextLayersProperty(property) {
        const nextLayersIndex = (this.activeLayerIdx + 1) % this.layersList.length;
        return this.layers[this.layersList[nextLayersIndex]][property];
    }
}
