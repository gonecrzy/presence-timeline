import test from "node:test";
import assert from "node:assert/strict";

import {
  buildHistoryWindow,
  buildPanelMapModel,
  buildRefreshStatus,
  formatDistanceImperial,
  formatMemberBadgeStatus,
  getMapThemeOptions,
  mergePanelPreferences,
  formatStopWaypointLabel,
  normalizeMapTheme,
  normalizeHistoryHours,
  resolveAssetVersion,
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

test("map theme helpers expose supported themes and normalize invalid values", () => {
  assert.deepEqual(
    getMapThemeOptions(),
    [
      { value: "dark", label: "Dark map" },
      { value: "light", label: "Light map" },
    ],
  );
  assert.equal(normalizeMapTheme("light"), "light");
  assert.equal(normalizeMapTheme("dark"), "dark");
  assert.equal(normalizeMapTheme("other", "light"), "light");
});

test("mergePanelPreferences normalizes stored panel state", () => {
  assert.deepEqual(
    mergePanelPreferences(
      { historyHours: "48", mapTheme: "light", showHistoryRoutes: false },
      { historyHours: 24, mapTheme: "dark", showHistoryRoutes: true },
    ),
    { historyHours: 48, mapTheme: "light", showHistoryRoutes: false },
  );
  assert.deepEqual(
    mergePanelPreferences(
      { historyHours: "999", mapTheme: "bogus" },
      { historyHours: 12, mapTheme: "dark", showHistoryRoutes: true },
    ),
    { historyHours: 12, mapTheme: "dark", showHistoryRoutes: true },
  );
});

test("resolveAssetVersion uses the module query version when present", () => {
  assert.equal(
    resolveAssetVersion("https://ha.example/api/presence-timeline/static/presence-timeline-panel.js?v=0.3.11"),
    "0.3.11",
  );
  assert.equal(
    resolveAssetVersion("https://ha.example/api/presence-timeline/static/presence-timeline-panel.js", "dev"),
    "dev",
  );
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

test("buildRefreshStatus falls back to fresh summary timestamps when integration status is unavailable", () => {
  const now = new Date("2026-07-11T12:30:00Z");

  assert.deepEqual(
    buildRefreshStatus(null, now, [
      { observed_at: "2026-07-11T12:27:00Z" },
      { observed_at: "2026-07-11T12:22:00Z" },
    ]),
    { tone: "good", label: "Connected", detail: "Updated 3m ago" },
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

test("formatDistanceImperial uses feet for short trips and miles for longer ones", () => {
  assert.equal(formatDistanceImperial(18), "59 ft");
  assert.equal(formatDistanceImperial(304.8), "1000 ft");
  assert.equal(formatDistanceImperial(365.76), "0.2 mi");
  assert.equal(formatDistanceImperial(4143), "2.6 mi");
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
