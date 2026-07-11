import {
  buildHistorySegments,
  createMapRenderSignature,
} from "./presence-timeline-map-utils.js";

const DEFAULT_SUMMARY_API = "/api/presence-timeline/panel/summary";
const DEFAULT_MEMBER_API_TEMPLATE = "/api/presence-timeline/panel/members/{member_id}";
const DEFAULT_HISTORY_HOURS = 24;
const STATIC_ROOT = "/api/presence-timeline/static";
const LEAFLET_CSS_URL = `${STATIC_ROOT}/vendor/leaflet.css`;
const LEAFLET_JS_URL = `${STATIC_ROOT}/vendor/leaflet.js`;
const ASSET_VERSION = "0.3.3";

class PresenceTimelinePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._panel = null;
    this._summary = [];
    this._selectedMemberId = null;
    this._memberPanel = null;
    this._loading = false;
    this._error = null;
    this._renderedMapSignature = null;
  }

  set hass(hass) {
    const shouldRender = this._hass == null;
    this._hass = hass;
    this._ensureLoaded();
    if (shouldRender) {
      this._render();
    }
  }

  set panel(panel) {
    this._panel = panel;
    this._ensureLoaded();
  }

  connectedCallback() {
    this._render();
  }

  async _ensureLoaded() {
    if (!this._hass || this._loading || this._summary.length) {
      return;
    }
    await this._loadSummary(true);
  }

  async _loadSummary(loadSelectedMember = false) {
    if (!this._hass) {
      return;
    }

    this._loading = true;
    this._error = null;
    this._render();

    try {
      const payload = await this._apiGet(this._summaryApiPath());
      this._summary = payload.items || [];
      if (!this._selectedMemberId || !this._summary.some((member) => member.member_id === this._selectedMemberId)) {
        this._selectedMemberId = this._summary[0]?.member_id ?? null;
      }
      if (loadSelectedMember && this._selectedMemberId) {
        await this._loadMemberPanel(this._selectedMemberId);
      } else {
        this._render();
      }
    } catch (err) {
      this._error = this._normalizeError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _loadMemberPanel(memberId) {
    if (!this._hass) {
      return;
    }

    this._selectedMemberId = memberId;
    this._loading = true;
    this._error = null;
    this._render();

    try {
      const { startIso, endIso } = this._historyWindow();
      const path = this._memberApiPath(memberId, startIso, endIso);
      this._memberPanel = await this._apiGet(path);
    } catch (err) {
      this._error = this._normalizeError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _historyWindow() {
    const end = new Date();
    const hours = this._panel?.config?.defaultHistoryHours ?? DEFAULT_HISTORY_HOURS;
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
    return { startIso: start.toISOString(), endIso: end.toISOString() };
  }

  _summaryApiPath() {
    return this._panel?.config?.summaryApi ?? DEFAULT_SUMMARY_API;
  }

  _memberApiPath(memberId, startIso, endIso) {
    const template = this._panel?.config?.memberApiTemplate ?? DEFAULT_MEMBER_API_TEMPLATE;
    const base = template.replace("{member_id}", memberId);
    const params = new URLSearchParams({ start: startIso, end: endIso });
    return `${base}?${params.toString()}`;
  }

  async _apiGet(path) {
    const headers = { Accept: "application/json" };
    const token = this._hass?.auth?.data?.accessToken || this._hass?.auth?.accessToken;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(path, {
      method: "GET",
      headers,
      credentials: "same-origin",
    });
    if (!response.ok) {
      let detail = "";
      try {
        const payload = await response.json();
        detail = payload?.message || payload?.error || JSON.stringify(payload);
      } catch (_err) {
        detail = await response.text();
      }
      throw new Error(`Presence Timeline panel request failed: ${response.status}${detail ? ` ${detail}` : ""}`);
    }
    return response.json();
  }

  _render() {
    const selectedMember = this._summary.find((member) => member.member_id === this._selectedMemberId) ?? null;
    const mapModel = this._buildMapModel(selectedMember, this._memberPanel);
    const historyStops = this._memberPanel?.stops ?? [];
    const historyTrips = (this._memberPanel?.timeline ?? []).filter((item) => item.kind === "trip");

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          height: 100%;
          color: var(--primary-text-color);
          background:
            radial-gradient(circle at top left, rgba(33, 150, 243, 0.14), transparent 35%),
            linear-gradient(180deg, rgba(15, 23, 42, 0.06), rgba(15, 23, 42, 0));
        }
        .page {
          box-sizing: border-box;
          min-height: 100%;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
        }
        .title {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
          letter-spacing: 0.02em;
        }
        .subtitle {
          color: var(--secondary-text-color);
          font-size: 14px;
        }
        .toolbar button, .badge {
          border: none;
          border-radius: 999px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
        }
        .toolbar button {
          padding: 10px 16px;
          font: inherit;
          cursor: pointer;
          box-shadow: var(--ha-card-box-shadow, none);
        }
        .status-row {
          display: flex;
          gap: 12px;
          overflow-x: auto;
          padding-bottom: 4px;
        }
        .badge {
          min-width: 220px;
          padding: 14px 16px;
          text-align: left;
          cursor: pointer;
          box-shadow: var(--ha-card-box-shadow, none);
          border: 1px solid transparent;
        }
        .badge[selected] {
          border-color: var(--primary-color);
          background: color-mix(in srgb, var(--card-background-color) 82%, var(--primary-color));
        }
        .badge-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        .badge-name {
          font-size: 16px;
          font-weight: 700;
        }
        .badge-state {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--secondary-text-color);
        }
        .badge-detail {
          font-size: 14px;
          color: var(--secondary-text-color);
        }
        .content {
          display: grid;
          grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
          gap: 18px;
          min-height: 0;
          flex: 1;
        }
        .card {
          background: var(--card-background-color);
          border-radius: var(--ha-card-border-radius, 16px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: 1px solid var(--divider-color);
        }
        .map-card {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .map-header, .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 12px;
        }
        .map-stage {
          position: relative;
          min-height: 520px;
          height: 520px;
          border-radius: 18px;
          overflow: hidden;
          background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.92));
        }
        .map-frame {
          display: block;
          width: 100%;
          height: 100%;
          border: 0;
          background: transparent;
        }
        .map-note {
          position: absolute;
          left: 14px;
          bottom: 14px;
          z-index: 500;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.72);
          color: rgba(255,255,255,0.82);
          font-size: 12px;
          letter-spacing: 0.03em;
          pointer-events: none;
        }
        .detail-card {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .stats {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }
        .stat {
          padding: 12px;
          border-radius: 14px;
          background: color-mix(in srgb, var(--card-background-color) 85%, var(--primary-color));
        }
        .stat-label {
          font-size: 12px;
          text-transform: uppercase;
          color: var(--secondary-text-color);
          letter-spacing: 0.08em;
        }
        .stat-value {
          margin-top: 6px;
          font-size: 15px;
          font-weight: 700;
        }
        .section {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .section h2 {
          margin: 0;
          font-size: 15px;
        }
        .list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .item {
          padding: 10px 12px;
          border-radius: 12px;
          background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-color));
        }
        .item-title {
          font-weight: 600;
          margin-bottom: 4px;
        }
        .item-meta, .item-submeta {
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .item-submeta {
          margin-top: 4px;
        }
        .empty, .error {
          padding: 18px;
          border-radius: 14px;
          background: color-mix(in srgb, var(--card-background-color) 86%, var(--warning-color, #f59e0b));
          color: var(--primary-text-color);
        }
        .error {
          background: color-mix(in srgb, var(--card-background-color) 82%, var(--error-color, #ef4444));
        }
        @media (max-width: 1100px) {
          .content {
            grid-template-columns: 1fr;
          }
          .map-stage {
            min-height: 420px;
            height: 420px;
          }
        }
      </style>
      <div class="page">
        <div class="header">
          <div class="title">
            <h1>Presence Timeline</h1>
            <div class="subtitle">Location history and family presence timelines for Home Assistant.</div>
          </div>
          <div class="toolbar">
            <button id="refresh-button" type="button">${this._loading ? "Refreshing..." : "Refresh"}</button>
          </div>
        </div>
        ${this._error ? `<div class="error">${this._escape(this._error)}</div>` : ""}
        <div class="status-row">
          ${this._summary.map((member) => this._badgeTemplate(member)).join("")}
        </div>
        <div class="content">
          <div class="card map-card">
            <div class="map-header">
              <div>
                <div class="stat-label">Map</div>
                <div class="stat-value">Current Positions${selectedMember ? ` + ${this._escape(selectedMember.display_name)} history` : ""}</div>
              </div>
              <div class="subtitle">${mapModel.markerCount} member${mapModel.markerCount === 1 ? "" : "s"}</div>
            </div>
            ${mapModel.markerCount ? this._mapTemplate() : '<div class="empty">No location data is available yet.</div>'}
          </div>
          <div class="card detail-card">
            ${selectedMember ? `
              <div class="detail-header">
                <div>
                  <div class="stat-label">Selected Member</div>
                  <div class="stat-value">${this._escape(selectedMember.display_name)}</div>
                </div>
                <div class="subtitle">${this._statusText(selectedMember)}</div>
              </div>
              <div class="stats">
                <div class="stat">
                  <div class="stat-label">Battery</div>
                  <div class="stat-value">${selectedMember.battery_level ?? "Unknown"}</div>
                </div>
                <div class="stat">
                  <div class="stat-label">Place</div>
                  <div class="stat-value">${this._escape(selectedMember.current_location_label ?? "In transit")}</div>
                </div>
                <div class="stat">
                  <div class="stat-label">Last Seen</div>
                  <div class="stat-value">${this._escape(this._formatDateTime(selectedMember.observed_at || selectedMember.last_seen_at))}</div>
                </div>
                <div class="stat">
                  <div class="stat-label">History Window</div>
                  <div class="stat-value">${this._panel?.config?.defaultHistoryHours ?? DEFAULT_HISTORY_HOURS}h</div>
                </div>
              </div>
              <div class="section">
                <h2>Stops</h2>
                <div class="list">
                  ${historyStops.length ? historyStops.slice(0, 6).map((stop) => this._stopTemplate(stop)).join("") : '<div class="empty">No qualifying stops in the selected window.</div>'}
                </div>
              </div>
              <div class="section">
                <h2>Trips</h2>
                <div class="list">
                  ${historyTrips.length ? historyTrips.slice(0, 6).map((trip) => this._tripTemplate(trip)).join("") : '<div class="empty">No trips in the selected window.</div>'}
                </div>
              </div>
            ` : '<div class="empty">Select a member to load history and trip detail.</div>'}
          </div>
        </div>
      </div>
    `;

    this.shadowRoot.querySelector("#refresh-button")?.addEventListener("click", () => this._loadSummary(true));
      this.shadowRoot.querySelectorAll(".badge").forEach((button) => {
      button.addEventListener("click", () => this._loadMemberPanel(button.dataset.memberId));
    });

    this._renderMapFrame(mapModel).catch((err) => {
      if (!this._error) {
        this._error = this._normalizeError(err);
        this._render();
      }
    });
  }

  _badgeTemplate(member) {
    const selected = member.member_id === this._selectedMemberId ? "selected" : "";
    return `
      <button class="badge" ${selected} data-member-id="${member.member_id}">
        <div class="badge-top">
          <div class="badge-name">${this._escape(member.display_name)}</div>
          <div class="badge-state">${this._escape(member.status || "unknown")}</div>
        </div>
        <div class="badge-detail">${this._escape(this._statusText(member))}</div>
      </button>
    `;
  }

  _mapTemplate() {
    return `
      <div class="map-stage">
        <iframe id="map-frame" class="map-frame" title="Presence Timeline family map"></iframe>
        <div class="map-note">Drag to pan, scroll to zoom, click markers and stops for detail.</div>
      </div>
    `;
  }

  _stopTemplate(stop) {
    const title = stop.label || "Unnamed stop";
    const durationMinutes = Math.round((stop.duration_seconds || 0) / 60);
    const address = stop.address && stop.address !== stop.label ? `<div class="item-submeta">${this._escape(stop.address)}</div>` : "";
    return `
      <div class="item">
        <div class="item-title">${this._escape(title)}${stop.is_current ? " · Current" : ""}</div>
        <div class="item-meta">${durationMinutes} min · ${this._escape(this._formatDateTime(stop.started_at))} to ${this._escape(this._formatDateTime(stop.ended_at))}</div>
        ${address}
      </div>
    `;
  }

  _tripTemplate(trip) {
    const distance = typeof trip.distance_m === "number" ? `${Math.round(trip.distance_m)} m` : "Distance unknown";
    const from = trip.start_label || "Unknown start";
    const to = trip.end_label || "Unknown end";
    return `
      <div class="item">
        <div class="item-title">${this._escape(from)} → ${this._escape(to)}</div>
        <div class="item-meta">${distance} · ${this._escape(this._formatDateTime(trip.started_at))}${trip.ended_at ? ` to ${this._escape(this._formatDateTime(trip.ended_at))}` : ""}</div>
      </div>
    `;
  }

  _statusText(member) {
    if (member.status === "stopped" && member.status_detail) {
      return `Stopped at ${member.status_detail}`;
    }
    if (member.status === "moving") {
      return member.current_location_label ? `Moving near ${member.current_location_label}` : "Moving";
    }
    return "No recent location";
  }

  _buildMapModel(selectedMember, memberPanel) {
    const markers = [];
    const stops = [];

    for (const member of this._summary) {
      if (member.latitude == null || member.longitude == null) {
        continue;
      }
      markers.push({
        memberId: member.member_id,
        label: member.display_name,
        status: member.status,
        detail: this._statusText(member),
        observedAt: member.observed_at || member.last_seen_at,
        latitude: member.latitude,
        longitude: member.longitude,
        batteryLevel: member.battery_level,
        selected: member.member_id === this._selectedMemberId,
      });
    }

    for (const stop of memberPanel?.stops ?? []) {
      if (stop.latitude == null || stop.longitude == null) {
        continue;
      }
      stops.push(stop);
    }

    return {
      markerCount: markers.length,
      markers,
      historySegments: buildHistorySegments(memberPanel?.history ?? [], memberPanel?.timeline ?? []),
      stops,
    };
  }

  async _renderMapFrame(mapModel) {
    const frame = this.shadowRoot.getElementById("map-frame");
    if (!frame || !mapModel.markerCount) {
      this._renderedMapSignature = null;
      return;
    }

    const nextSignature = createMapRenderSignature(mapModel);
    if (nextSignature === this._renderedMapSignature) {
      return;
    }

    frame.srcdoc = this._mapDocument(mapModel);
    this._renderedMapSignature = nextSignature;
  }

  _mapDocument(mapModel) {
    const modelJson = JSON.stringify(mapModel).replaceAll("<", "\\u003c");
    return `
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <link rel="stylesheet" href="${LEAFLET_CSS_URL}?v=${ASSET_VERSION}">
          <style>
            html, body, #map {
              height: 100%;
              margin: 0;
              background: #0f172a;
              color: #e2e8f0;
              font-family: system-ui, sans-serif;
            }
            .leaflet-container {
              background: #0f172a;
            }
            .leaflet-popup-content-wrapper,
            .leaflet-popup-tip {
              background: rgba(15, 23, 42, 0.96);
              color: #e2e8f0;
            }
            .leaflet-popup-content {
              margin: 12px 14px;
              line-height: 1.45;
              min-width: 180px;
            }
            .popup-title {
              font-weight: 700;
              margin-bottom: 6px;
            }
            .popup-line {
              color: rgba(226, 232, 240, 0.86);
              font-size: 13px;
            }
            .stop-waypoint {
              background: transparent;
              border: 0;
            }
            .stop-waypoint span {
              display: grid;
              place-items: center;
              width: 28px;
              height: 28px;
              border-radius: 999px;
              border: 2px solid #99f6e4;
              background: rgba(15, 118, 110, 0.94);
              color: #f8fafc;
              font-size: 13px;
              font-weight: 700;
              box-shadow: 0 8px 18px rgba(15, 23, 42, 0.36);
            }
            .stop-waypoint.current span {
              border-color: #fdba74;
              background: rgba(249, 115, 22, 0.96);
            }
          </style>
        </head>
        <body>
          <div id="map" role="img" aria-label="Presence Timeline family map"></div>
          <script src="${LEAFLET_JS_URL}?v=${ASSET_VERSION}"></script>
          <script>
            const model = ${modelJson};

            const escapeHtml = (value) => String(value ?? "")
              .replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;")
              .replaceAll("'", "&#39;");

            const formatDateTime = (value) => {
              if (!value) {
                return "Unknown";
              }
              const date = new Date(value);
              if (Number.isNaN(date.getTime())) {
                return String(value);
              }
              return date.toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              });
            };

            const map = L.map(document.getElementById("map"), {
              zoomControl: true,
              preferCanvas: true,
            });

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
              maxZoom: 19,
              attribution: "&copy; OpenStreetMap contributors",
            }).addTo(map);

            const bounds = [];
            const addBounds = (latitude, longitude) => {
              if (latitude == null || longitude == null) {
                return;
              }
              bounds.push([latitude, longitude]);
            };

            for (const member of model.markers) {
              addBounds(member.latitude, member.longitude);
              const marker = L.circleMarker([member.latitude, member.longitude], {
                radius: member.selected ? 9 : 7,
                color: "#e2e8f0",
                weight: 2,
                fillColor: member.selected ? "#f97316" : "#38bdf8",
                fillOpacity: 0.95,
              }).addTo(map);
              marker.bindPopup(\`
                <div class="popup-title">\${escapeHtml(member.label)}</div>
                <div class="popup-line">\${escapeHtml(member.detail || "No recent location")}</div>
                <div class="popup-line">Last seen: \${escapeHtml(formatDateTime(member.observedAt))}</div>
                <div class="popup-line">Battery: \${escapeHtml(member.batteryLevel ?? "Unknown")}</div>
              \`);
            }

            for (const segment of model.historySegments) {
              if (segment.length < 2) {
                continue;
              }

              const route = segment.map((point) => {
                addBounds(point.latitude, point.longitude);
                return [point.latitude, point.longitude];
              });
              L.polyline(route, {
                color: "#22d3ee",
                weight: 4,
                opacity: 0.9,
              }).addTo(map);
            }

            model.stops.forEach((stop, index) => {
              addBounds(stop.latitude, stop.longitude);
              const marker = L.marker([stop.latitude, stop.longitude], {
                icon: L.divIcon({
                  className: "stop-waypoint" + (stop.is_current ? " current" : ""),
                  html: "<span>" + (index + 1) + "</span>",
                  iconSize: [28, 28],
                  iconAnchor: [14, 14],
                }),
              }).addTo(map);

              const durationMinutes = Math.round((stop.duration_seconds || 0) / 60);
              const address = stop.address && stop.address !== stop.label
                ? \`<div class="popup-line">\${escapeHtml(stop.address)}</div>\`
                : "";

              marker.bindPopup(\`
                <div class="popup-title">\${escapeHtml(stop.label || "Unnamed stop")}\${stop.is_current ? " · Current" : ""}</div>
                \${address}
                <div class="popup-line">\${durationMinutes} min</div>
                <div class="popup-line">\${escapeHtml(formatDateTime(stop.started_at))} to \${escapeHtml(formatDateTime(stop.ended_at))}</div>
              \`);
            });

            if (bounds.length === 1) {
              map.setView(bounds[0], 15);
            } else if (bounds.length > 1) {
              map.fitBounds(bounds, { padding: [36, 36] });
            } else {
              map.setView([33.0, -80.0], 11);
            }

            window.requestAnimationFrame(() => map.invalidateSize());
          </script>
        </body>
      </html>
    `;
  }

  _formatDateTime(value) {
    if (!value) {
      return "Unknown";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }
    return date.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  _normalizeError(err) {
    if (!err) {
      return "Unknown Presence Timeline error";
    }
    if (typeof err === "string") {
      return err;
    }
    if (typeof err.message === "string" && err.message) {
      return err.message;
    }
    try {
      return JSON.stringify(err);
    } catch (_jsonError) {
      return String(err);
    }
  }

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
}

customElements.define("presence-timeline-panel", PresenceTimelinePanel);
