import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { createUltimaWeaponV2Model } from "~/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model";

/**
 * Cinematic hero turntable, ported from img2threejs-showcase's hero-stage.ts.
 *
 * The upstream version reads an authored camera pose off each demo's registry
 * entry. Nothing here has one, so the stage frames every model from its own
 * bounding sphere instead — one less thing to keep in sync per exhibit.
 *
 * Client-only: imported dynamically so vite-ssg never evaluates WebGL in node.
 */

export type HeroEntry = {
  slug: string;
  title: string;
  /** Built fresh on entry and disposed on exit — the stage owns the instance. */
  build: () => THREE.Object3D;
};

const CYCLE_MS = 5200;
const MATERIALIZE_S = 1.05;

export class HeroStage {
  private readonly mount: HTMLElement;
  private readonly entries: HeroEntry[];
  private readonly onEntry: (entry: HeroEntry, index: number) => void;

  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly composer: EffectComposer;
  private readonly clock = new THREE.Clock();
  private readonly ro: ResizeObserver;
  private readonly reduceMotion: boolean;

  private readonly target = new THREE.Vector3();
  private orbitRadius = 3;
  private orbitAngle = 0;
  private orbitHeight = 1;
  private modelRadius = 1;
  private model: THREE.Object3D | null = null;

  private index = -1;
  private elapsed = 0;
  private entryStart = 0;
  private sinceSwap = 0;
  private raf = 0;
  private disposed = false;

  constructor(
    mount: HTMLElement,
    entries: HeroEntry[],
    onEntry: (entry: HeroEntry, index: number) => void,
  ) {
    this.mount = mount;
    this.entries = entries;
    this.onEntry = onEntry;
    this.reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    mount.appendChild(this.renderer.domElement);
    Object.assign(this.renderer.domElement.style, {
      display: "block",
      width: "100%",
      height: "100%",
    });

    this.scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();

    // The exhibits ship their own review rigs; the stage is not a review, so one
    // key light over the neutral room environment is the whole lighting budget.
    const key = new THREE.DirectionalLight(0xffffff, 1.6);
    key.position.set(3, 5, 4);
    this.scene.add(key, new THREE.AmbientLight(0xffffff, 0.35));

    this.camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100);
    this.scene.add(this.buildParticles());

    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.composer.addPass(new UnrealBloomPass(new THREE.Vector2(1, 1), 0.45, 0.5, 0.85));
    this.composer.addPass(new OutputPass());

    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(mount);
    this.resize();
  }

  private buildParticles(): THREE.Points {
    const count = 340;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 12;
      positions[i * 3 + 1] = Math.random() * 8 - 1.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 64;
    const ctx = canvas.getContext("2d")!;
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.4, "rgba(150,200,255,0.55)");
    g.addColorStop(1, "rgba(150,200,255,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 64, 64);
    const sprite = new THREE.CanvasTexture(canvas);
    sprite.colorSpace = THREE.SRGBColorSpace;

    const points = new THREE.Points(
      geo,
      new THREE.PointsMaterial({
        size: 0.09,
        map: sprite,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        opacity: 0.7,
      }),
    );
    points.name = "__particles";
    points.renderOrder = -1;
    return points;
  }

  private resize(): void {
    const w = this.mount.clientWidth || 1;
    const h = this.mount.clientHeight || 1;
    this.camera.aspect = w / Math.max(1, h);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.composer.setSize(w, h);
    this.frame();
  }

  /**
   * Fit the turntable orbit to the model's bounding sphere. The limiting half
   * angle is the vertical FOV on a tall stage and the horizontal one on a wide
   * stage, so a phone-shaped stage pulls back instead of cropping the subject.
   */
  private frame(): void {
    if (!this.model) return;
    const vertical = THREE.MathUtils.degToRad(this.camera.fov) / 2;
    const horizontal = Math.atan(Math.tan(vertical) * this.camera.aspect);
    const distance = (this.modelRadius / Math.sin(Math.min(vertical, horizontal))) * 1.15;
    this.orbitHeight = distance * 0.32;
    this.orbitRadius = Math.sqrt(Math.max(distance ** 2 - this.orbitHeight ** 2, 0.01));
    this.camera.near = Math.max(0.01, distance * 0.02);
    this.camera.far = distance + this.modelRadius * 6;
    this.camera.updateProjectionMatrix();
  }

  private clearActive(): void {
    if (!this.model) return;
    this.scene.remove(this.model);
    this.model.traverse((node) => {
      const mesh = node as THREE.Mesh;
      mesh.geometry?.dispose();
      const material = mesh.material as THREE.Material | THREE.Material[] | undefined;
      if (!material) return;
      for (const m of Array.isArray(material) ? material : [material]) m.dispose();
    });
    this.model = null;
  }

  private show(index: number, tried = 0): void {
    this.clearActive();
    const entry = this.entries[index]!;
    let model: THREE.Object3D;
    try {
      model = entry.build();
    } catch (error) {
      // A factory mid-rewrite must not take the whole landing page down with it.
      // `tried` stops the fallback from cycling forever when every factory throws.
      console.error(`hero stage: ${entry.slug} failed to build`, error);
      if (tried + 1 < this.entries.length) {
        this.show((index + 1) % this.entries.length, tried + 1);
      }
      return;
    }
    this.scene.add(model);
    this.model = model;

    const sphere = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());
    this.modelRadius = Math.max(sphere.radius, 1e-3);
    this.target.copy(sphere.center);
    this.frame();

    this.entryStart = this.elapsed;
    this.index = index;
    this.onEntry(entry, index);
  }

  start(): void {
    if (this.entries.length === 0) return;
    this.show(0);
    const loop = (): void => {
      if (this.disposed) return;
      this.raf = requestAnimationFrame(loop);
      const dt = Math.min(0.05, this.clock.getDelta());
      this.elapsed += dt;

      if (!this.reduceMotion) this.orbitAngle += dt * 0.32;
      this.camera.position.set(
        this.target.x + this.orbitRadius * Math.cos(this.orbitAngle),
        this.target.y + this.orbitHeight,
        this.target.z + this.orbitRadius * Math.sin(this.orbitAngle),
      );
      this.camera.lookAt(this.target);

      // Materialize on entry: scale up and settle.
      const t = Math.min(1, (this.elapsed - this.entryStart) / MATERIALIZE_S);
      const eased = 1 - (1 - t) ** 3;
      if (this.model) {
        this.model.scale.setScalar(0.82 + 0.18 * eased);
        this.model.position.y = (1 - eased) * this.modelRadius * 0.2;
      }

      const particles = this.scene.getObjectByName("__particles") as THREE.Points | null;
      if (particles && !this.reduceMotion) {
        const pos = particles.geometry.getAttribute("position") as THREE.BufferAttribute;
        for (let i = 0; i < pos.count; i++) {
          const y = pos.getY(i) + dt * 0.35;
          pos.setY(i, y > 6.5 ? -1.5 : y);
        }
        pos.needsUpdate = true;
        particles.rotation.y = this.elapsed * 0.02;
      }

      if (this.entries.length > 1) {
        this.sinceSwap += dt * 1000;
        if (this.sinceSwap >= CYCLE_MS) {
          this.sinceSwap = 0;
          this.show((this.index + 1) % this.entries.length);
        }
      }

      this.composer.render();
    };
    loop();
  }

  /** Jump straight to an exhibit — what hovering its gallery card does. */
  focus(index: number): void {
    if (index < 0 || index >= this.entries.length || index === this.index) return;
    this.sinceSwap = 0;
    this.show(index);
  }

  dispose(): void {
    this.disposed = true;
    cancelAnimationFrame(this.raf);
    this.ro.disconnect();
    this.clearActive();
    this.scene.traverse((node) => {
      const mesh = node as THREE.Mesh;
      mesh.geometry?.dispose();
      const material = mesh.material as THREE.Material | THREE.Material[] | undefined;
      if (material) for (const m of Array.isArray(material) ? material : [material]) m.dispose();
    });
    this.composer.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}

/**
 * The exhibits the turntable can build, in gallery order. Deliberately its own
 * list rather than a field on `exhibits`: that module is imported by
 * vite.config.ts to enumerate SSG routes, and must stay free of three.js.
 */
export function heroEntries(): HeroEntry[] {
  return [
    {
      slug: "ff7-cloud-ultima-weapon",
      title: "Ultima Weapon",
      build: () => createUltimaWeaponV2Model({ detail: "full" }),
    },
  ];
}
