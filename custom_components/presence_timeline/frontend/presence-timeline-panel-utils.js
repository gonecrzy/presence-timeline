const HISTORY_WINDOW_OPTIONS = [
  { hours: 4, label: "4h" },
  { hours: 12, label: "12h" },
  { hours: 24, label: "24h" },
  { hours: 48, label: "48h" },
  { hours: 72, label: "3d" },
  { hours: 168, label: "7d" },
];

const STATUS_STALE_MINUTES = 20;

export function getHistoryWindowOptions() {
  return HISTORY_WINDOW_OPTIONS.map((option) => ({ ...option }));
}

export function normalizeHistoryHours(value, fallback = 24) {
  const numeric = Number(value);
  return HISTORY_WINDOW_OPTIONS.some((option) => option.hours === numeric) ? numeric : fallback;
}

export function buildHistoryWindow(hours, now = new Date()) {
  const normalizedHours = normalizeHistoryHours(hours);
  const end = new Date(now);
  const start = new Date(end.getTime() - normalizedHours * 60 * 60 * 1000);
  return { hours: normalizedHours, startIso: start.toISOString(), endIso: end.toISOString() };
}

export function buildRefreshStatus(status, now = new Date(), summary = []) {
  const state = status?.state ?? "unknown";
  const lastEventAt = parseDate(status?.last_event_at ?? status?.lastEventAt);
  const lastConnectedAt = parseDate(status?.last_connected_at ?? status?.lastConnectedAt);
  const fallbackSummaryAt = latestSummaryTimestamp(summary);
  const baseline = lastEventAt ?? lastConnectedAt ?? fallbackSummaryAt;
  const ageMinutes = baseline ? Math.max(0, Math.round((now.getTime() - baseline.getTime()) / 60000)) : null;

  if (state === "connected" && ageMinutes !== null && ageMinutes <= STATUS_STALE_MINUTES) {
    return {
      tone: "good",
      label: "Connected",
      detail: ageMinutes <= 1 ? "Live now" : `Updated ${ageMinutes}m ago`,
    };
  }
  if (state === "connected") {
    return {
      tone: "stale",
      label: "Stale",
      detail: ageMinutes == null ? "No event timestamp" : `Last event ${ageMinutes}m ago`,
    };
  }
  if (state === "retrying") {
    return {
      tone: "error",
      label: "Unavailable",
      detail: status?.retry_delay_seconds != null || status?.retryDelaySeconds != null
        ? `Retrying in ${status.retry_delay_seconds ?? status.retryDelaySeconds}s`
        : "Retrying",
    };
  }
  if (state === "disabled") {
    return {
      tone: "error",
      label: "Disabled",
      detail: "Ingestion disabled",
    };
  }
  if (ageMinutes !== null && ageMinutes <= STATUS_STALE_MINUTES) {
    return {
      tone: "good",
      label: "Connected",
      detail: ageMinutes <= 1 ? "Live now" : `Updated ${ageMinutes}m ago`,
    };
  }
  if (ageMinutes !== null) {
    return {
      tone: "stale",
      label: "Stale",
      detail: `Last update ${ageMinutes}m ago`,
    };
  }
  return {
    tone: "error",
    label: "Unavailable",
    detail: "Status unknown",
  };
}

export function formatStopWaypointLabel(index) {
  if (!Number.isInteger(index) || index < 0) {
    return "?";
  }

  let value = index;
  let label = "";
  do {
    label = String.fromCharCode(65 + (value % 26)) + label;
    value = Math.floor(value / 26) - 1;
  } while (value >= 0);
  return label;
}

export function formatMemberBadgeStatus(member) {
  if (!member) {
    return "No recent location";
  }
  if (member.status === "stopped" && member.status_detail) {
    return `At ${member.status_detail}`;
  }
  if (member.status === "moving") {
    return member.current_location_label ? `Near ${member.current_location_label}` : "Moving";
  }
  return "No recent location";
}

export function buildPanelMapModel(summary, selectedMemberId, memberPanel, options = {}) {
  const markers = [];
  const stops = [];
  const showHistory = options.showHistory !== false;

  for (const member of summary || []) {
    if (member.latitude == null || member.longitude == null) {
      continue;
    }
    markers.push({
      memberId: member.member_id,
      label: member.display_name,
      status: member.status,
      detail: formatMemberBadgeStatus(member),
      observedAt: member.observed_at || member.last_seen_at,
      latitude: member.latitude,
      longitude: member.longitude,
      batteryLevel: member.battery_level,
      selected: member.member_id === selectedMemberId,
    });
  }

  if (showHistory) {
    for (const stop of memberPanel?.stops ?? []) {
      if (stop.latitude == null || stop.longitude == null) {
        continue;
      }
      stops.push({
        ...stop,
        waypointLabel: formatStopWaypointLabel(stops.length),
      });
    }
  }

  return {
    markerCount: markers.length,
    markers,
    historySegments: showHistory ? options.buildHistorySegments(memberPanel?.history ?? [], memberPanel?.timeline ?? []) : [],
    stops,
  };
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function latestSummaryTimestamp(summary) {
  let latest = null;
  for (const member of summary || []) {
    const candidate = parseDate(member?.observed_at ?? member?.observedAt ?? member?.last_seen_at ?? member?.lastSeenAt);
    if (!candidate) {
      continue;
    }
    if (!latest || candidate > latest) {
      latest = candidate;
    }
  }
  return latest;
}
