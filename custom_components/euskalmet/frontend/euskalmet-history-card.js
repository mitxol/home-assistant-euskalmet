class EuskalmetHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.date = new Date();
    this.retries = 0;
  }

  setConfig(config) {
    if (!config) throw new Error("Falta la configuración de la tarjeta");
    this.config = { title: "Histórico Euskalmet", measure: "temperature", ...config };
    this.render();
    this.scheduleLoad();
  }

  set hass(hass) {
    this._hass = hass;
    this.scheduleLoad();
  }

  connectedCallback() { this.scheduleLoad(); }
  disconnectedCallback() { clearTimeout(this.retryTimer); }
  getCardSize() { return 6; }
  static getStubConfig() { return { measure: "temperature" }; }

  scheduleLoad(force = false) {
    if (!this.isConnected || !this._hass || !this.config || this.loading) return;
    if (!force && this.loaded) return;
    queueMicrotask(() => this.load(force));
  }

  async load(force = false) {
    if (!this.isConnected || !this._hass || !this.config || this.loading) return;
    if (!force && this.loaded) return;
    this.loading = true;
    this.error = null;
    this.render();
    const request = (this.request || 0) + 1;
    this.request = request;
    try {
      const entityState = this.config.entity
        ? this._hass.states[this.config.entity]
        : undefined;
      const stationId = entityState?.attributes?.station;
      const data = await this._hass.callWS({
        type: "euskalmet/history",
        entry_id: this.config.entry_id,
        station_id: stationId,
        year: this.date.getFullYear(),
        month: this.date.getMonth() + 1,
      });
      if (request !== this.request) return;
      this.data = data;
      this.loaded = true;
      this.retries = 0;
    } catch (error) {
      if (request !== this.request) return;
      this.error = String(error?.message || error);
      this.loaded = false;
      if (this.retries < 3 && this.isConnected) {
        this.retries += 1;
        clearTimeout(this.retryTimer);
        this.retryTimer = setTimeout(() => this.scheduleLoad(true), this.retries * 1000);
      }
    } finally {
      if (request === this.request) {
        this.loading = false;
        this.render();
      }
    }
  }

  item() { return this.data?.items?.find((item) => item.measureId === this.config.measure); }

  points(field) {
    return (this.item()?.dailySummaries || []).map((summary, index) => ({
      x: index + 1,
      y: typeof summary[field] === "object" ? summary[field]?.value : summary[field],
    })).filter((point) => Number.isFinite(point.y));
  }

  path(points, min, max) {
    return points.map((point, index) =>
      `${index ? "L" : "M"} ${30 + ((point.x - 1) * 555) / 30} ${10 + ((max - point.y) * 230) / (max - min || 1)}`,
    ).join(" ");
  }

  shift(delta) {
    this.date = new Date(this.date.getFullYear(), this.date.getMonth() + delta, 1);
    this.data = null;
    this.loaded = false;
    this.retries = 0;
    this.scheduleLoad(true);
  }

  render() {
    if (!this.config) return;
    const labels = {
      temperature: "Temperatura (°C)", precipitation: "Precipitación (mm)",
      humidity: "Humedad (%)", pressure: "Presión (hPa)", irradiance: "Radiación (W/m²)",
      mean_speed: "Viento medio (m/s)", max_speed: "Racha (m/s)",
    };
    const fields = this.config.measure === "temperature" ? ["min", "mean", "max"]
      : this.config.measure === "precipitation" ? ["total"] : ["mean", "max"];
    const series = fields.map((field) => ({ field, points: this.points(field) }));
    const values = series.flatMap((item) => item.points.map((point) => point.y));
    const min = Math.min(...values, 0);
    const max = Math.max(...values, 1);
    const colors = ["#42a5f5", "#66bb6a", "#ef5350"];
    const month = this.date.toLocaleDateString("es-ES", { month: "long", year: "numeric" });
    const graph = `<div class="legend">${series.map((item, index) =>
      `<span><i style="background:${colors[index]}"></i>${item.field}</span>`).join("")}</div>
      <svg viewBox="0 0 600 260"><line class="grid" x1="30" y1="230" x2="585" y2="230"/>
      ${series.map((item, index) => `<path class="line" stroke="${colors[index]}" d="${this.path(item.points, min, max)}"/>`).join("")}
      <text x="30" y="250">1</text><text x="555" y="250">31</text><text x="2" y="18">${max.toFixed(1)}</text><text x="2" y="230">${min.toFixed(1)}</text></svg>`;
    const body = this.loading ? '<div class="message">Cargando…</div>'
      : this.error ? `<div class="message">No se pudo cargar el histórico.<small>${this.error}</small><button id="retry">Reintentar</button></div>`
        : values.length ? graph : '<div class="message">No hay datos para este mes.</div>';
    this.shadowRoot.innerHTML = `<style>
      :host{display:block}ha-card{padding:16px}header{display:flex;justify-content:space-between;align-items:center}h2{font-size:18px;margin:0}
      .tools,.legend{display:flex;gap:8px;align-items:center}.legend{gap:14px;font-size:12px;margin:8px 0;flex-wrap:wrap}
      button,select{color:var(--primary-text-color);background:transparent;border:1px solid var(--divider-color);border-radius:8px;padding:7px}
      .legend i{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:5px}svg{width:100%;height:260px}.grid{stroke:var(--divider-color)}
      .line{fill:none;stroke-width:2}text{fill:currentColor}.message{min-height:220px;display:flex;gap:12px;flex-direction:column;align-items:center;justify-content:center;text-align:center}
    </style><ha-card><header><div><h2>${this.config.title}</h2><small>${month}</small></div><div class="tools"><button id="prev">‹</button><button id="next">›</button></div></header>
      <select id="measure">${Object.entries(labels).map(([key, label]) => `<option value="${key}" ${key === this.config.measure ? "selected" : ""}>${label}</option>`).join("")}</select>${body}</ha-card>`;
    this.shadowRoot.querySelector("#prev")?.addEventListener("click", () => this.shift(-1));
    this.shadowRoot.querySelector("#next")?.addEventListener("click", () => this.shift(1));
    this.shadowRoot.querySelector("#retry")?.addEventListener("click", () => { this.retries = 0; this.scheduleLoad(true); });
    this.shadowRoot.querySelector("#measure")?.addEventListener("change", (event) => { this.config.measure = event.target.value; this.render(); });
  }
}

if (!customElements.get("euskalmet-history-card")) {
  customElements.define("euskalmet-history-card", EuskalmetHistoryCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "euskalmet-history-card")) {
  window.customCards.push({ type: "euskalmet-history-card", name: "Euskalmet - Histórico", description: "Gráficos diarios históricos de Euskalmet" });
}
