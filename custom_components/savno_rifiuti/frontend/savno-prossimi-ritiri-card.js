const SAVNO_ICON_BASE = "/api/savno_rifiuti/frontend/icons";

function savnoNormalize(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function savnoWasteIcon(waste) {
  const value = savnoNormalize(waste);
  if (value.includes("plastica") || value.includes("lattine")) return `${SAVNO_ICON_BASE}/sacco_plastica-lattine.svg`;
  if (value.includes("umido") || value.includes("organico")) return `${SAVNO_ICON_BASE}/bidone_umido.svg`;
  if (value.includes("carta") || value.includes("cartone")) return `${SAVNO_ICON_BASE}/bidone_carta.svg`;
  if (value.includes("vetro")) return `${SAVNO_ICON_BASE}/bidone_vetro.svg`;
  if (value.includes("verde") || value.includes("ramaglie")) return `${SAVNO_ICON_BASE}/bidone_verde_ramaglie.png`;
  if (value.includes("secco") || value.includes("indifferenziato")) return `${SAVNO_ICON_BASE}/bidone_secco.svg`;
  return null;
}

class SavnoProssimiRitiriCard extends HTMLElement {
  setConfig(config) {
    this._config = { title: "Prossimi ritiri", ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return Math.max(2, this._getRows().length + 1);
  }

  static getStubConfig() {
    return { title: "Prossimi ritiri" };
  }

  static getConfigElement() {
    return document.createElement("savno-prossimi-ritiri-card-editor");
  }

  _findEntity() {
    if (!this._hass) return null;
    const configured = this._config?.entity;
    if (configured && this._hass.states[configured]) return configured;

    return Object.keys(this._hass.states).find((entityId) => {
      const state = this._hass.states[entityId];
      return entityId.startsWith("sensor.") &&
        Array.isArray(state?.attributes?.ritiri) &&
        state?.attributes?.comune !== undefined;
    }) || null;
  }

  _getRows() {
    const entityId = this._findEntity();
    if (!entityId || !this._hass) return [];
    const rows = this._hass.states[entityId]?.attributes?.ritiri;
    return Array.isArray(rows) ? rows : [];
  }

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _wastes(row) {
    if (Array.isArray(row?.rifiuti) && row.rifiuti.length) return row.rifiuti;
    if (row?.cosa) return String(row.cosa).split(/\s*\+\s*/).filter(Boolean);
    return [];
  }


  _daysAway(row) {
    const raw = Number(row?.giorni_mancanti);
    if (Number.isFinite(raw)) return raw;
    if (!row?.data) return null;
    const target = new Date(`${row.data}T12:00:00`);
    if (Number.isNaN(target.getTime())) return null;
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0, 0);
    return Math.round((target.getTime() - today.getTime()) / 86400000);
  }

  _daysAwayLabel(row) {
    const days = this._daysAway(row);
    if (days === null) return "—";
    if (days <= 0) return "Oggi";
    if (days === 1) return "1 giorno";
    return `${days} giorni`;
  }


  _weekdayLabel(row) {
    if (row?.giorno_settimana) return String(row.giorno_settimana);
    if (!row?.data) return "—";
    const parts = String(row.data).split("-").map(Number);
    if (parts.length !== 3 || parts.some((v) => !Number.isFinite(v))) return "—";
    const [year, month, day] = parts;
    const date = new Date(year, month - 1, day, 12, 0, 0);
    if (Number.isNaN(date.getTime())) return "—";
    const names = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"];
    return names[date.getDay()];
  }

  _wasteHtml(waste) {
    const icon = savnoWasteIcon(waste);
    return `
      <span class="waste">
        ${icon ? `<img class="bin" src="${icon}" alt="">` : `<ha-icon class="fallback" icon="mdi:delete-outline"></ha-icon>`}
        <span>${this._escape(waste)}</span>
      </span>`;
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;

    const entityId = this._findEntity();
    const rows = this._getRows();
    const title = this._config.title || "Prossimi ritiri";
    const comune = entityId && this._hass
      ? this._hass.states[entityId]?.attributes?.comune
      : null;

    let body;
    if (!this._hass) {
      body = `<div class="message">Caricamento…</div>`;
    } else if (!entityId) {
      body = `<div class="message">Nessuna entità SAVNO “Prossimi ritiri” trovata.</div>`;
    } else if (!rows.length) {
      body = `<div class="message">Nessun ritiro disponibile.</div>`;
    } else {
      body = `
        <div class="table" role="table" aria-label="Prossimi ritiri SAVNO">
          <div class="tr head" role="row">
            <div role="columnheader">Giorno</div>
            <div role="columnheader">Quando</div>
            <div role="columnheader">Fra</div>
            <div role="columnheader">Cosa</div>
          </div>
          ${rows.map((row) => `
            <div class="tr" role="row">
              <div class="weekday" role="cell">${this._escape(this._weekdayLabel(row))}</div>
              <div class="when" role="cell">${this._escape(row.quando)}</div>
              <div class="away" role="cell">${this._escape(this._daysAwayLabel(row))}</div>
              <div class="what" role="cell">${this._wastes(row).map((w) => this._wasteHtml(w)).join("")}</div>
            </div>
          `).join("")}
        </div>`;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header {
          display: flex; align-items: center; gap: 12px;
          padding: 16px 16px 12px;
        }
        .header ha-icon { color: var(--primary-color); width: 28px; height: 28px; }
        .heading { min-width: 0; }
        .title { font-size: 18px; font-weight: 500; color: var(--primary-text-color); line-height: 1.25; }
        .subtitle { margin-top: 2px; font-size: 12px; color: var(--secondary-text-color); }
        .table { width: 100%; color: var(--primary-text-color); }
        .tr {
          display: grid; grid-template-columns: minmax(92px, 0.34fr) minmax(72px, 0.24fr) minmax(72px, 0.25fr) minmax(0, 1fr);
          align-items: center; min-height: 58px; padding: 0 16px;
          border-top: 1px solid var(--divider-color);
          box-sizing: border-box;
        }
        .tr.head { min-height: 34px; font-size: 12px; font-weight: 500; color: var(--secondary-text-color); }
        .weekday { font-weight: 500; white-space: nowrap; padding-right: 10px; }
        .when { white-space: nowrap; padding-right: 10px; }
        .away { white-space: nowrap; color: var(--secondary-text-color); font-size: 13px; padding-right: 10px; }
        .what { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; padding: 7px 0; }
        .waste { display: inline-flex; align-items: center; gap: 7px; min-width: 0; }
        .bin { width: 26px; height: 35px; object-fit: contain; flex: 0 0 auto; }
        .fallback { width: 24px; height: 24px; color: var(--secondary-text-color); }
        .message { padding: 8px 16px 18px; color: var(--secondary-text-color); }
        @media (max-width: 420px) {
          .tr { grid-template-columns: 82px 62px 62px minmax(0, 1fr); padding: 0 12px; font-size: 13px; }
          .header { padding-left: 12px; padding-right: 12px; }
          .bin { width: 23px; height: 31px; }
        }
      </style>
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:calendar-clock"></ha-icon>
          <div class="heading">
            <div class="title">${this._escape(title)}</div>
            ${comune ? `<div class="subtitle">SAVNO · ${this._escape(comune)}</div>` : ""}
          </div>
        </div>
        ${body}
      </ha-card>`;
  }
}

class SavnoProssimiRitiriCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { title: "Prossimi ritiri", ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _entities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states).filter((entityId) => {
      const state = this._hass.states[entityId];
      return entityId.startsWith("sensor.") &&
        Array.isArray(state?.attributes?.ritiri) &&
        state?.attributes?.comune !== undefined;
    });
  }

  _changed() {
    const entity = this.shadowRoot.querySelector("#entity")?.value || undefined;
    const title = this.shadowRoot.querySelector("#title")?.value || "Prossimi ritiri";
    const config = { ...this._config, title };
    if (entity) config.entity = entity;
    else delete config.entity;
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config }, bubbles: true, composed: true,
    }));
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const entities = this._entities();
    const options = entities.map((entityId) => {
      const state = this._hass.states[entityId];
      const comune = state.attributes.comune || entityId;
      const selected = this._config.entity === entityId ? " selected" : "";
      return `<option value="${entityId}"${selected}>${comune} — ${entityId}</option>`;
    }).join("");

    this.shadowRoot.innerHTML = `
      <style>
        .hint { padding: 10px 12px; margin-bottom: 12px; border-radius: 10px; background: var(--secondary-background-color); font-size: 13px; line-height: 1.4; }
        .field { margin: 12px 0; }
        label { display:block; margin-bottom:6px; font-size:13px; color:var(--secondary-text-color); }
        input, select { box-sizing:border-box; width:100%; padding:10px; border-radius:8px; border:1px solid var(--divider-color); background:var(--card-background-color); color:var(--primary-text-color); font:inherit; }
      </style>
      <div class="hint">Questa è la card tabellare SAVNO. Mostra tutte le righe disponibili e le icone dei materiali.</div>
      <div class="field">
        <label for="entity">Configurazione SAVNO</label>
        <select id="entity">
          <option value="">Automatico</option>
          ${options}
        </select>
      </div>
      <div class="field">
        <label for="title">Titolo</label>
        <input id="title" value="${String(this._config.title || "Prossimi ritiri").replaceAll('"','&quot;')}">
      </div>`;

    this.shadowRoot.querySelector("#entity").addEventListener("change", () => this._changed());
    this.shadowRoot.querySelector("#title").addEventListener("change", () => this._changed());
  }
}

if (!customElements.get("savno-prossimi-ritiri-card")) {
  customElements.define("savno-prossimi-ritiri-card", SavnoProssimiRitiriCard);
}
if (!customElements.get("savno-prossimi-ritiri-card-editor")) {
  customElements.define("savno-prossimi-ritiri-card-editor", SavnoProssimiRitiriCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "savno-prossimi-ritiri-card")) {
  window.customCards.push({
    type: "savno-prossimi-ritiri-card",
    name: "SAVNO - Tabella prossimi ritiri",
    description: "Card SAVNO con tabella Giorno/Quando/Fra/Cosa e icone originali dei materiali.",
    preview: false,
  });
}
