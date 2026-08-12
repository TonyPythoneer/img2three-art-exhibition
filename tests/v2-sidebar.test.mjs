import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("FF7 menu gutter does not displace inspector icon buttons", async () => {
  const css = await readFile(path.join(ROOT, "src/styles/ff7-page.css"), "utf8");
  assert.match(css, /a:not\(\.panel-dock-link\)/);
  assert.match(css, /button:not\(\.chip\):not\(\.icon-btn\):not\(\.panel-dock-item\)/);
});

test("v2 sidebar exposes compact section navigation", async () => {
  const source = await readFile(path.join(ROOT, "src/components/stage/ExhibitStage.vue"), "utf8");
  const styles = await readFile(path.join(ROOT, "src/styles/showcase/stage-panel.css"), "utf8");
  const ff7Styles = await readFile(path.join(ROOT, "src/styles/ff7-page.css"), "utf8");
  for (const id of ["brief", "components", "controls", "spec"]) {
    assert.match(source, new RegExp(`id=["']${id}["']`));
  }
  assert.doesNotMatch(source, /<StagePanelBar/);
  assert.doesNotMatch(source, /demo-panel-bar/);
  assert.match(source, /panel-dock/);
  assert.match(source, /panel-dock-link/);
  assert.match(source, /aria-label="Back to exhibition list"/);
  assert.match(source, /activeDock = ref<string>\([\s\S]*?: "brief"\)/);
  assert.match(source, /id: "brief", label: "Brief"/);
  assert.match(source, /v-show="activeDock === 'brief'"/);
  assert.match(styles, /\.panel-dock[\s\S]*?flex-direction:\s*column/);
  assert.match(styles, /\.panel-dock-divider/);
  assert.match(ff7Styles, /\.ff7-page \.panel-dock-item \{[\s\S]*?border:/);
  assert.match(ff7Styles, /\.ff7-page \.panel-dock-section(?:,|\s*\{)[\s\S]*?border:/);
  assert.match(ff7Styles, /\.ff7-page \.demo-panel \{[\s\S]*?overflow:\s*visible/);
  assert.match(ff7Styles, /\.ff7-page \.demo-panel-body \{[\s\S]*?border:\s*0/);
  assert.match(ff7Styles, /\.ff7-page \.demo-panel \{[\s\S]*?width:\s*min\(390px/);
  assert.ok((ff7Styles.match(/inset 0 0 0 5px var\(--ff7-border-highlight\)/g) ?? []).length >= 2);
});

// Brief wraps PanelSectionTitle.vue in a header the other four tabs do not have. The wrapper
// must stay out of the layout, or Brief's subtitle sits lower than every other tab's.
test("the section title sits at the same offset on every dock tab", async () => {
  const styles = await readFile(path.join(ROOT, "src/styles/showcase/stage-panel.css"), "utf8");
  assert.match(styles, /\.demo-panel-head \{\s*display:\s*contents;\s*\}/);
});

test("v2 controls use an FF7 settings window layout", async () => {
  const source = await readFile(
    path.join(ROOT, "src/pages/ff7-cloud-ultima-weapon/index.vue"),
    "utf8",
  );
  const shell = await readFile(path.join(ROOT, "src/components/stage/ExhibitStage.vue"), "utf8");
  const ff7Styles = await readFile(path.join(ROOT, "src/styles/ff7-page.css"), "utf8");
  assert.match(shell, /ff7-settings-body/);
  assert.match(source, /panel-row-options/);
  assert.match(ff7Styles, /\.ff7-page #controls \.panel-row-options/);
  assert.match(ff7Styles, /\.ff7-page #controls \.panel-row-label/);
  assert.match(ff7Styles, /\.ff7-page #controls \.panel-slider \{[\s\S]*?appearance:\s*none/);
  assert.match(ff7Styles, /#controls \.panel-slider::-webkit-slider-thumb/);
});
