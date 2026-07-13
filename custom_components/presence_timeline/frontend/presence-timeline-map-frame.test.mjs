import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("map frame prevents leaking the Home Assistant referer to tile hosts", () => {
  const html = readFileSync(new URL("./presence-timeline-map-frame.html", import.meta.url), "utf8");

  assert.match(html, /referrerPolicy:\s*"no-referrer"/);
});
