import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("panel source renders the map inline via srcdoc with carto tile safeguards", () => {
  const source = readFileSync(new URL("./presence-timeline-panel.js", import.meta.url), "utf8");

  assert.match(source, /frame\.srcdoc = this\._mapDocument\(mapModel\);/);
  assert.match(source, /const PANEL_PREFERENCES_KEY = "presence-timeline-panel-preferences";/);
  assert.match(source, /globalThis\.localStorage\?\.getItem\(PANEL_PREFERENCES_KEY\)/);
  assert.match(source, /globalThis\.localStorage\?\.setItem\(PANEL_PREFERENCES_KEY,/);
  assert.match(source, /const LEAFLET_CSS_URL = `\$\{STATIC_ROOT\}\/vendor\/leaflet\.css`;/);
  assert.match(source, /const LEAFLET_JS_URL = `\$\{STATIC_ROOT\}\/vendor\/leaflet\.js`;/);
  assert.match(source, /L\.control\.layers\(baseLayers, null,/);
  assert.match(source, /"Street map": L\.tileLayer\("https:\/\/\{s\}\.basemaps\.cartocdn\.com\/rastertiles\/voyager\/\{z\}\/\{x\}\/\{y\}\{r\}\.png"/);
  assert.match(source, /window\.parent\.postMessage\(\{/);
  assert.match(source, /presence-timeline-map-theme-change/);
  assert.match(source, /fadeAnimation:\s*false/);
  assert.match(source, /\.leaflet-container img\.leaflet-tile\.leaflet-tile-loaded\s*\{/);
});
