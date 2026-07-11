const DEFAULT_HISTORY_GAP_MS = 20 * 60 * 1000;

export function buildHistorySegments(history, timeline, options = {}) {
  const normalized = (history || [])
    .map(normalizeHistoryPoint)
    .filter((point) => point && point.observedAt && point.latitude != null && point.longitude != null);

  if (!normalized.length) {
    return [];
  }

  const tripSegments = buildTripSegments(normalized, timeline || []);
  if (tripSegments.length) {
    return tripSegments;
  }

  return buildGapSegments(normalized, options.maxGapMs ?? DEFAULT_HISTORY_GAP_MS);
}

export function createMapRenderSignature(mapModel) {
  return JSON.stringify({
    markerCount: mapModel?.markerCount ?? 0,
    markers: (mapModel?.markers ?? []).map((marker) => ({
      memberId: marker.memberId,
      latitude: marker.latitude,
      longitude: marker.longitude,
      selected: marker.selected,
      observedAt: marker.observedAt,
    })),
    historySegments: (mapModel?.historySegments ?? []).map((segment) =>
      segment.map((point) => ({
        observedAt: point.observedAt,
        latitude: point.latitude,
        longitude: point.longitude,
      })),
    ),
    stops: (mapModel?.stops ?? []).map((stop) => ({
      label: stop.label,
      latitude: stop.latitude,
      longitude: stop.longitude,
      started_at: stop.started_at,
      ended_at: stop.ended_at,
      is_current: stop.is_current,
    })),
  });
}

function buildTripSegments(points, timeline) {
  const tripItems = timeline
    .filter((item) => item?.kind === "trip" && item.started_at && item.ended_at)
    .map((item) => ({
      startedAtMs: Date.parse(item.started_at),
      endedAtMs: Date.parse(item.ended_at),
    }))
    .filter((item) => Number.isFinite(item.startedAtMs) && Number.isFinite(item.endedAtMs) && item.endedAtMs >= item.startedAtMs);

  const segments = [];
  for (const trip of tripItems) {
    const segment = points.filter((point) => point.observedAtMs >= trip.startedAtMs && point.observedAtMs <= trip.endedAtMs);
    if (segment.length > 1) {
      segments.push(segment);
    }
  }
  return segments;
}

function buildGapSegments(points, maxGapMs) {
  const segments = [];
  let current = [];

  for (const point of points) {
    const previous = current[current.length - 1];
    if (!previous || point.observedAtMs - previous.observedAtMs <= maxGapMs) {
      current.push(point);
      continue;
    }

    if (current.length > 1) {
      segments.push(current);
    }
    current = [point];
  }

  if (current.length > 1) {
    segments.push(current);
  }

  return segments;
}

function normalizeHistoryPoint(point) {
  if (!point) {
    return null;
  }

  const observedAt = point.observedAt ?? point.observed_at ?? null;
  const observedAtMs = observedAt ? Date.parse(observedAt) : NaN;
  return {
    observedAt,
    observedAtMs,
    latitude: point.latitude,
    longitude: point.longitude,
  };
}
