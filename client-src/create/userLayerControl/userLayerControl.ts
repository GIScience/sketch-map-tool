import { Control } from "ol/control";
import { CLASS_CONTROL, CLASS_UNSELECTABLE } from "ol/css";
import "./userLayerControl.css";
import BaseLayer from "ol/layer/Base";
import { UserLayerButton } from "./userLayerButton";

export class UserLayerControl extends Control {

    userLayer: BaseLayer;
    isLoading: boolean;


    constructor(options) {
        const {
            target,
        } = options;

        const element = document.createElement("div");
        const baseCssClassName = "userlayer-ctl";
        element.className = `${baseCssClassName} ${CLASS_CONTROL} ${CLASS_UNSELECTABLE}`;

        const shadowRoot = element.attachShadow({ mode: "open" });

        window.customElements.define("user-layer-button", UserLayerButton);

        shadowRoot.innerHTML = `
<style>
:host {
    margin-top: 0.5rem;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
    overflow: visible;
    width: 100%;
}

user-layer-button,
user-layer-button:hover,
user-layer-button:focus,
button,
button:hover,
button:focus {
    flex: 0 0 auto;
    /*margin-top: 0.5rem;*/
    height: 2.75rem;
    width: 2.75rem;
    color: white;
    font-size: 0.5rem;
    font-weight: bold;
    text-shadow: black 0 0 3px;
    line-height: 1em;
    background-color: white;
    border-radius: 4px;
    border: 1px solid lightgray;
    padding: 0;
    overflow: visible;
    cursor: pointer;
} 

#add-layer-container {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;  
    transition: display 0s ease-in-out 2s;
    & input {
        width: 0;
        opacity: 0;
        visibility: hidden;
        transition: all 0.2s;
        flex: 1 1 auto;
        align-self: start;
        font-size: 0.8rem;
        height: 1rem;
        border: none;
        outline: 1px solid lightgray;
        border-radius: 2px;/*0.25rem;*/
        padding: 5px;
        &:focus {
            outline: none;
            box-shadow: inset 0 0 0 1px #4d90fe,inset 0 0 5px #4d90fe;
        }
        &.expanded {
            visibility: visible;
            opacity: 100%;
            width: 30ex;   
        }
    }
}

button.add-layer-btn {
    /* OpenAerialMap Logo © 2016, Development Seed from https://de.wikipedia.org/wiki/Datei:OpenAerialMap_logo.svg */
    background-image: url('data:image/svg+xml,<%3Fxml version="1.0" encoding="utf-8"%3F><svg version="1.1" id="oam-logo-v-pos" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="100%" height="100%" viewBox="0 0 576 464" enable-background="new 0 0 576 464" xml:space="preserve"><g><path fill="%23203C46" d="M52.5,417.5c0,9.2-2.3,16.2-6.8,21.2c-4.5,4.9-11,7.4-19.5,7.4s-14.9-2.5-19.5-7.4c-4.5-4.9-6.8-12-6.8-21.2c0-9.2,2.3-16.3,6.8-21.2c4.5-4.9,11.1-7.3,19.5-7.3s15,2.5,19.5,7.4C50.3,401.3,52.5,408.3,52.5,417.5z M12.3,417.5c0,6.2,1.2,10.9,3.5,14c2.3,3.1,5.8,4.7,10.5,4.7c9.3,0,14-6.2,14-18.7c0-12.5-4.6-18.7-13.9-18.7c-4.7,0-8.2,1.6-10.5,4.7C13.4,406.7,12.3,411.3,12.3,417.5z"/><path fill="%23203C46" d="M84.8,446.1c-5,0-8.8-1.8-11.7-5.4h-0.6c0.4,3.5,0.6,5.6,0.6,6.1V464H61.6v-61.1h9.4l1.6,5.5h0.5c2.7-4.2,6.7-6.3,12-6.3c5,0,8.9,1.9,11.7,5.8c2.8,3.9,4.2,9.2,4.2,16.1c0,4.5-0.7,8.5-2,11.8c-1.3,3.3-3.2,5.9-5.6,7.6C90.9,445.2,88.1,446.1,84.8,446.1z M81.4,411.4c-2.8,0-4.9,0.9-6.2,2.6c-1.3,1.8-2,4.7-2,8.7v1.3c0,4.6,0.7,7.8,2,9.8c1.3,2,3.5,3,6.4,3c5.2,0,7.7-4.3,7.7-12.8c0-4.2-0.6-7.3-1.9-9.4C86.1,412.4,84.1,411.4,81.4,411.4z"/><path fill="%23203C46" d="M128.5,446.1c-6.8,0-12.1-1.9-15.9-5.7c-3.8-3.8-5.7-9.1-5.7-16c0-7.1,1.8-12.6,5.3-16.5c3.5-3.9,8.4-5.8,14.7-5.8c6,0,10.6,1.7,13.9,5.1c3.3,3.4,5,8.1,5,14.2v5.6h-27.2c0.1,3.3,1.1,5.9,2.9,7.7c1.8,1.8,4.4,2.8,7.6,2.8c2.5,0,4.9-0.3,7.2-0.8c2.3-0.5,4.6-1.4,7.1-2.5v9c-2,1-4.2,1.8-6.5,2.3C134.6,445.8,131.8,446.1,128.5,446.1z M126.9,410.4c-2.4,0-4.4,0.8-5.7,2.3c-1.4,1.6-2.2,3.8-2.4,6.6h16.2c-0.1-2.9-0.8-5.1-2.2-6.6C131.2,411.1,129.3,410.4,126.9,410.4z"/><path fill="%23203C46" d="M192.7,445.3h-11.5v-24.8c0-3.1-0.5-5.4-1.6-6.9c-1.1-1.5-2.8-2.3-5.2-2.3c-3.2,0-5.5,1.1-7,3.2s-2.2,5.7-2.2,10.8v20h-11.5v-42.4h8.8l1.5,5.4h0.6c1.3-2,3.1-3.6,5.3-4.6c2.3-1,4.8-1.6,7.7-1.6c4.9,0,8.6,1.3,11.2,4c2.5,2.7,3.8,6.5,3.8,11.6V445.3z"/><path fill="%23203C46" d="M238.8,445.3l-4-13.2h-20.1l-4,13.2h-12.6l19.5-55.7h14.3l19.6,55.7H238.8z M232,422.3c-3.7-12-5.8-18.7-6.2-20.3c-0.5-1.6-0.8-2.8-1-3.7c-0.8,3.2-3.2,11.2-7.1,24H232z"/><path fill="%23203C46" d="M274.8,446.1c-6.8,0-12.1-1.9-15.9-5.7c-3.8-3.8-5.7-9.1-5.7-16c0-7.1,1.8-12.6,5.3-16.5c3.5-3.9,8.4-5.8,14.7-5.8c6,0,10.6,1.7,13.9,5.1s5,8.1,5,14.2v5.6h-27.2c0.1,3.3,1.1,5.9,2.9,7.7c1.8,1.8,4.4,2.8,7.6,2.8c2.5,0,4.9-0.3,7.2-0.8c2.3-0.5,4.6-1.4,7.1-2.5v9c-2,1-4.2,1.8-6.5,2.3C280.9,445.8,278.1,446.1,274.8,446.1z M273.1,410.4c-2.4,0-4.4,0.8-5.7,2.3c-1.4,1.6-2.2,3.8-2.4,6.6h16.2c0-2.9-0.8-5.1-2.2-6.6C277.5,411.1,275.6,410.4,273.1,410.4z"/><path fill="%23203C46" d="M323.6,402.1c1.6,0,2.9,0.1,3.9,0.3l-0.9,10.9c-0.9-0.3-2.1-0.4-3.4-0.4c-3.7,0-6.5,0.9-8.6,2.8c-2.1,1.9-3.1,4.6-3.1,8v21.6H300v-42.4h8.7l1.7,7.1h0.6c1.3-2.4,3.1-4.3,5.3-5.7C318.5,402.8,320.9,402.1,323.6,402.1z"/><path fill="%23203C46" d="M332.7,392c0-3.8,2.1-5.7,6.3-5.7c4.2,0,6.3,1.9,6.3,5.7c0,1.8-0.5,3.2-1.6,4.2c-1,1-2.6,1.5-4.7,1.5C334.8,397.6,332.7,395.7,332.7,392z M344.7,445.3h-11.5v-42.4h11.5V445.3z"/><path fill="%23203C46" d="M381.5,445.3l-2.2-5.8H379c-1.9,2.5-3.9,4.2-6,5.1c-2.1,0.9-4.7,1.4-8,1.4c-4.1,0-7.2-1.2-9.6-3.5c-2.3-2.3-3.5-5.6-3.5-9.9c0-4.5,1.6-7.8,4.7-10c3.1-2.1,7.9-3.3,14.2-3.5l7.3-0.2v-1.9c0-4.3-2.2-6.4-6.6-6.4c-3.4,0-7.3,1-11.9,3.1l-3.8-7.8c4.9-2.6,10.2-3.8,16.2-3.8c5.7,0,10,1.2,13,3.7c3,2.5,4.5,6.2,4.5,11.3v28.3H381.5z M378.1,425.7l-4.5,0.2c-3.3,0.1-5.8,0.7-7.5,1.8c-1.6,1.1-2.5,2.8-2.5,5.1c0,3.3,1.9,4.9,5.6,4.9c2.7,0,4.8-0.8,6.4-2.3c1.6-1.5,2.4-3.6,2.4-6.1V425.7z"/><path fill="%23203C46" d="M410.9,445.3h-11.5v-59h11.5V445.3z"/><path fill="%23203C46" d="M445.3,445.3L432,401.8h-0.3c0.5,8.9,0.7,14.8,0.7,17.7v25.8h-10.5v-55.5h15.9l13.1,42.4h0.2l13.9-42.4h15.9v55.5H470v-26.3c0-1.2,0-2.7,0.1-4.3c0-1.6,0.2-5.9,0.5-12.9h-0.3L456,445.3H445.3z"/><path fill="%23203C46" d="M518.7,445.3l-2.2-5.8h-0.3c-1.9,2.5-3.9,4.2-6,5.1c-2.1,0.9-4.7,1.4-8,1.4c-4.1,0-7.2-1.2-9.6-3.5c-2.3-2.3-3.5-5.6-3.5-9.9c0-4.5,1.6-7.8,4.7-10c3.1-2.1,7.9-3.3,14.2-3.5l7.3-0.2v-1.9c0-4.3-2.2-6.4-6.6-6.4c-3.4,0-7.3,1-11.9,3.1l-3.8-7.8c4.9-2.6,10.2-3.8,16.2-3.8c5.7,0,10,1.2,13,3.7c3,2.5,4.5,6.2,4.5,11.3v28.3H518.7z M515.3,425.7l-4.5,0.2c-3.3,0.1-5.8,0.7-7.5,1.8c-1.6,1.1-2.5,2.8-2.5,5.1c0,3.3,1.9,4.9,5.6,4.9c2.7,0,4.8-0.8,6.4-2.3c1.6-1.5,2.4-3.6,2.4-6.1V425.7z"/><path fill="%23203C46" d="M559.8,446.1c-5,0-8.8-1.8-11.7-5.4h-0.6c0.4,3.5,0.6,5.6,0.6,6.1V464h-11.5v-61.1h9.4l1.6,5.5h0.5c2.7-4.2,6.7-6.3,12-6.3c5,0,8.9,1.9,11.7,5.8c2.8,3.9,4.2,9.2,4.2,16.1c0,4.5-0.7,8.5-2,11.8s-3.2,5.9-5.6,7.6C565.9,445.2,563.1,446.1,559.8,446.1z M556.4,411.4c-2.8,0-4.9,0.9-6.2,2.6c-1.3,1.8-2,4.7-2,8.7v1.3c0,4.6,0.7,7.8,2,9.8c1.3,2,3.5,3,6.4,3c5.2,0,7.7-4.3,7.7-12.8c0-4.2-0.6-7.3-1.9-9.4C561.1,412.4,559.1,411.4,556.4,411.4z"/></g><g><polygon fill="%23FFFFFF" points="128,224 288,0 448,224 416,320 352,304 288,256 224,304 160,320 "/><polygon fill="%23E4E8E9" points="208,256 208,308 224,304 234.1,256 "/><polygon fill="%23E4E8E9" points="240.8,224 240.8,224 288,0 208,112 208,224 "/><polygon fill="%2368C39F" points="448,224 368,112 368,224 "/><polygon fill="%23E4E8E9" points="335.2,224 336,224 336,67.2 288,0 335.2,224 "/><polygon fill="%23449BB5" points="128,224 160,320 176,316 176,156.8 "/><polygon fill="%23E4E8E9" points="352,304 416,320 437.3,256 341.9,256 "/><polygon fill="%23B8C1C4" points="234.1,256 234.1,256 224,304 288,256 288,224 "/><polygon fill="%23B8C1C4" points="288,192 288,0 240.8,224 "/><polygon fill="%23D2D8DA" points="335.2,224 288,0 288,192 "/><polygon fill="%23D2D8DA" points="341.9,256 288,224 288,256 352,304 341.9,256 "/><polygon fill="%23DBE0E1" points="240.8,224 234.1,256 288,224 288,192 "/><polygon fill="%23FFFFFF" points="234.1,256 240.8,224 208,224 208,112 176,156.8 176,316 208,308 208,256 "/><polygon fill="%23FFFFFF" points="234.1,256 234.1,256 240,228 "/><polygon fill="%23FFFFFF" points="448,224 368,224 368,112 336,67.2 336,224 335.2,224 341.9,256 437.3,256 448,224 "/><polygon fill="%23FFFFFF" points="341.9,256 336,228 341.9,256 "/><polygon fill="%23EDEFF0" points="288,192 288,224 341.9,256 335.2,224 "/></g></svg>');
    background-position-y: center;
    background-repeat: no-repeat;
    font-size: 1.5rem;
    font-weight: bold;
    cursor: pointer;
}   

.hidden {
        display: none !important;
    }

</style>
<div id="add-layer-container">
    <input type="text" placeholder="Enter OpenAerialMap ItemId">
    <button class="add-layer-btn">+</button>
</div>
<user-layer-button class="hidden">OpenAerialMap</user-layer-button>
`;

        super({
            element,
            target,
        });

        const addLayerContainer = shadowRoot.querySelector<HTMLInputElement>("#add-layer-container");
        const inputField = shadowRoot.querySelector<HTMLInputElement>("#add-layer-container input");
        const addButton = shadowRoot.querySelector<HTMLButtonElement>(".add-layer-btn");
        const userLayerButton = shadowRoot.querySelector<HTMLButtonElement>("user-layer-button");

        addButton.addEventListener("click", toggleInput);

        function toggleInput() {
            const inputField = shadowRoot.querySelector<HTMLInputElement>("#add-layer-container input");
            inputField.className = inputField.className.includes("expanded") ? "" : "expanded";
            if (inputField.className === "expanded") {
                window.setTimeout(() => inputField.focus(), 100);
            }
        }

        inputField.addEventListener("keydown", handleInput);

        function handleInput(e) {
            if (e.key === "Enter") {
                alert(e.target.value);
                inputField.className = inputField.className.includes("expanded") ? "" : "expanded";
                addLayerContainer.className = "hidden";
                userLayerButton.className = "";
            }
        }

        userLayerButton.addEventListener("close", handleClose);

        function handleClose(event: CustomEvent) {
            addLayerContainer.className = "";
            userLayerButton.className = "hidden";
            //TODO removelayer, switch to baselayer etc
        }

        userLayerButton.addEventListener("info", handleInfo);

        function handleInfo(event: CustomEvent) {
            alert("Some layer info");
            //TODO show info about the current layer
        }

    }

}