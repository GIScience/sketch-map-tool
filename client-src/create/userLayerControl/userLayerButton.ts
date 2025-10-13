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
          /*border-radius: 10px;*/
          /*background: var(--bg, url('https://via.placeholder.com/150')) center/cover no-repeat;*/
          overflow: hidden;
          /*cursor: pointer;*/
          /*font-family: sans-serif;*/
        }

        /* Slot content (main label) */
        #layer-btn {
          position: absolute;
          inset: 0;
          border: 0;
          padding: var(--padding);
          /*// display: flex;*/
          /*align-items: center;*/
          /*justify-content: center;*/
          color: var(--color);
          font-weight: var(--font-weight);
          font-size: var(--font-size);
          text-shadow: var(--text-shadow);
          line-height: var(--line-height);
          background: var(--background);
          cursor: pointer;  
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
            &:hover {
                background: #ca2334;
            }
          }
          &.info {
            bottom: -10px;
            &:hover {
                background: #0172ad;
            }
          }
          &:hover {
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
