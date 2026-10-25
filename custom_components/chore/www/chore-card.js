console.info(
  "%c CHORE-CARD %c Loaded ",
  "color: white; background: #44739e; font-weight: 700;",
  "color: #44739e; background: white; font-weight: 700;"
);

class ChoreCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("You need to define an entity");
    }
    this._config = config;

    if (!this._body) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="chore-card__body">
            <ha-icon class="chore-card__icon"></ha-icon>
            <div class="chore-card__name"></div>
            <div class="chore-card__state"></div>
          </div>
        </ha-card>
        <style>
          ha-card {
            cursor: pointer;
          }
          .chore-card__body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 24px 16px;
          }
          .chore-card__icon {
            --mdc-icon-size: 80px;
            color: var(--state-icon-color, var(--paper-item-icon-color));
            margin-bottom: 16px;
          }
          .chore-card__name {
            font-size: 1em;
            font-weight: 500;
          }
          .chore-card__state {
            font-size: 0.85em;
            opacity: 0.8;
          }
          .chore-card__body--due .chore-card__icon {
            color: var(--warning-color, #e6b800);
          }
          .chore-card__body--overdue .chore-card__icon {
            color: var(--error-color, red);
          }
        </style>
      `;
      this._body = this.shadowRoot.querySelector(".chore-card__body");
      this._icon = this.shadowRoot.querySelector(".chore-card__icon");
      this._name = this.shadowRoot.querySelector(".chore-card__name");
      this._state = this.shadowRoot.querySelector(".chore-card__state");
      this.shadowRoot.querySelector("ha-card").addEventListener("click", () =>
        this._markDone()
      );
    }

    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config || !this._body) {
      return;
    }

    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this._name.textContent = this._config.entity;
      this._state.textContent = "unavailable";
      return;
    }

    const name =
      this._config.name || stateObj.attributes.friendly_name || this._config.entity;
    const icon =
      this._config.icon || stateObj.attributes.icon || "mdi:checkbox-marked-circle-outline";
    const days = stateObj.state;
    const tier = stateObj.attributes.tier || "ok";

    this._name.textContent = name;
    this._state.textContent = `${days} day${days === "1" ? "" : "s"} since last done`;
    this._icon.setAttribute("icon", icon);
    this._body.className = `chore-card__body chore-card__body--${tier}`;
  }

  _markDone() {
    if (!this._hass || !this._config) {
      return;
    }
    this._hass.callService("chore", "mark_done", {
      entity_id: this._config.entity,
    });
  }

  static getConfigElement() {
    return document.createElement("chore-card-editor");
  }

  static getStubConfig() {
    return { entity: "", icon: "" };
  }

  getCardSize() {
    return 1;
  }
}

class ChoreCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) {
      return;
    }
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        this._config = ev.detail.value;
        this.dispatchEvent(
          new CustomEvent("config-changed", { detail: { config: this._config } })
        );
      });
      this.shadowRoot.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = [
      {
        name: "entity",
        selector: { entity: { domain: "sensor", integration: "chore" } },
      },
      { name: "icon", selector: { icon: {} } },
    ];
    this._form.computeLabel = (schema) =>
      schema.name === "entity" ? "Chore" : "Icon (optional override)";
  }
}

customElements.define("chore-card", ChoreCard);
customElements.define("chore-card-editor", ChoreCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "chore-card",
  name: "Chore",
  description: "Shows a tracked chore's days-since-done status and resets it on tap.",
  preview: false,
});
