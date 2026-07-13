import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("panel source renders the map inline via srcdoc with carto tile safeguards", () => {
  const source = readFileSync(new URL("./presence-timeline-panel.js", import.meta.url), "utf8");

  assert.match(source, /frame\.srcdoc = this\._mapDocument\(mapModel\);/);
  assert.match(source, /const LEAFLET_CSS_URL = `\$\{STATIC_ROOT\}\/vendor\/leaflet\.css`;/);
  assert.match(source, /const LEAFLET_JS_URL = `\$\{STATIC_ROOT\}\/vendor\/leaflet\.js`;/);
  assert.match(source, /https:\/\/\{s\}\.basemaps\.cartocdn\.com\/dark_all\/\{z\}\/\{x\}\/\{y\}\{r\}\.png/);
  assert.match(source, /fadeAnimation:\s*false/);
  assert.match(source, /\.leaflet-container img\.leaflet-tile\.leaflet-tile-loaded\s*\{/);
});
