import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);
const read = (path) => readFile(new URL(path, root), "utf8");

test("the Ultima exhibit exposes Codex Sol as an independent third tab", async () => {
  const [page, viewer, mount] = await Promise.all([
    read("src/pages/[slug].vue"),
    read("src/exhibits/cloud-ultima-weapon-codex-sol/CodexSolViewer.vue"),
    read("src/exhibits/cloud-ultima-weapon-codex-sol/mountCodexSolViewer.ts"),
  ]);

  assert.match(page, /Codex Sol 5\.6 xhigh · independent rerun/);
  assert.match(page, /ultimaTab === ['"]codex-sol['"]/);
  assert.match(page, /cloud-ultima-weapon-codex-sol\/CodexSolViewer\.vue/);
  assert.match(viewer, /mountCodexSolViewer/);
  assert.match(mount, /\.\/createCodexSolUltimaWeaponModel/);
  assert.doesNotMatch(mount, /cloud-ultima-weapon(?:-fable)?\//);
});
