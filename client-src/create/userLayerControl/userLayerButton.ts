export class UserLayerButton extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });

        const template = document.createElement("template");
        template.innerHTML = `
      <style>
        :host {
          display: inline-block;
          min-width: 1rem;
          min-height: 1rem;
          position: relative;
          overflow: hidden;
        }

        #layer-btn {
          position: absolute;
          inset: 0;
          border: 0;
          border-radius: inherit;
          padding: var(--padding);
          color: var(--color);
          font-weight: var(--font-weight);
          font-size: var(--font-size);
          text-shadow: var(--text-shadow);
          line-height: var(--line-height);
          background: var(--background);
          cursor: pointer;  
          background-position-y: center;
          background-repeat: no-repeat;
          background-size: contain;
          background-color: rgb(22.62% 46.96% 23.13%);
        }

        /* Action buttons */
        .action-btn {
          position: absolute;
          right: -10px;
          width: 24px;
          height: 24px;
          background: slategrey;
          color: white;
          border: 2px solid lightgray;  
          border-radius: 50%;
          font-size: 20px;
          font-weight: bold;
          text-align: center;
          cursor: pointer;
          user-select: none;
          line-height: 0;
          transition: border-color 0.2s, background 0.2s;
          &.close {
            top: -10px;
            &:is(:hover, :focus) {
                background: #ca2334;
            }
          }
          &.info {
            bottom: -10px;
            font-size: 16px;
            &:is(:hover, :focus) {
                background: #0172ad;
            }
          }
          &:is(:hover, :focus) {
            border-color: white;
          }
        }
      
        .bottom-action:hover {
          background: rgba(0,0,0,0.8);
        }
      </style>

      <button id="layer-btn" aria-label="Show Layer">button</button>
      <button class="action-btn close" aria-label="Remove layer from map">&times;</button>
      <button class="action-btn info" aria-label="Get more information">i</button>
    `;

        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }

    static get observedAttributes() {
        return ["bgimageurl"];
    }

    attributeChangedCallback(name: string, oldValue: string, newValue: string) {
        if (name === 'bgimageurl') {
            const layerButton = this.shadowRoot.querySelector<HTMLButtonElement>('#layer-btn');
            layerButton.style.backgroundImage = `url(${newValue})`;
        }
    }

    connectedCallback() {

        // transfer host content to button
        this.shadowRoot.getElementById("layer-btn").innerHTML = this.innerHTML;

        this.shadowRoot.querySelector('#layer-btn')
            .addEventListener('click', e => {
                e.stopPropagation(); // don’t trigger outer click
                this.dispatchEvent(new CustomEvent('click', { bubbles: true, composed: true }));
            });

        this.shadowRoot.querySelector('.close')
            .addEventListener('click', e => {
                e.stopPropagation(); // don’t trigger outer click
                this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
            });

        this.shadowRoot.querySelector('.info')
            .addEventListener('click', e => {
                e.stopPropagation(); // don’t trigger outer click
                this.dispatchEvent(new CustomEvent('info', { bubbles: true, composed: true }));
            });

    }
}
