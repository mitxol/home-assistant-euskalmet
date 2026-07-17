class EuskalmetAlertCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._config = undefined;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Debes indicar el sensor de nivel o el aviso meteorológico de Euskalmet");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const alerts = this._state()?.attributes?.alerts;
    return Math.max(2, Math.min(6, (Array.isArray(alerts) ? alerts.length : 0) + 1));
  }

  static getStubConfig() {
    return { entity: "sensor.nivel_de_aviso" };
  }

  _state() {
    return this._hass?.states?.[this._config?.entity];
  }

  _severity(state) {
    const value = state?.attributes?.severity ?? state?.state ?? "none";
    return String(value).toLowerCase();
  }

  _render() {
    if (!this._config || !this._hass) return;

    const state = this._state();
    const severity = this._severity(state);
    const labels = {
      none: "Sin avisos",
      yellow: "Aviso amarillo",
      orange: "Aviso naranja",
      red: "Aviso rojo",
      unavailable: "Avisos no disponibles",
      unknown: "Avisos no disponibles",
    };
    const alerts = Array.isArray(state?.attributes?.alerts)
      ? state.attributes.alerts
      : [];
    const descriptions = Array.isArray(state?.attributes?.descriptions)
      ? state.attributes.descriptions
      : [];

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        * { box-sizing: border-box; }
        .card {
          overflow: hidden;
          color: var(--primary-text-color);
          background: var(--ha-card-background, var(--card-background-color));
          border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
        }
        .header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 18px;
          border-left: 7px solid var(--alert-color);
        }
        .badge {
          display: grid;
          flex: 0 0 40px;
          width: 40px;
          height: 40px;
          place-items: center;
          color: var(--badge-text);
          background: var(--alert-color);
          border-radius: 50%;
          font-size: 22px;
          font-weight: 700;
        }
        .title { font-size: 18px; font-weight: 600; }
        .summary { margin-top: 2px; color: var(--secondary-text-color); font-size: 13px; }
        .risks { margin: 0; padding: 0 18px 15px 77px; list-style: none; }
        .risk { padding: 11px 0; border-top: 1px solid var(--divider-color); }
        .cause { margin-bottom: 3px; color: var(--alert-color); font-size: 12px; font-weight: 700; text-transform: uppercase; }
        .description { line-height: 1.45; white-space: pre-line; }
        .none { --alert-color: var(--success-color, #43a047); --badge-text: white; }
        .yellow { --alert-color: #d6a700; --badge-text: #211b00; }
        .orange { --alert-color: #ef6c00; --badge-text: white; }
        .red { --alert-color: var(--error-color, #d32f2f); --badge-text: white; }
        .unknown, .unavailable { --alert-color: var(--disabled-text-color, #888); --badge-text: white; }
      </style>
      <section class="card ${["none", "yellow", "orange", "red", "unknown", "unavailable"].includes(severity) ? severity : "unknown"}">
        <div class="header">
          <div class="badge" aria-hidden="true">${severity === "none" ? "✓" : "!"}</div>
          <div>
            <div class="title"></div>
            <div class="summary"></div>
          </div>
        </div>
        <ul class="risks"></ul>
      </section>
    `;

    this.shadowRoot.querySelector(".title").textContent =
      this._config.title || labels[severity] || "Aviso meteorológico";
    this.shadowRoot.querySelector(".summary").textContent = alerts.length
      ? `${alerts.length} riesgo${alerts.length === 1 ? "" : "s"} activo${alerts.length === 1 ? "" : "s"}`
      : (severity === "none" ? "No hay riesgos meteorológicos activos" : "Sin detalles disponibles");

    const risks = this.shadowRoot.querySelector(".risks");
    const items = alerts.length
      ? alerts
      : descriptions.map((description) => ({ description }));

    for (const alert of items) {
      if (!alert?.description) continue;
      const item = document.createElement("li");
      item.className = "risk";
      if (alert.cause) {
        const cause = document.createElement("div");
        cause.className = "cause";
        cause.textContent = String(alert.cause).replaceAll("_", " ");
        item.appendChild(cause);
      }
      const description = document.createElement("div");
      description.className = "description";
      description.textContent = alert.description;
      item.appendChild(description);
      risks.appendChild(item);
    }
  }
}

if (!customElements.get("euskalmet-alert-card")) {
  customElements.define("euskalmet-alert-card", EuskalmetAlertCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "euskalmet-alert-card",
  name: "Euskalmet: avisos meteorológicos",
  description: "Relaciona el nivel de aviso con la descripción de cada riesgo activo.",
  preview: true,
});
