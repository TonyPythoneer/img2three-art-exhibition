<template>
  <section class="demo-parts">
    <div class="parts-head">
      <span class="parts-title">Parts</span>
      <span class="parts-count">{{ parts.length }}</span>
    </div>

    <div v-if="selected" class="part-card">
      <div class="part-card-head">
        <strong>{{ selected.name }}</strong>
        <span class="part-kind" :class="`part-kind-${selected.kind}`">{{ selected.kind }}</span>
      </div>
      <dl class="part-facts">
        <div v-if="selected.module">
          <dt>module</dt>
          <dd>{{ selected.module }}</dd>
        </div>
        <div>
          <dt>triangles</dt>
          <dd>{{ selected.triangles.toLocaleString() }}</dd>
        </div>
        <div v-for="m in selected.materials" :key="m">
          <dt>material</dt>
          <dd>{{ m }}</dd>
        </div>
      </dl>
      <div class="part-actions">
        <button
          class="btn part-btn"
          type="button"
          :aria-pressed="isolated"
          @click="emit('isolate', !isolated)"
        >
          {{ isolated ? "Show all" : "Isolate" }}
        </button>
        <button class="btn part-btn" type="button" @click="emit('clear')">Clear</button>
      </div>
    </div>

    <div class="parts-scroll">
      <ul class="parts-list">
        <template v-for="group in grouped" :key="group.module">
          <li v-if="grouped.length > 1" class="parts-group">
            <svg
              class="parts-group-icon"
              viewBox="0 0 24 24"
              width="12"
              height="12"
              aria-hidden="true"
            >
              <path
                d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              />
              <path
                d="m4.5 7.5 7.5 4.2 7.5-4.2M12 11.7V21"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              />
            </svg>
            {{ group.module }}
          </li>
          <li v-for="part in group.items" :key="part.name">
            <button
              class="part-item"
              type="button"
              :class="{ 'is-active': selected?.name === part.name }"
              @click="emit('select', part.name)"
            >
              <span class="part-name">{{ part.name }}</span>
            </button>
            <template v-if="visibleParts">
              <button
                class="icon-btn"
                type="button"
                :class="{ 'icon-btn-active': isolatedPart === part.name }"
                :aria-label="`Isolate ${part.name}`"
                @click.stop="emit('isolatePart', part.name)"
              >
                <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                  <circle
                    cx="8"
                    cy="8"
                    r="6"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.2"
                  />
                  <circle cx="8" cy="8" r="1.6" fill="currentColor" />
                </svg>
              </button>
              <button
                class="icon-btn"
                type="button"
                :class="{ 'icon-btn-off': !visibleParts.has(part.name) }"
                :aria-label="`${visibleParts.has(part.name) ? 'Hide' : 'Show'} ${part.name}`"
                @click.stop="emit('toggleVisible', part.name)"
              >
                <svg
                  v-if="visibleParts.has(part.name)"
                  viewBox="0 0 16 16"
                  width="14"
                  height="14"
                  aria-hidden="true"
                >
                  <path
                    d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.2"
                  />
                  <circle cx="8" cy="8" r="2" fill="currentColor" />
                </svg>
                <svg v-else viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                  <path
                    d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.2"
                  />
                  <circle cx="8" cy="8" r="2" fill="currentColor" />
                  <line x1="2" y1="14" x2="14" y2="2" stroke="currentColor" stroke-width="1.2" />
                </svg>
              </button>
            </template>
          </li>
        </template>
      </ul>
    </div>

    <!-- Model-level, not per-part: the honest caption for every number above it. -->
    <p v-if="provenance" class="parts-prov">{{ provenance }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PartInfo } from "~/exhibits/partInspector";

// Styles: src/styles/showcase/stage-parts.css
// Behaviour (picking, highlight, isolate, explode): src/exhibits/partInspector.ts

const props = defineProps<{
  parts: PartInfo[];
  selected: PartInfo | null;
  isolated: boolean;
  isolatedPart?: string | null;
  visibleParts?: Set<string>;
  provenance?: string;
}>();

const emit = defineEmits<{
  select: [name: string];
  isolate: [on: boolean];
  isolatePart: [name: string];
  toggleVisible: [name: string];
  clear: [];
}>();

const grouped = computed(() => {
  const groups = new Map<string, PartInfo[]>();
  for (const p of props.parts) {
    const key = p.module ?? "—";
    const list = groups.get(key);
    if (list) list.push(p);
    else groups.set(key, [p]);
  }
  return [...groups].map(([module, items]) => ({ module, items }));
});
</script>

<style scoped>
.part-item {
  display: inline-flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--ff7-text-white, #e8ecf4);
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.1s ease;
}

.icon-btn:hover {
  opacity: 1;
}

.icon-btn-active {
  opacity: 1;
  color: #5cd6b0;
}

.icon-btn-off {
  opacity: 0.4;
}

.icon-btn-off:hover {
  opacity: 0.7;
}

.icon-btn svg {
  display: block;
}
</style>
