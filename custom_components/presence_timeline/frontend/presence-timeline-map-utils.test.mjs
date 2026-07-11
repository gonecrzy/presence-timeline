import test from "node:test";
import assert from "node:assert/strict";

import {
  buildHistorySegments,
  createMapRenderSignature,
} from "./presence-timeline-map-utils.js";

test("buildHistorySegments groups history by trip windows", () => {
  const history = [
    { observed_at: "2026-07-11T10:00:00Z", latitude: 33.0, longitude: -80.0 },
    { observed_at: "2026-07-11T10:03:00Z", latitude: 33.01, longitude: -80.01 },
    { observed_at: "2026-07-11T11:00:00Z", latitude: 33.1, longitude: -80.1 },
    { observed_at: "2026-07-11T11:04:00Z", latitude: 33.11, longitude: -80.11 },
  ];
  const timeline = [
    { kind: "trip", started_at: "2026-07-11T10:00:00Z", ended_at: "2026-07-11T10:03:00Z" },
    { kind: "trip", started_at: "2026-07-11T11:00:00Z", ended_at: "2026-07-11T11:04:00Z" },
  ];

  const segments = buildHistorySegments(history, timeline);

  assert.equal(segments.length, 2);
  assert.deepEqual(
    segments.map((segment) => segment.map((point) => point.observedAt)),
    [
      ["2026-07-11T10:00:00Z", "2026-07-11T10:03:00Z"],
      ["2026-07-11T11:00:00Z", "2026-07-11T11:04:00Z"],
    ],
  );
});

test("buildHistorySegments falls back to gap-based segments without trip data", () => {
  const history = [
    { observed_at: "2026-07-11T10:00:00Z", latitude: 33.0, longitude: -80.0 },
    { observed_at: "2026-07-11T10:02:00Z", latitude: 33.01, longitude: -80.01 },
    { observed_at: "2026-07-11T10:45:00Z", latitude: 33.1, longitude: -80.1 },
    { observed_at: "2026-07-11T10:47:00Z", latitude: 33.11, longitude: -80.11 },
  ];

  const segments = buildHistorySegments(history, []);

  assert.equal(segments.length, 2);
  assert.deepEqual(
    segments.map((segment) => segment.map((point) => point.observedAt)),
    [
      ["2026-07-11T10:00:00Z", "2026-07-11T10:02:00Z"],
      ["2026-07-11T10:45:00Z", "2026-07-11T10:47:00Z"],
    ],
  );
});

test("createMapRenderSignature is stable and changes when map data changes", () => {
  const mapModel = {
    markerCount: 1,
    markers: [{ memberId: "a", latitude: 1, longitude: 2, selected: true }],
    historySegments: [[{ observedAt: "2026-07-11T10:00:00Z", latitude: 1, longitude: 2 }]],
    stops: [{ label: "Home", latitude: 1, longitude: 2 }],
  };

  const first = createMapRenderSignature(mapModel);
  const second = createMapRenderSignature(mapModel);
  const changed = createMapRenderSignature({
    ...mapModel,
    stops: [{ label: "Work", latitude: 1, longitude: 2 }],
  });

  assert.equal(first, second);
  assert.notEqual(first, changed);
});
