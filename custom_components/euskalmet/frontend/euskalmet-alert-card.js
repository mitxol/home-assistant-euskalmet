class EuskalmetAlertCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._config = undefined;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error(this._text().missingEntity);
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

  _text() {
    const language = this._hass?.locale?.language || navigator.language || "es";
    const eu = String(language).toLowerCase().startsWith("eu");
    return eu ? {
      missingEntity: "Euskalmeteko abisu-mailaren sentsorea edo abisu meteorologikoa adierazi behar duzu",
      labels: {
        none: "Abisurik ez", yellow: "Abisu horia", orange: "Abisu laranja",
        red: "Abisu gorria", unavailable: "Abisuak ez daude eskuragarri",
        unknown: "Abisuak ez daude eskuragarri",
      },
      defaultTitle: "Abisu meteorologikoa",
      activeRisk: (count) => `${count} arrisku aktibo`,
      noRisks: "Ez dago arrisku meteorologiko aktiborik",
      noDetails: "Ez dago xehetasunik",
    } : {
      missingEntity: "Debes indicar el sensor de nivel o el aviso meteorológico de Euskalmet",
      labels: {
        none: "Sin avisos", yellow: "Aviso amarillo", orange: "Aviso naranja",
        red: "Aviso rojo", unavailable: "Avisos no disponibles",
        unknown: "Avisos no disponibles",
      },
      defaultTitle: "Aviso meteorológico",
      activeRisk: (count) => `${count} riesgo${count === 1 ? "" : "s"} activo${count === 1 ? "" : "s"}`,
      noRisks: "No hay riesgos meteorológicos activos",
      noDetails: "Sin detalles disponibles",
    };
  }

  _render() {
    if (!this._config || !this._hass) return;

    const state = this._state();
    const severity = this._severity(state);
    const text = this._text();
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
      this._config.title || text.labels[severity] || text.defaultTitle;
    this.shadowRoot.querySelector(".summary").textContent = alerts.length
      ? text.activeRisk(alerts.length)
      : (severity === "none" ? text.noRisks : text.noDetails);

    const risks = this.shadowRoot.querySelector(".risks");
    const items = alerts.length
      ? alerts
      : descriptions.map((description) => ({ description }));
    const language = String(this._hass?.locale?.language || "es")
      .toLowerCase().startsWith("eu") ? "eu" : "es";

    for (const alert of items) {
      const translatedDescription =
        alert?.descriptions_by_language?.[language] || alert?.description;
      if (!translatedDescription) continue;
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
      description.textContent = translatedDescription;
      item.appendChild(description);
      risks.appendChild(item);
    }
  }
}

if (!customElements.get("euskalmet-alert-card")) {
  customElements.define("euskalmet-alert-card", EuskalmetAlertCard);
}

window.customCards = window.customCards || [];
const euskalmetAlertLanguage = navigator.language?.toLowerCase().startsWith("eu");
window.customCards.push({
  type: "euskalmet-alert-card",
  name: euskalmetAlertLanguage ? "Euskalmet: abisu meteorologikoak" : "Euskalmet: avisos meteorológicos",
  description: euskalmetAlertLanguage
    ? "Abisu-maila arrisku aktibo bakoitzaren deskribapenarekin lotzen du."
    : "Relaciona el nivel de aviso con la descripción de cada riesgo activo.",
  preview: true,
});
