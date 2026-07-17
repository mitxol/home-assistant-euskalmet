const EUSKALMET_ASSET_ROOT = "/euskalmet_static";
const OFFICIAL_BOUNDS = [
  [41.864983, -3.7478],
  [43.655708, -1.2893926],
];

class EuskalmetRadarMapCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._config = undefined;
    this._map = undefined;
    this._overlay = undefined;
    this._timeline = [];
    this._activeIndex = -1;
    this._frameUrls = new Map();
    this._framePromises = new Map();
    this._timelineKey = undefined;
    this._playTimer = undefined;
    this._playing = false;
    this._preloadGeneration = 0;
    this._frameInterval = 125;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Debes indicar la entidad camera del radar de Euskalmet");
    }

    this._config = {
      opacity: 1,
      frame_interval: 125,
      autoplay: true,
      show_header: true,
      show_controls: true,
      show_options: true,
      ...config,
    };
    this._frameInterval = Number(this._config.frame_interval) || 125;
    this._ensureShell();
    this._applyConfiguration();
    this._updateSpeedButton();
    this._syncFromState();
  }

  set hass(hass) {
    this._hass = hass;
    this._syncFromState();
  }

  connectedCallback() {
    this._ensureShell();
    this._initializeMap();
  }

  disconnectedCallback() {
    this._stopPlayback();
    this._preloadGeneration += 1;
    this._revokeFrameUrls();

    if (this._map) {
      this._map.remove();
      this._map = undefined;
      this._overlay = undefined;
    }
  }

  getCardSize() {
    return 8;
  }

  getGridOptions() {
    return {
      rows: 8,
      columns: 12,
      min_rows: 6,
      min_columns: 6,
    };
  }

  static getStubConfig() {
    return { entity: "camera.radar_de_precipitacion" };
  }

  _ensureShell() {
    if (this.shadowRoot.querySelector(".radar-card")) {
      return;
    }

    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = `${EUSKALMET_ASSET_ROOT}/leaflet/leaflet.css`;

    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; }
      * { box-sizing: border-box; }
      .radar-card {
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
        justify-content: space-between;
        gap: 12px;
        padding: 16px 18px 14px;
      }
      .heading { min-width: 0; }
      .title { font-size: 18px; font-weight: 500; }
      .summary {
        margin-top: 3px;
        color: var(--secondary-text-color);
        font-size: 13px;
      }
      .loading {
        flex: 0 0 auto;
        color: var(--secondary-text-color);
        font-size: 12px;
      }
      .map {
        height: 460px;
        min-height: 320px;
        background: var(--secondary-background-color);
      }
      .map-shell { position: relative; }
      .leaflet-tile-pane {
        filter: grayscale(1) saturate(0) contrast(0.9) brightness(1.08);
      }
      .map-controls {
        position: absolute;
        z-index: 600;
        right: 12px;
        bottom: 12px;
        left: 12px;
        display: flex;
        align-items: center;
        gap: 0;
        min-height: 38px;
        padding: 3px;
        color: var(--primary-text-color);
        background: var(--card-background-color);
        background: color-mix(in srgb, var(--card-background-color) 92%, transparent);
        border: 1px solid color-mix(in srgb, var(--divider-color) 75%, transparent);
        border-radius: 7px;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(5px);
      }
      .transport-button {
        flex: 0 0 34px;
        width: 34px;
        height: 32px;
        padding: 0;
        border: 0;
        border-right: 1px solid var(--divider-color);
        border-radius: 0;
        color: var(--primary-text-color);
        background: transparent;
        font: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .transport-button:hover { background: var(--secondary-background-color); }
      .transport-button:disabled { cursor: default; opacity: 0.45; }
      .play { color: var(--primary-color); font-size: 16px; }
      .frame-time {
        flex: 0 1 205px;
        min-width: 145px;
        padding: 0 11px;
        overflow: hidden;
        font-size: 12px;
        font-weight: 500;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .timeline {
        flex: 1 1 180px;
        min-width: 90px;
        margin: 0 10px;
      }
      .speed {
        flex: 0 0 auto;
        min-width: 48px;
        height: 30px;
        padding: 0 8px;
        border: 0;
        border-left: 1px solid var(--divider-color);
        color: var(--secondary-text-color);
        background: transparent;
        font: inherit;
        color: var(--secondary-text-color);
        font-size: 12px;
        cursor: pointer;
      }
      input[type="range"] {
        accent-color: var(--primary-color);
      }
      .legend {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
        padding: 15px 18px 13px;
        color: var(--secondary-text-color);
      }
      .legend-title {
        grid-column: 1 / -1;
        font-size: 12px;
        letter-spacing: 0.04em;
      }
      .legend-ramp { display: flex; height: 6px; }
      .legend-ramp span { flex: 1 1 0; }
      .legend-label {
        display: block;
        margin-top: 7px;
        text-align: center;
        font-size: 12px;
      }
      .options {
        display: flex;
        align-items: center;
        gap: 10px 14px;
        flex-wrap: wrap;
        padding: 3px 18px 14px;
      }
      .opacity-label {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--secondary-text-color);
        font-size: 13px;
      }
      .opacity-label input { width: 100px; margin: 0; }
      .text-button {
        min-height: 34px;
        padding: 0 11px;
        border: 1px solid var(--divider-color);
        border-radius: 9px;
        color: var(--primary-text-color);
        background: transparent;
        font: inherit;
        font-size: 13px;
        cursor: pointer;
      }
      .text-button:hover { background: var(--secondary-background-color); }
      button:focus-visible, input:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
      }
      .message {
        display: none;
        padding: 0 18px 14px;
        color: var(--error-color, var(--secondary-text-color));
        font-size: 13px;
      }
      .message.visible { display: block; }
      [hidden] { display: none !important; }
      .leaflet-control-attribution { font-size: 11px; }
      @media (max-width: 560px) {
        .header { padding: 14px; }
        .map { height: 370px; }
        .map-controls { right: 8px; bottom: 8px; left: 8px; }
        .step { display: none; }
        .frame-time { flex-basis: 120px; min-width: 95px; padding: 0 8px; }
        .speed { display: none; }
        .timeline { margin: 0 7px; }
        .legend { gap: 4px; padding: 13px 10px 11px; }
        .legend-label { font-size: 11px; }
        .options { padding: 4px 14px 13px; }
        .opacity-label { flex: 1 1 160px; }
        .opacity-label input { flex: 1 1 auto; }
      }
    `;

    const card = document.createElement("section");
    card.className = "radar-card";
    card.innerHTML = `
      <div class="header">
        <div class="heading">
          <div class="title">Radar de precipitación</div>
          <div class="summary" aria-live="polite">Esperando datos…</div>
        </div>
        <div class="loading" aria-live="polite"></div>
      </div>
      <div class="map-shell">
        <div class="map" role="application" aria-label="Radar de Euskalmet sobre OpenStreetMap"></div>
        <div class="map-controls" aria-label="Controles de animación">
          <button class="previous step transport-button" type="button" aria-label="Fotograma anterior" disabled>◀</button>
          <button class="play transport-button" type="button" aria-label="Reproducir animación" disabled>▶</button>
          <button class="next step transport-button" type="button" aria-label="Fotograma siguiente" disabled>▶</button>
          <span class="frame-time">Última captura disponible</span>
          <input class="timeline" type="range" min="0" max="0" step="1" value="0" aria-label="Fotograma del radar" disabled>
          <button class="speed" type="button" aria-label="Velocidad de reproducción">2 fps</button>
        </div>
      </div>
      <div class="legend" aria-label="Leyenda de intensidad de precipitación">
        <span class="legend-title">PRECIPITACIONES</span>
        <div><div class="legend-ramp"><span style="background:#7efb30"></span><span style="background:#29dd15"></span><span style="background:#00af00"></span><span style="background:#0b5d00"></span></div><span class="legend-label">Débiles</span></div>
        <div><div class="legend-ramp"><span style="background:#08fdf9"></span><span style="background:#06a5ff"></span><span style="background:#0056ff"></span><span style="background:#000097"></span></div><span class="legend-label">Moderadas</span></div>
        <div><div class="legend-ramp"><span style="background:#fffcad"></span><span style="background:#f6ff03"></span><span style="background:#ffa713"></span></div><span class="legend-label">Fuertes</span></div>
        <div><div class="legend-ramp"><span style="background:#ff0000"></span><span style="background:#b90000"></span><span style="background:#7e0008"></span></div><span class="legend-label">Muy fuertes</span></div>
        <div><div class="legend-ramp"><span style="background:#f804ed"></span><span style="background:#b000ff"></span><span style="background:#66009b"></span><span style="background:#817e7e"></span><span style="background:#020202"></span></div><span class="legend-label">Torrenciales</span></div>
      </div>
      <div class="options">
        <label class="opacity-label">
          Opacidad
          <input class="opacity" type="range" min="0" max="1" step="0.05" aria-label="Opacidad del radar">
        </label>
        <button class="fit text-button" type="button">Ver cobertura</button>
        <button class="refresh text-button" type="button">Recargar datos</button>
      </div>
      <div class="message" role="status"></div>
    `;

    this.shadowRoot.append(stylesheet, style, card);

    const opacity = card.querySelector(".opacity");
    opacity.value = String(this._config?.opacity ?? 1);
    opacity.addEventListener("input", () => {
      this._overlay?.setOpacity(Number(opacity.value));
    });

    const timeline = card.querySelector(".timeline");
    timeline.addEventListener("input", () => {
      this._stopPlayback();
      this._selectFrame(Number(timeline.value));
    });

    card.querySelector(".play").addEventListener("click", () => {
      this._togglePlayback();
    });

    card.querySelector(".previous").addEventListener("click", () => {
      this._stepFrame(-1);
    });

    card.querySelector(".next").addEventListener("click", () => {
      this._stepFrame(1);
    });

    card.querySelector(".speed").addEventListener("click", () => {
      this._cycleSpeed();
    });

    card.querySelector(".fit").addEventListener("click", () => {
      this._map?.fitBounds(this._currentBounds(), { padding: [8, 8] });
    });

    card.querySelector(".refresh").addEventListener("click", () => {
      this._refreshData();
    });

    this._applyConfiguration();
  }

  _applyConfiguration() {
    if (!this.shadowRoot || !this._config) {
      return;
    }
    const visibility = {
      ".header": this._config.show_header !== false,
      ".map-controls": this._config.show_controls !== false,
      ".options": this._config.show_options !== false,
    };
    for (const [selector, visible] of Object.entries(visibility)) {
      const element = this.shadowRoot.querySelector(selector);
      if (element) {
        element.hidden = !visible;
      }
    }
    if (this._config.autoplay !== true && this._playing) {
      this._stopPlayback();
    }
  }

  async _loadLeaflet() {
    if (window.L) {
      return window.L;
    }

    if (!window.__euskalmetLeafletPromise) {
      window.__euskalmetLeafletPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = `${EUSKALMET_ASSET_ROOT}/leaflet/leaflet.js`;
        script.onload = () => resolve(window.L);
        script.onerror = () => reject(new Error("No se pudo cargar Leaflet"));
        document.head.appendChild(script);
      });
    }

    return window.__euskalmetLeafletPromise;
  }

  async _initializeMap() {
    if (this._map || !this.isConnected) {
      return;
    }

    try {
      const L = await this._loadLeaflet();
      if (!this.isConnected || this._map) {
        return;
      }

      this._map = L.map(this.shadowRoot.querySelector(".map"), {
        zoomControl: true,
        scrollWheelZoom: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this._map);

      this._map.fitBounds(this._currentBounds(), { padding: [8, 8] });
      this._syncFromState();
      queueMicrotask(() => this._map?.invalidateSize());
    } catch (error) {
      this._showMessage(error.message);
    }
  }

  _stateObject() {
    if (!this._hass || !this._config) {
      return undefined;
    }
    return this._hass.states[this._config.entity];
  }

  _currentBounds() {
    const candidate = this._stateObject()?.attributes?.bounds;
    if (
      Array.isArray(candidate) &&
      candidate.length === 2 &&
      candidate.every((point) => Array.isArray(point) && point.length === 2)
    ) {
      return candidate;
    }
    return OFFICIAL_BOUNDS;
  }

  _syncFromState() {
    if (!this.isConnected) {
      return;
    }
    if (!this._map) {
      this._initializeMap();
      return;
    }

    const state = this._stateObject();
    if (!state) {
      this._showMessage(`No existe la entidad ${this._config?.entity ?? "camera"}`);
      return;
    }

    const title = this._config.title || state.attributes.friendly_name || "Radar de precipitación";
    this.shadowRoot.querySelector(".title").textContent = title;

    const key = [
      state.attributes.config_entry_id,
      state.attributes.frame_count,
      state.attributes.timestamp,
    ].join("|");

    if (key !== this._timelineKey) {
      this._timelineKey = key;
      this._loadTimeline();
    }
  }

  async _loadTimeline() {
    const state = this._stateObject();
    if (!state || state.state === "unavailable") {
      this._showMessage("La imagen del radar no está disponible");
      return;
    }

    this._stopPlayback();
    this._showMessage("");
    this.shadowRoot.querySelector(".summary").textContent = "Cargando línea temporal…";

    try {
      const response = await this._callRadarCommand({
        type: "euskalmet/radar_frames",
        entry_id: state.attributes.config_entry_id,
      });

      this._timeline = Array.isArray(response.frames) ? response.frames : [];

      if (!this._timeline.length) {
        throw new Error("Todavía no hay fotogramas para animar");
      }

      const timeline = this.shadowRoot.querySelector(".timeline");
      timeline.max = String(this._timeline.length - 1);
      timeline.disabled = false;
      this.shadowRoot.querySelector(".play").disabled = false;
      this.shadowRoot.querySelector(".previous").disabled = false;
      this.shadowRoot.querySelector(".next").disabled = false;
      this.shadowRoot.querySelector(".summary").textContent = `${this._timeline.length} fotogramas · intervalo de 10 min`;

      await this._selectFrame(this._timeline.length - 1);
      this._preloadFrames();
      if (this._config?.autoplay === true && !this._playing) {
        await this._togglePlayback();
      }
    } catch (error) {
      this._timeline = [];
      this.shadowRoot.querySelector(".summary").textContent = "Última captura disponible";
      this._showLatestCameraImage();
      this._showMessage(`Animación no disponible: ${error.message}`);
    }
  }

  _showLatestCameraImage() {
    const state = this._stateObject();
    const picture = state?.attributes?.entity_picture;
    if (!picture) {
      return;
    }
    this._setOverlayUrl(picture);
    this.shadowRoot.querySelector(".frame-time").textContent = this._formatTimestamp({
      timestamp: state.attributes.timestamp,
      range: state.attributes.range,
    });
  }

  async _ensureFrame(index) {
    if (this._frameUrls.has(index)) {
      return this._frameUrls.get(index);
    }
    if (this._framePromises.has(index)) {
      return this._framePromises.get(index);
    }

    const state = this._stateObject();
    const promise = this._callRadarCommand({
      type: "euskalmet/radar_frames",
      entry_id: state?.attributes?.config_entry_id,
      index,
    }).then((response) => {
      const binary = atob(response.image);
      const bytes = new Uint8Array(binary.length);
      for (let offset = 0; offset < binary.length; offset += 1) {
        bytes[offset] = binary.charCodeAt(offset);
      }
      const url = URL.createObjectURL(new Blob([bytes], {
        type: response.content_type || "image/png",
      }));
      this._frameUrls.set(index, url);
      this._updateLoadingStatus();
      return url;
    }).finally(() => {
      this._framePromises.delete(index);
    });

    this._framePromises.set(index, promise);
    return promise;
  }

  async _callRadarCommand(message) {
    const connection = this._hass?.connection;
    if (typeof connection?.sendMessagePromise === "function") {
      const response = await connection.sendMessagePromise(message);
      return response?.result ?? response;
    }
    if (typeof this._hass?.callWS === "function") {
      return this._hass.callWS(message);
    }
    throw new Error("WebSocket no disponible");
  }

  async _selectFrame(index) {
    if (!this._timeline.length) {
      return;
    }
    const selected = Math.max(0, Math.min(index, this._timeline.length - 1));
    this._activeIndex = selected;
    const frame = this._timeline[selected];
    const timeline = this.shadowRoot.querySelector(".timeline");
    timeline.value = String(selected);
    this.shadowRoot.querySelector(".frame-time").textContent = this._formatTimestamp(frame);

    try {
      const url = await this._ensureFrame(selected);
      if (selected === this._activeIndex) {
        this._setOverlayUrl(url);
      }
    } catch (error) {
      this._showMessage(`No se pudo cargar el fotograma: ${error.message}`);
      this._stopPlayback();
    }
  }

  _setOverlayUrl(url) {
    if (!url || !this._map || !window.L) {
      return;
    }
    if (this._overlay) {
      this._overlay.setUrl(url);
      return;
    }
    this._overlay = window.L.imageOverlay(url, this._currentBounds(), {
      opacity: Number(this.shadowRoot.querySelector(".opacity").value),
      interactive: false,
    }).addTo(this._map);
  }

  _formatTimestamp(frame) {
    if (frame?.timestamp) {
      const date = new Date(frame.timestamp);
      if (!Number.isNaN(date.getTime())) {
        const language = this._hass?.locale?.language || navigator.language;
        return new Intl.DateTimeFormat(language, {
          weekday: "short",
          day: "2-digit",
          month: "short",
          hour: "2-digit",
          minute: "2-digit",
          timeZoneName: "short",
        }).format(date);
      }
    }
    return frame?.range || "Hora no disponible";
  }

  async _togglePlayback() {
    if (this._playing) {
      this._stopPlayback();
      return;
    }
    if (this._timeline.length < 2) {
      return;
    }

    if (this._activeIndex >= this._timeline.length - 1) {
      await this._selectFrame(0);
    }
    this._playing = true;
    this._updatePlayButton();
    this._scheduleNextFrame();
  }

  _stepFrame(direction) {
    if (!this._timeline.length) {
      return;
    }
    this._stopPlayback();
    const next = Math.max(
      0,
      Math.min(this._activeIndex + direction, this._timeline.length - 1),
    );
    this._selectFrame(next);
  }

  _cycleSpeed() {
    const speeds = [1000, 500, 250, 125];
    const current = speeds.indexOf(this._frameInterval);
    this._frameInterval = speeds[(current + 1) % speeds.length];
    this._updateSpeedButton();
    if (this._playing) {
      this._scheduleNextFrame();
    }
  }

  _updateSpeedButton() {
    const button = this.shadowRoot.querySelector(".speed");
    if (button) {
      button.textContent = `${Math.round(1000 / this._frameInterval)} fps`;
    }
  }

  _scheduleNextFrame() {
    clearTimeout(this._playTimer);
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const interval = reducedMotion
      ? Math.max(1200, this._frameInterval)
      : Math.max(125, this._frameInterval);

    this._playTimer = setTimeout(async () => {
      if (!this._playing) {
        return;
      }
      const next = (this._activeIndex + 1) % this._timeline.length;
      await this._selectFrame(next);
      if (this._playing) {
        this._scheduleNextFrame();
      }
    }, interval);
  }

  _stopPlayback() {
    this._playing = false;
    clearTimeout(this._playTimer);
    this._playTimer = undefined;
    this._updatePlayButton();
  }

  _updatePlayButton() {
    const button = this.shadowRoot.querySelector(".play");
    if (!button) {
      return;
    }
    button.textContent = this._playing ? "Ⅱ" : "▶";
    button.setAttribute("aria-label", this._playing ? "Pausar animación" : "Reproducir animación");
    if (this._playing) {
      this.shadowRoot.querySelector(".loading").textContent = "Reproduciendo";
    } else if (this._timeline.length) {
      this._updateLoadingStatus();
    }
  }

  _preloadFrames() {
    const generation = ++this._preloadGeneration;
    let cursor = 0;
    const worker = async () => {
      while (cursor < this._timeline.length && generation === this._preloadGeneration) {
        const index = cursor;
        cursor += 1;
        try {
          await this._ensureFrame(index);
        } catch (_error) {
          return;
        }
      }
    };
    Promise.all([worker(), worker(), worker()]).then(() => {
      if (generation === this._preloadGeneration) {
        this._updateLoadingStatus();
      }
    });
  }

  _updateLoadingStatus() {
    const loading = this.shadowRoot.querySelector(".loading");
    if (!loading || !this._timeline.length) {
      return;
    }
    const loaded = this._frameUrls.size;
    loading.textContent = loaded < this._timeline.length
      ? `Preparando ${loaded}/${this._timeline.length}`
      : "Animación lista";
  }

  async _refreshData() {
    const button = this.shadowRoot.querySelector(".refresh");
    button.disabled = true;
    try {
      if (typeof this._hass.callService === "function") {
        await this._hass.callService("homeassistant", "update_entity", {
          entity_id: this._config.entity,
        });
      }
      this._preloadGeneration += 1;
      this._revokeFrameUrls();
      this._timelineKey = undefined;
      this._syncFromState();
    } catch (error) {
      this._showMessage(`No se pudo actualizar el radar: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  }

  _revokeFrameUrls() {
    for (const url of this._frameUrls.values()) {
      URL.revokeObjectURL(url);
    }
    this._frameUrls.clear();
    this._framePromises.clear();
  }

  _showMessage(text) {
    const message = this.shadowRoot.querySelector(".message");
    if (!message) {
      return;
    }
    message.textContent = text;
    message.classList.toggle("visible", Boolean(text));
  }
}

if (!customElements.get("euskalmet-radar-map-card")) {
  customElements.define("euskalmet-radar-map-card", EuskalmetRadarMapCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "euskalmet-radar-map-card",
  name: "Euskalmet: radar animado sobre OpenStreetMap",
  description: "Anima todos los fotogramas del radar de Kapildui sobre OpenStreetMap.",
  preview: false,
  getEntitySuggestion: (_hass, entityId) => {
    if (!entityId.startsWith("camera.")) {
      return null;
    }
    return {
      config: {
        type: "custom:euskalmet-radar-map-card",
        entity: entityId,
      },
    };
  },
});
