const DEFAULT_SUMMARY_API = "/api/gpstrack/panel/summary";
const DEFAULT_MEMBER_API_TEMPLATE = "/api/gpstrack/panel/members/{member_id}";
const DEFAULT_HISTORY_HOURS = 24;

class GpsTrackPanel extends HTMLElement {
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
  }

  set hass(hass) {
    this._hass = hass;
    this._ensureLoaded();
    this._render();
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
      this._error = err?.message || String(err);
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
      this._error = err?.message || String(err);
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
    if (this._hass?.callApi) {
      try {
        const normalized = path.startsWith("/api/") ? path.slice(5) : path.replace(/^\//, "");
        return await this._hass.callApi("GET", normalized);
      } catch (err) {
        if (err?.status !== 404) {
          throw err;
        }
      }
    }

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
      throw new Error(`GpsTrack panel request failed: ${response.status}`);
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
          border-radius: 18px;
          overflow: hidden;
          background:
            linear-gradient(0deg, rgba(34, 197, 94, 0.07), rgba(34, 197, 94, 0.07)),
            repeating-linear-gradient(0deg, rgba(255,255,255,0.05), rgba(255,255,255,0.05) 1px, transparent 1px, transparent 56px),
            repeating-linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.05) 1px, transparent 1px, transparent 56px),
            linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.92));
        }
        svg {
          width: 100%;
          height: 100%;
          display: block;
        }
        .map-note {
          position: absolute;
          left: 14px;
          bottom: 14px;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.72);
          color: rgba(255,255,255,0.82);
          font-size: 12px;
          letter-spacing: 0.03em;
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
        .item-meta {
          color: var(--secondary-text-color);
          font-size: 13px;
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
          }
        }
      </style>
      <div class="page">
        <div class="header">
          <div class="title">
            <h1>GpsTrack</h1>
            <div class="subtitle">Current family map with member history on selection</div>
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
            ${mapModel.markerCount ? this._mapTemplate(mapModel) : '<div class="empty">No location data is available yet.</div>'}
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

  _mapTemplate(mapModel) {
    const polyline = mapModel.historyPoints.length
      ? `<polyline fill="none" stroke="#22d3ee" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${mapModel.historyPoints.map((point) => `${point.x},${point.y}`).join(" ")}"></polyline>`
      : "";

    const markers = mapModel.markers.map((marker) => `
      <g>
        <circle cx="${marker.x}" cy="${marker.y}" r="${marker.selected ? 11 : 8}" fill="${marker.selected ? "#f97316" : "#38bdf8"}" stroke="rgba(255,255,255,0.92)" stroke-width="2"></circle>
        <text x="${marker.x + 14}" y="${marker.y - 14}" fill="rgba(255,255,255,0.95)" font-size="14" font-weight="700">${this._escape(marker.label)}</text>
      </g>
    `).join("");

    return `
      <div class="map-stage">
        <svg viewBox="0 0 1000 640" role="img" aria-label="GpsTrack family map">
          ${polyline}
          ${markers}
        </svg>
        <div class="map-note">Status badges use the backend stop rule: 10 minutes within 250 meters.</div>
      </div>
    `;
  }

  _stopTemplate(stop) {
    const title = stop.label || "Unnamed stop";
    const durationMinutes = Math.round((stop.duration_seconds || 0) / 60);
    return `
      <div class="item">
        <div class="item-title">${this._escape(title)}${stop.is_current ? " · Current" : ""}</div>
        <div class="item-meta">${durationMinutes} min · ${this._escape(this._formatDateTime(stop.started_at))} to ${this._escape(this._formatDateTime(stop.ended_at))}</div>
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
    const points = [];
    const markers = [];
    const history = [];

    for (const member of this._summary) {
      if (member.latitude == null || member.longitude == null) {
        continue;
      }
      points.push({ lat: member.latitude, lon: member.longitude });
      markers.push({
        lat: member.latitude,
        lon: member.longitude,
        label: member.display_name,
        selected: member.member_id === this._selectedMemberId,
      });
    }

    if (selectedMember && memberPanel?.history?.length) {
      for (const point of memberPanel.history) {
        if (point.latitude == null || point.longitude == null) {
          continue;
        }
        points.push({ lat: point.latitude, lon: point.longitude });
        history.push({ lat: point.latitude, lon: point.longitude });
      }
    }

    if (!points.length) {
      return { markerCount: 0, markers: [], historyPoints: [] };
    }

    const latitudes = points.map((point) => point.lat);
    const longitudes = points.map((point) => point.lon);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLon = Math.min(...longitudes);
    const maxLon = Math.max(...longitudes);
    const latSpan = Math.max(maxLat - minLat, 0.002);
    const lonSpan = Math.max(maxLon - minLon, 0.002);
    const padding = 48;
    const width = 1000 - padding * 2;
    const height = 640 - padding * 2;

    const project = (lat, lon) => ({
      x: padding + ((lon - minLon) / lonSpan) * width,
      y: padding + (1 - (lat - minLat) / latSpan) * height,
    });

    return {
      markerCount: markers.length,
      markers: markers.map((marker) => ({
        ...marker,
        ...project(marker.lat, marker.lon),
      })),
      historyPoints: history.map((point) => ({
        ...project(point.lat, point.lon),
      })),
    };
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

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
}

customElements.define("gpstrack-panel", GpsTrackPanel);
