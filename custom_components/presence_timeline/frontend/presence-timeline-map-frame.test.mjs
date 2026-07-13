import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("map frame uses a supported raster basemap endpoint", () => {
  const html = readFileSync(new URL("./presence-timeline-map-frame.html", import.meta.url), "utf8");

  assert.match(html, /https:\/\/\{s\}\.basemaps\.cartocdn\.com\/dark_all\/\{z\}\/\{x\}\/\{y\}\{r\}\.png/);
});
