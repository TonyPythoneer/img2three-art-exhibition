<template>
  <div class="yt-audio-bar" :data-expanded="expanded">
    <button type="button" class="yt-audio-play" @click="toggle">
      <svg v-if="!playing" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M8 5v14l11-7z" />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M6 5h4v14H6zM14 5h4v14h-4z" />
      </svg>
    </button>

    <span class="yt-audio-time">{{ formatTime(currentTime) }}</span>

    <div class="yt-audio-track" @click="seek">
      <div class="yt-audio-track-bg"></div>
      <div class="yt-audio-track-fill" :style="{ width: `${progress * 100}%` }"></div>
    </div>

    <span class="yt-audio-time">{{ formatTime(duration) }}</span>

    <button
      type="button"
      class="yt-audio-loop"
      :class="{ 'is-active': looping }"
      :aria-pressed="looping"
      title="Loop"
      @click="toggleLoop"
    >
      <svg
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M17 1l4 4-4 4" />
        <path d="M3 11V9a4 4 0 0 1 4-4h14" />
        <path d="M7 23l-4-4 4-4" />
        <path d="M21 13v2a4 4 0 0 1-4 4H3" />
      </svg>
    </button>

    <button type="button" class="yt-audio-volume" @click="toggleMute">
      <svg v-if="!muted" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path
          d="M3 10v4h4l5 5V5L7 10H3zm13.5 2A4.5 4.5 0 0 0 14 7.97v8.05A4.5 4.5 0 0 0 16.5 12z"
        />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M3 10v4h4l5 5V5l-5 5H3z" />
      </svg>
    </button>

    <button
      type="button"
      class="yt-audio-info-toggle"
      :class="{ 'is-active': expanded }"
      :aria-pressed="expanded"
      @click="expanded = !expanded"
      :title="expanded ? 'Collapse info' : 'Song info'"
    >
      <svg v-if="!expanded" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" />
        <line
          x1="12"
          y1="11"
          x2="12"
          y2="17"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        />
        <circle cx="12" cy="8" r="1" fill="currentColor" />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <line x1="6" y1="6" x2="18" y2="18" stroke-linecap="round" />
        <line x1="18" y1="6" x2="6" y2="18" stroke-linecap="round" />
      </svg>
    </button>

    <div v-if="expanded && audioTitle" class="yt-audio-info">
      <a
        :href="`https://www.youtube.com/watch?v=${videoId}`"
        target="_blank"
        rel="noopener noreferrer"
        class="yt-audio-info-link"
        title="Watch on YouTube"
      >
        <svg class="yt-logo" viewBox="0 0 21 20" width="28" height="20">
          <path
            d="M3 6.5C3 4.6 4.6 3 6.5 3h11C19.4 3 21 4.6 21 6.5v7c0 1.9-1.6 3.5-3.5 3.5h-11C4.6 17 3 15.4 3 13.5v-7z"
            fill="#FF0000"
          />
          <polygon points="9,7 9,13 14,10" fill="#fff" />
        </svg>
      </a>
      <div class="yt-audio-marquee">
        <span class="yt-audio-marquee-text">{{ audioTitle }}</span>
      </div>
    </div>

    <div ref="mount" class="yt-audio-player"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps<{ videoId: string; audioTitle?: string }>();

// YouTube's API terms require the player to stay visible — this widget keeps a real,
// tiny player on screen instead of hiding it, and drives all controls through custom UI.
declare global {
  interface Window {
    YT?: {
      Player: new (el: HTMLElement, opts: unknown) => YtPlayer;
      PlayerState: { PLAYING: number };
    };
    onYouTubeIframeAPIReady?: () => void;
  }
}
type YtPlayer = {
  playVideo(): void;
  pauseVideo(): void;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  mute(): void;
  unMute(): void;
  setLoop(loop: boolean): void;
  getCurrentTime(): number;
  getDuration(): number;
  destroy(): void;
};

const mount = ref<HTMLDivElement | null>(null);
const playing = ref(false);
const muted = ref(false);
const looping = ref(true);
const expanded = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const progress = ref(0);
let player: YtPlayer | null = null;
let pollTimer = 0;

const formatTime = (s: number) => {
  const total = Math.max(0, Math.floor(s));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
};

const loadApi = () =>
  new Promise<void>((resolve) => {
    if (window.YT?.Player) return resolve();
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      prev?.();
      resolve();
    };
    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    }
  });

onMounted(async () => {
  await loadApi();
  if (!mount.value || !window.YT) return;
  player = new window.YT.Player(mount.value, {
    videoId: props.videoId,
    width: "1",
    height: "1",
    playerVars: {
      controls: 0,
      disablekb: 1,
      modestbranding: 1,
      rel: 0,
      loop: 1,
      playlist: props.videoId,
    },
    events: {
      // The poll starts HERE, not after the constructor. `new YT.Player()` returns an object
      // immediately but does not attach its methods until the iframe has loaded and this fires,
      // so a timer started any earlier threw `getCurrentTime is not a function` on every tick in
      // between — several times on every exhibit page load.
      onReady: () => {
        duration.value = player?.getDuration() ?? 0;
        pollTimer = window.setInterval(() => {
          if (!player) return;
          currentTime.value = player.getCurrentTime();
          duration.value = player.getDuration() || duration.value;
          progress.value = duration.value ? currentTime.value / duration.value : 0;
        }, 250);
      },
      onStateChange: (e: { data: number }) => {
        playing.value = e.data === window.YT?.PlayerState.PLAYING;
      },
    },
  });
});

onBeforeUnmount(() => {
  window.clearInterval(pollTimer);
  player?.destroy();
});

const toggle = () => (playing.value ? player?.pauseVideo() : player?.playVideo());

const toggleMute = () => {
  muted.value = !muted.value;
  muted.value ? player?.mute() : player?.unMute();
};

const toggleLoop = () => {
  looping.value = !looping.value;
  player?.setLoop(looping.value);
};

const seek = (e: MouseEvent) => {
  if (!player || !duration.value) return;
  const track = e.currentTarget as HTMLElement;
  const ratio = (e.clientX - track.getBoundingClientRect().left) / track.clientWidth;
  player.seekTo(ratio * duration.value, true);
};
</script>

<style scoped>
.yt-audio-bar {
  position: fixed;
  right: 16px;
  bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgb(35, 40, 56);
  background: rgba(20, 22, 30, 0.92);
  backdrop-filter: blur(6px);
  color: rgb(238, 240, 246);
  z-index: 100;
}

.yt-audio-play,
.yt-audio-volume {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
}

.yt-audio-play {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgb(238, 240, 246);
  color: rgb(20, 22, 30);
}

.yt-audio-time {
  font:
    11px SFMono-Regular,
    ui-monospace,
    Menlo,
    Consolas,
    monospace;
  color: rgb(160, 166, 184);
  min-width: 28px;
  text-align: center;
}

.yt-audio-track {
  position: relative;
  width: 140px;
  height: 14px;
  display: flex;
  align-items: center;
}

.yt-audio-track-bg {
  position: absolute;
  inset: 0;
  margin: auto 0;
  height: 4px;
  border-radius: 999px;
  background: rgb(60, 66, 88);
}

.yt-audio-track-fill {
  position: absolute;
  left: 0;
  margin: auto 0;
  top: 0;
  bottom: 0;
  height: 4px;
  border-radius: 999px;
  background: var(--accent-strong, #6ea8fe);
}

.yt-audio-loop {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgb(120, 126, 148);
  padding: 0;
  transition: color 0.15s;
}

.yt-audio-loop.is-active {
  color: var(--accent-strong, #6ea8fe);
}

.yt-audio-info-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgb(120, 126, 148);
  padding: 0;
  transition: color 0.15s;
}

.yt-audio-info-toggle:hover {
  color: rgb(238, 240, 246);
}

.yt-audio-info-toggle.is-active {
  color: var(--accent-strong, #6ea8fe);
}

/* Opens upward: the bar is pinned to the bottom of the viewport, so a panel below it
   would hang off the screen. */
.yt-audio-info {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgb(35, 40, 56);
  background: rgba(20, 22, 30, 0.95);
  backdrop-filter: blur(6px);
}

.yt-audio-info-link {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.yt-logo {
  display: block;
}

.yt-audio-marquee {
  overflow: hidden;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.yt-audio-marquee-text {
  display: inline-block;
  font-size: 12px;
  color: rgb(238, 240, 246);
  padding-left: 100%;
  animation: yt-marquee 12s linear infinite;
}

.yt-audio-marquee-text:hover {
  animation-play-state: paused;
}

@keyframes yt-marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-100%);
  }
}

.yt-audio-player {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
}
</style>
