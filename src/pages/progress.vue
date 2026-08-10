<template>
  <div class="mx-auto max-w-5xl px-6 py-16">
    <RouterLink to="/balamb-garden" class="text-ink-soft hover:text-accent text-sm">
      ← 回 Balamb Garden 展件
    </RouterLink>

    <h1 class="mt-6 text-3xl font-semibold tracking-tight sm:text-4xl">重建進度</h1>
    <p class="text-ink-soft mt-3 max-w-3xl text-sm">
      狀態權威 = <code class="bg-panel rounded px-1">tracking/*.yaml</code>(D-008,唯讀呈現);
      量測數字來源 = <code class="bg-panel rounded px-1">artifacts/</code> gate
      JSON(顯示時併讀,不落地複本)。改動 tracking YAML 後重新 build 即同步。
    </p>

    <!-- 全域三閘門 -->
    <section class="mt-10">
      <h2 class="text-xl font-semibold">全域三道硬閘門</h2>
      <p class="text-ink-soft mt-1 text-xs">三道全過才算過,無加權分數(SPEC.md §6)。</p>
      <div class="mt-4 grid gap-4 sm:grid-cols-3">
        <div class="border-line bg-panel rounded-lg border p-4">
          <div class="flex items-baseline justify-between">
            <h3 class="font-semibold">相機</h3>
            <span :class="gateBadge(finalReport.cameraGateResult)">
              {{ finalReport.cameraGateResult }}
            </span>
          </div>
          <ul class="text-ink-soft mt-3 space-y-1 text-xs">
            <li>median {{ pct(camera.medianResidualPercentOfWidth) }} / ≤0.75%</li>
            <li>P90 {{ pct(camera.p90ResidualPercentOfWidth) }} / ≤1.50%</li>
            <li>critical 最大 {{ pct(camera.maxCriticalResidualPercentOfWidth) }} / ≤1.00%</li>
            <li>逃生門:{{ camera.escapeProtocolUsed ? "已用" : "未用" }}</li>
          </ul>
        </div>
        <div class="border-line bg-panel rounded-lg border p-4">
          <div class="flex items-baseline justify-between">
            <h3 class="font-semibold">剪影 IoU</h3>
            <span :class="gateBadge(finalReport.silhouetteGateResult)">
              {{ finalReport.silhouetteGateResult }}
            </span>
          </div>
          <ul class="text-ink-soft mt-3 space-y-1 text-xs">
            <li>IoU {{ silhouette.visibleRegionIoU.toFixed(4) }} / ≥{{ silhouette.threshold }}</li>
            <li>reference-only {{ silhouette.referenceOnlyPixels }} px</li>
            <li>render-only {{ silhouette.renderOnlyPixels }} px</li>
          </ul>
        </div>
        <div class="border-line bg-panel rounded-lg border p-4">
          <div class="flex items-baseline justify-between">
            <h3 class="font-semibold">輪廓 Chamfer</h3>
            <span :class="gateBadge(finalReport.contourGateResult)">
              {{ finalReport.contourGateResult }}
            </span>
          </div>
          <ul class="text-ink-soft mt-3 space-y-1 text-xs">
            <li>median {{ pct(contour.symmetricChamferMedianPercentOfWidth) }} / ≤1.5%</li>
            <li>P95 {{ pct(contour.symmetricChamferP95PercentOfWidth) }} / ≤4.0%</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 層級進度樹 -->
    <section v-for="bldg in buildings" :key="bldg.id" class="mt-12">
      <div class="flex flex-wrap items-baseline gap-3">
        <h2 class="text-xl font-semibold">{{ bldg.id }} {{ bldg.name }}</h2>
        <span :class="statusBadge(bldg.status)">{{ bldg.status }}</span>
      </div>
      <p v-if="bldg.notes" class="text-ink-soft mt-2 text-sm">{{ bldg.notes }}</p>

      <div class="border-line mt-5 overflow-x-auto rounded-lg border">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead>
            <tr class="border-line bg-panel border-b">
              <th class="px-4 py-2 font-medium">節點</th>
              <th class="px-4 py-2 font-medium">狀態</th>
              <th class="px-4 py-2 font-medium">零件閘門</th>
              <th class="px-4 py-2 font-medium">卡在哪</th>
              <th class="px-4 py-2 font-medium">備註 / 已知失敗</th>
              <th class="px-4 py-2 font-medium whitespace-nowrap">更新</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="asm in assembliesOf(bldg.id)" :key="asm.id">
              <tr class="border-line border-b">
                <td class="px-4 py-2.5 font-medium whitespace-nowrap">{{ asm.id }}</td>
                <td class="px-4 py-2.5">
                  <span :class="statusBadge(asm.status)">{{ asm.status }}</span>
                </td>
                <td class="px-4 py-2.5"><VerdictDots :verdicts="asm.verdicts" /></td>
                <td class="text-ink-soft px-4 py-2.5 text-xs">
                  {{ asm.blockedBy.join("、") || "—" }}
                </td>
                <td class="text-ink-soft px-4 py-2.5 text-xs">{{ asm.summary || "—" }}</td>
                <td class="text-ink-soft px-4 py-2.5 text-xs whitespace-nowrap">
                  {{ asm.updatedAt }}
                </td>
              </tr>
              <tr v-for="cmp in componentsOf(asm.id)" :key="cmp.id" class="border-line border-b">
                <td class="text-ink-soft px-4 py-2 pl-8 whitespace-nowrap">└ {{ cmp.id }}</td>
                <td class="px-4 py-2">
                  <span :class="statusBadge(cmp.status)">{{ cmp.status }}</span>
                </td>
                <td class="px-4 py-2"><VerdictDots :verdicts="cmp.verdicts" /></td>
                <td class="text-ink-soft px-4 py-2 text-xs">
                  {{ cmp.blockedBy.join("、") || "—" }}
                </td>
                <td class="text-ink-soft px-4 py-2 text-xs">{{ cmp.summary || "—" }}</td>
                <td class="text-ink-soft px-4 py-2 text-xs whitespace-nowrap">
                  {{ cmp.updatedAt }}
                </td>
              </tr>
            </template>
            <tr v-for="cmp in componentsOf(bldg.id)" :key="cmp.id" class="border-line border-b">
              <td class="px-4 py-2.5 whitespace-nowrap">{{ cmp.id }}</td>
              <td class="px-4 py-2.5">
                <span :class="statusBadge(cmp.status)">{{ cmp.status }}</span>
              </td>
              <td class="px-4 py-2.5"><VerdictDots :verdicts="cmp.verdicts" /></td>
              <td class="text-ink-soft px-4 py-2.5 text-xs">
                {{ cmp.blockedBy.join("、") || "—" }}
              </td>
              <td class="text-ink-soft px-4 py-2.5 text-xs">{{ cmp.summary || "—" }}</td>
              <td class="text-ink-soft px-4 py-2.5 text-xs whitespace-nowrap">
                {{ cmp.updatedAt }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 狀態圖例 -->
    <section class="mt-10">
      <h2 class="text-sm font-semibold">狀態圖例</h2>
      <div class="mt-3 flex flex-wrap gap-2">
        <span v-for="s in allStatuses" :key="s" :class="statusBadge(s)">{{ s }}</span>
      </div>
      <p class="text-ink-soft mt-3 text-xs">
        零件閘門欄:● IoU / ● Chamfer median / ● Chamfer P95(綠=pass、紅=fail、灰=未跑);FL =
        form-locked。verdicts 僅為 pass/fail,數值一律開
        <code class="bg-panel rounded px-1">artifacts/component-gates.json</code>。
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, type PropType } from "vue";
import { RouterLink } from "vue-router";
import { useSeoMeta } from "@unhead/vue";
import { parseTrackingYaml, type TrackingDoc } from "~/systems/tracking/parseTracking.js";

// ── tracking YAML(狀態權威)─────────────────────────────────────────────
const rawFiles = import.meta.glob("../../tracking/**/*.yaml", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

type Node = {
  id: string;
  name: string;
  type: string;
  parent: string | null;
  status: string;
  blockedBy: string[];
  verdicts: Record<string, string | boolean> | null;
  summary: string;
  notes: string;
  updatedAt: string;
};

const asString = (v: unknown): string => (typeof v === "string" ? v : "");
const asList = (v: unknown): string[] =>
  Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];

const nodes: Node[] = Object.entries(rawFiles).map(([path, src]) => {
  const doc: TrackingDoc = parseTrackingYaml(src, path);
  const gate = doc.gate_results;
  const verdicts =
    gate &&
    typeof gate === "object" &&
    !Array.isArray(gate) &&
    gate.verdicts &&
    typeof gate.verdicts === "object" &&
    !Array.isArray(gate.verdicts)
      ? (gate.verdicts as Record<string, string | boolean>)
      : null;
  const failures = asList(doc.known_failures);
  return {
    id: asString(doc.id),
    name: asString(doc.name),
    type: asString(doc.type),
    parent: typeof doc.parent === "string" ? doc.parent : null,
    status: asString(doc.status) || "planned",
    blockedBy: asList(doc.blocked_by),
    verdicts,
    summary: failures[0] ?? asString(doc.notes),
    notes: asString(doc.notes),
    updatedAt: asString(doc.updated_at),
  };
});

const buildings = computed(() => nodes.filter((n) => n.type === "building"));
const assembliesOf = (parent: string) =>
  nodes
    .filter((n) => n.type === "assembly" && n.parent === parent)
    .sort((a, b) => a.id.localeCompare(b.id));
const componentsOf = (parent: string) =>
  nodes
    .filter((n) => n.type === "component" && n.parent === parent)
    .sort((a, b) => a.id.localeCompare(b.id));

// ── gate JSON(量測數字,顯示時併讀)──────────────────────────────────────
const reports = import.meta.glob("../../artifacts/evaluation-report.json", {
  eager: true,
  import: "default",
}) as Record<string, Record<string, Record<string, unknown>>>;
const report = Object.values(reports)[0] ?? {};
const finalReport = (report.FINAL ?? {}) as {
  cameraGateResult?: string;
  silhouetteGateResult?: string;
  contourGateResult?: string;
};
const camera = (report.CAMERA ?? {}) as {
  medianResidualPercentOfWidth?: number;
  p90ResidualPercentOfWidth?: number;
  maxCriticalResidualPercentOfWidth?: number;
  escapeProtocolUsed?: boolean;
};
const silhouette = (report.SILHOUETTE ?? {}) as {
  visibleRegionIoU: number;
  threshold: number;
  referenceOnlyPixels: number;
  renderOnlyPixels: number;
};
const contour = (report.CONTOUR ?? {}) as {
  symmetricChamferMedianPercentOfWidth?: number;
  symmetricChamferP95PercentOfWidth?: number;
};

const pct = (v: number | undefined) => (v === undefined ? "—" : `${v.toFixed(3)}%`);

// ── 呈現 ────────────────────────────────────────────────────────────────
const badgeBase = "inline-block rounded border px-2 py-0.5 text-xs whitespace-nowrap ";
const statusClasses: Record<string, string> = {
  planned: "border-neutral-600 bg-neutral-700/30 text-neutral-300",
  ready: "border-sky-700 bg-sky-900/40 text-sky-300",
  in_progress: "border-blue-700 bg-blue-900/40 text-blue-300",
  blocked: "border-amber-700 bg-amber-900/40 text-amber-300",
  local_review: "border-violet-700 bg-violet-900/40 text-violet-300",
  revision_required: "border-red-700 bg-red-900/40 text-red-300",
  locally_accepted: "border-green-700 bg-green-900/40 text-green-300",
  integration_review: "border-teal-700 bg-teal-900/40 text-teal-300",
  globally_accepted: "border-emerald-700 bg-emerald-900/40 text-emerald-300",
  rejected: "border-rose-700 bg-rose-900/40 text-rose-300",
  archived: "border-neutral-700 bg-neutral-800/60 text-neutral-500",
};
const allStatuses = Object.keys(statusClasses);
const statusBadge = (s: string) => badgeBase + (statusClasses[s] ?? statusClasses.planned);
const gateBadge = (result: string | undefined) =>
  badgeBase +
  (result === "pass"
    ? statusClasses.locally_accepted
    : result === "fail"
      ? statusClasses.revision_required
      : statusClasses.planned);

const VerdictDots = defineComponent({
  props: {
    verdicts: { type: Object as PropType<Record<string, string | boolean> | null>, default: null },
  },
  setup(props) {
    const dot = (v: string | undefined) =>
      h("span", {
        class:
          "inline-block h-2.5 w-2.5 rounded-full " +
          (v === "pass" ? "bg-green-500" : v === "fail" ? "bg-red-500" : "bg-neutral-600"),
      });
    return () => {
      const v = props.verdicts;
      if (!v) return h("span", { class: "text-ink-soft text-xs" }, "—");
      const keys = ["iou", "chamfer_median", "chamfer_p95"] as const;
      const children = keys.map((k) =>
        dot(typeof v[k] === "string" ? (v[k] as string) : undefined),
      );
      if ("form_locked" in v)
        children.push(
          h(
            "span",
            { class: "text-ink-soft ml-1 text-[10px] tracking-wider uppercase" },
            v.form_locked === true ? "FL✓" : "FL✗",
          ),
        );
      return h("span", { class: "flex items-center gap-1" }, children);
    };
  },
});

useSeoMeta({
  title: "重建進度 · img2three",
  description: "Balamb Garden 中央建築逐 assembly / component 進度追蹤。",
});
</script>
