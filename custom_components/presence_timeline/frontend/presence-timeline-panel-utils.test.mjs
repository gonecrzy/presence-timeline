import test from "node:test";
import assert from "node:assert/strict";

import {
  buildHistoryWindow,
  buildPanelMapModel,
  buildRefreshStatus,
  formatMemberBadgeStatus,
  formatStopWaypointLabel,
  normalizeHistoryHours,
} from "./presence-timeline-panel-utils.js";

test("normalizeHistoryHours accepts supported values and falls back otherwise", () => {
  assert.equal(normalizeHistoryHours(4), 4);
  assert.equal(normalizeHistoryHours("168"), 168);
  assert.equal(normalizeHistoryHours(999, 24), 24);
});

test("buildHistoryWindow returns the selected time range", () => {
  const window = buildHistoryWindow(12, new Date("2026-07-11T12:00:00Z"));

  assert.equal(window.hours, 12);
  assert.equal(window.startIso, "2026-07-11T00:00:00.000Z");
  assert.equal(window.endIso, "2026-07-11T12:00:00.000Z");
});

test("buildRefreshStatus distinguishes connected stale and retrying states", () => {
  const now = new Date("2026-07-11T12:30:00Z");

  assert.deepEqual(
    buildRefreshStatus({ state: "connected", last_event_at: "2026-07-11T12:25:00Z" }, now),
    { tone: "good", label: "Connected", detail: "Updated 5m ago" },
  );
  assert.deepEqual(
    buildRefreshStatus({ state: "connected", last_event_at: "2026-07-11T11:30:00Z" }, now),
    { tone: "stale", label: "Stale", detail: "Last event 60m ago" },
  );
  assert.deepEqual(
    buildRefreshStatus({ state: "retrying", retry_delay_seconds: 10 }, now),
    { tone: "error", label: "Unavailable", detail: "Retrying in 10s" },
  );
});

test("formatStopWaypointLabel uses alphabetic markers", () => {
  assert.equal(formatStopWaypointLabel(0), "A");
  assert.equal(formatStopWaypointLabel(1), "B");
  assert.equal(formatStopWaypointLabel(25), "Z");
  assert.equal(formatStopWaypointLabel(26), "AA");
});

test("formatMemberBadgeStatus compacts stopped state wording", () => {
  assert.equal(formatMemberBadgeStatus({ status: "stopped", status_detail: "Home" }), "At Home");
  assert.equal(formatMemberBadgeStatus({ status: "moving", current_location_label: "Main Street" }), "Near Main Street");
});

test("buildPanelMapModel omits history layers in current-only mode", () => {
  const summary = [
    {
      member_id: "m1",
      display_name: "Sam",
      status: "stopped",
      status_detail: "Home",
      observed_at: "2026-07-11T12:00:00Z",
      latitude: 1,
      longitude: 2,
      battery_level: 80,
    },
  ];
  const panel = {
    history: [{ observed_at: "2026-07-11T11:00:00Z", latitude: 1, longitude: 2 }],
    timeline: [],
    stops: [{ label: "Home", latitude: 1, longitude: 2 }],
  };

  const mapModel = buildPanelMapModel(summary, "m1", panel, {
    showHistory: false,
    buildHistorySegments: () => [[{ observedAt: "2026-07-11T11:00:00Z", latitude: 1, longitude: 2 }]],
  });

  assert.equal(mapModel.markers.length, 1);
  assert.deepEqual(mapModel.historySegments, []);
  assert.deepEqual(mapModel.stops, []);
});

test("buildPanelMapModel assigns alphabetic waypoint labels to stops", () => {
  const mapModel = buildPanelMapModel([], null, {
    history: [],
    timeline: [],
    stops: [
      { label: "Home", latitude: 1, longitude: 2 },
      { label: "Store", latitude: 3, longitude: 4 },
    ],
  }, {
    showHistory: true,
    buildHistorySegments: () => [],
  });

  assert.equal(mapModel.stops[0].waypointLabel, "A");
  assert.equal(mapModel.stops[1].waypointLabel, "B");
});
