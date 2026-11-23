/* Official NY Senate geometry, rendered as a real extruded Three.js atlas.
 * Inputs retain every positive-area polygon and its holes; no schematic map.
 * colorFor(id, district) returns a CSS color. Callbacks receive (id, pointerEvent).
 */
import * as THREE from './vendor/three.module.min.js';

const UNIT = 0.01;
const DEPTH = 0.17;
const GOLD = 0xd9bb76;
const DEFAULT_TILT = 0.43;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const world = ([x, y], z = 0) => new THREE.Vector3((x - 500) * UNIT, (390 - y) * UNIT, z);

function ringPath(ring, Constructor) {
  const path = new Constructor();
  ring.forEach((point, i) => {
    const x = (point[0] - 500) * UNIT;
    const y = (390 - point[1]) * UNIT;
    if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('Invalid atlas polygon coordinate.');
    if (i) path.lineTo(x, y); else path.moveTo(x, y);
  });
  path.closePath();
  return path;
}

function studioEnvironment(renderer) {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  const sky = ctx.createLinearGradient(0, 0, 0, 512);
  [[0, '#a9b3ba'], [.22, '#dbe0e3'], [.43, '#78858e'], [.52, '#171c22'], [.7, '#101316'], [1, '#050609']]
    .forEach(([stop, color]) => sky.addColorStop(stop, color));
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, 1024, 512);
  [[180, 120, 'rgba(245,246,240,.85)'], [665, 75, 'rgba(224,199,139,.46)'], [890, 100, 'rgba(200,218,234,.7)']]
    .forEach(([x, spread, color]) => {
      const strip = ctx.createLinearGradient(x - spread, 0, x + spread, 0);
      strip.addColorStop(0, 'rgba(255,255,255,0)');
      strip.addColorStop(.5, color);
      strip.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = strip;
      ctx.fillRect(x - spread, 0, spread * 2, 310);
    });
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.mapping = THREE.EquirectangularReflectionMapping;
  const generator = new THREE.PMREMGenerator(renderer);
  const target = generator.fromEquirectangular(texture);
  generator.dispose();
  texture.dispose();
  return target;
}

export function createAtlas3D(container, geometry, options = {}) {
  if (!container || !geometry?.districts?.length) throw new Error('Atlas container or district geometry is unavailable.');
  if (!geometry.districts.every(d => Array.isArray(d.polygons) && d.polygons.length)) {
    throw new Error('Official district polygons are required for the 3D atlas.');
  }

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  } catch (cause) {
    throw new Error('WebGL is unavailable; use the official SVG atlas.', { cause });
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.65));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.18;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const canvas = renderer.domElement;
  Object.assign(canvas.style, { display: 'block', width: '100%', height: '100%', touchAction: 'none', cursor: 'grab' });
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'Interactive official New York Senate map. Click a district to open its dossier. Drag to pan; shift-drag or right-drag to rotate; scroll to zoom. Arrow keys pan, plus and minus zoom, Home resets.');
  canvas.dataset.renderer = 'threejs';
  container.appendChild(canvas);

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-6, 6, 4.5, -4.5, .1, 80);
  const districts = new THREE.Group();
  scene.add(districts);
  const environment = studioEnvironment(renderer);
  if (environment) scene.environment = environment.texture;

  scene.add(new THREE.HemisphereLight(0xdce5ed, 0x22201b, 1.6));
  const key = new THREE.DirectionalLight(0xfff2d6, 3.4);
  key.position.set(-3.8, 5.7, 9);
  key.castShadow = true;
  key.shadow.mapSize.set(1536, 1536);
  Object.assign(key.shadow.camera, { left: -7, right: 7, top: 6, bottom: -6, near: .1, far: 28 });
  key.shadow.bias = -.0002;
  key.shadow.normalBias = .015;
  key.shadow.radius = 3;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xc1d0df, 1.65);
  fill.position.set(5, -3, 6);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xdcc28b, 1.25);
  rim.position.set(1.2, 6, 2.4);
  scene.add(rim);

  const groundGeometry = new THREE.PlaneGeometry(28, 22);
  const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x090c0f, roughness: .92, metalness: .12, transparent: true, opacity: .66 });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.position.z = -.045;
  ground.receiveShadow = true;
  scene.add(ground);

  let selected = Number(options.selected) || null;
  let hoverId = null;
  let colorFor = options.colorFor;
  let disposed = false;
  let contextLost = false;
  let dirty = true;
  let width = 1;
  let height = 1;
  let halfHeight = 4.4;
  let frame = 0;
  let lastFrame = 0;
  let currentMode = '3d';
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const state = { x: 0, y: -.02, zoom: 1, azimuth: 0, tilt: DEFAULT_TILT };
  const target = { ...state };
  const entries = new Map();
  const meshList = [];
  const allBounds = geometry.state?.bounds || [26, 28, 948, 724];
  const temporaryVector = new THREE.Vector3();
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const listenerRemovers = [];
  const listen = (node, event, fn, settings) => {
    node.addEventListener(event, fn, settings);
    listenerRemovers.push(() => node.removeEventListener(event, fn, settings));
  };
  const motionEnabled = () => options.motion !== false && !reduced?.matches && !document.body.classList.contains('motion-off');

  function baseColor(id, district) {
    const value = typeof colorFor === 'function' ? colorFor(id, district) : null;
    try {
      if (value !== null && value !== undefined && value !== '') return new THREE.Color(value);
    } catch (_) { /* A bad color cannot make the official geography disappear. */ }
    return new THREE.Color(id % 4 === 0 ? 0x999fa2 : id % 3 === 0 ? 0xb5b8b6 : 0xa6adae);
  }

  try {
    for (const district of geometry.districts) {
      const id = Number(district.id);
      const shapes = district.polygons.map(polygon => {
        if (!Array.isArray(polygon.outer) || polygon.outer.length < 3) throw new Error(`District ${id} has an incomplete polygon.`);
        const shape = ringPath(polygon.outer, THREE.Shape);
        for (const hole of polygon.holes || []) if (hole.length >= 3) shape.holes.push(ringPath(hole, THREE.Path));
        return shape;
      });
      const bodyGeometry = new THREE.ExtrudeGeometry(shapes, { depth: DEPTH, steps: 1, bevelEnabled: false, curveSegments: 1 });
      bodyGeometry.computeBoundingSphere();
      const top = new THREE.MeshStandardMaterial({ color: baseColor(id, district), metalness: .72, roughness: .34, envMapIntensity: .9 });
      const side = new THREE.MeshStandardMaterial({ color: 0x33383c, metalness: .68, roughness: .4, envMapIntensity: .65 });
      const body = new THREE.Mesh(bodyGeometry, [top, side]);
      body.userData.districtId = id;
      body.castShadow = true;
      body.receiveShadow = true;
      const group = new THREE.Group();
      group.add(body);
      const lineVertices = [];
      for (const polygon of district.polygons) {
        for (const ring of [polygon.outer, ...(polygon.holes || [])]) {
          for (let i = 0; i < ring.length - 1; i++) {
            for (const point of [ring[i], ring[i + 1]]) lineVertices.push((point[0] - 500) * UNIT, (390 - point[1]) * UNIT, DEPTH + .004);
          }
          // Input rings are normally closed, but preserve the final side if not.
          const first = ring[0], last = ring[ring.length - 1];
          if (first && last && (first[0] !== last[0] || first[1] !== last[1])) {
            for (const point of [last, first]) lineVertices.push((point[0] - 500) * UNIT, (390 - point[1]) * UNIT, DEPTH + .004);
          }
        }
      }
      const lineGeometry = new THREE.BufferGeometry();
      lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(lineVertices, 3));
      const lineMaterial = new THREE.LineBasicMaterial({ color: 0x697378, transparent: true, opacity: .76, depthWrite: false });
      const outline = new THREE.LineSegments(lineGeometry, lineMaterial);
      group.add(outline);
      districts.add(group);
      const entry = { id, district, group, body, top, side, outline, lineMaterial, raised: 1, targetRaised: 1 };
      entries.set(id, entry);
      meshList.push(body);
    }
  } catch (error) {
    districts.traverse(object => {
      object.geometry?.dispose();
      (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material?.dispose());
    });
    environment?.dispose();
    groundGeometry.dispose();
    groundMaterial.dispose();
    renderer.dispose();
    canvas.remove();
    throw error;
  }

  const labelHost = options.labelsContainer || null;
  let labelLayer = null;
  const labelEntries = [];
  if (labelHost) {
    labelLayer = document.createElement('div');
    labelLayer.className = 'atlas3d-label-layer';
    Object.assign(labelLayer.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
    labelHost.appendChild(labelLayer);
    for (const entry of entries.values()) {
      const element = document.createElement('button');
      element.type = 'button';
      element.className = 'map-label district-label';
      element.textContent = String(entry.id);
      element.setAttribute('aria-label', `Open Senate District ${entry.id} dossier`);
      element.style.pointerEvents = 'auto';
      listen(element, 'click', event => {
        event.stopPropagation();
        select(entry.id);
        options.onSelect?.(entry.id, event);
      });
      labelLayer.appendChild(element);
      labelEntries.push({ element, entry, point: world(entry.district.centroid, DEPTH + .06), type: 'district' });
    }
    for (const place of geometry.places || []) {
      const element = document.createElement('span');
      element.className = 'map-label place-label';
      element.textContent = place.name;
      Object.assign(element.style, { fontSize: '9px', letterSpacing: '.07em', color: '#adb4b7', pointerEvents: 'none', whiteSpace: 'nowrap' });
      labelLayer.appendChild(element);
      labelEntries.push({ element, point: world(place.position, DEPTH + .06), type: 'place', name: place.name });
    }
  }

  function updateAppearance() {
    for (const entry of entries.values()) {
      const active = entry.id === selected;
      const hovered = entry.id === hoverId;
      entry.top.color.copy(active ? new THREE.Color(GOLD) : baseColor(entry.id, entry.district));
      entry.top.emissive.set(active ? 0x80601b : hovered ? 0x263138 : 0x000000);
      entry.top.emissiveIntensity = active ? .12 : hovered ? .16 : 0;
      entry.top.roughness = active ? .29 : .34;
      entry.side.color.set(active ? 0x9c7a3e : 0x33383c);
      entry.lineMaterial.color.set(active ? 0xffe7ad : hovered ? 0xdbe9ef : 0x697378);
      entry.lineMaterial.opacity = active || hovered ? 1 : .76;
      entry.targetRaised = active ? 1.5 : hovered ? 1.12 : 1;
    }
    dirty = true;
  }

  function viewFit(bounds, azimuth = state.azimuth, tilt = state.tilt) {
    const [x, y, w, h] = bounds;
    const c = Math.abs(Math.cos(azimuth)), s = Math.abs(Math.sin(azimuth));
    const projectedWidth = (w * c + h * s) * UNIT;
    const projectedHeight = (h * c + w * s) * UNIT * Math.cos(tilt) + DEPTH * Math.sin(tilt);
    return Math.max(projectedHeight, projectedWidth / (width / height)) * .5 * 1.14;
  }

  function positionCamera() {
    halfHeight = viewFit(allBounds, 0, DEFAULT_TILT);
    camera.left = -halfHeight * width / height;
    camera.right = halfHeight * width / height;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.zoom = state.zoom;
    camera.updateProjectionMatrix();
    const distance = 19;
    camera.position.set(
      state.x + Math.sin(state.azimuth) * Math.sin(state.tilt) * distance,
      state.y - Math.cos(state.azimuth) * Math.sin(state.tilt) * distance,
      Math.cos(state.tilt) * distance,
    );
    camera.up.set(0, 1, 0);
    camera.lookAt(state.x, state.y, .06);
    camera.updateMatrixWorld();
  }

  function updateLabels() {
    if (!labelLayer) return;
    const occupied = [];
    const sorted = [...labelEntries].sort((a, b) => {
      const rank = item => item.entry?.id === selected ? 1000000 : item.type === 'place' ? 100000 : item.entry.district.areaKm2;
      return rank(b) - rank(a);
    });
    for (const label of sorted) {
      const { element, entry } = label;
      const active = entry?.id === selected;
      const minArea = state.zoom >= 4 ? 0 : state.zoom > 1.7 ? 140 : 850;
      if (entry && !active && entry.district.areaKm2 < minArea) {
        element.style.display = 'none';
        continue;
      }
      if (entry) {
        label.point.z = DEPTH * entry.raised + .06;
        element.classList.toggle('selected', active);
        element.textContent = active ? `SD ${entry.id}` : String(entry.id);
      }
      temporaryVector.copy(label.point).project(camera);
      const x = (temporaryVector.x * .5 + .5) * width;
      const y = (-temporaryVector.y * .5 + .5) * height;
      if (x < 14 || x > width - 14 || y < 18 || y > height - 12 || temporaryVector.z < -1 || temporaryVector.z > 1) {
        element.style.display = 'none';
        continue;
      }
      const bw = active ? 45 : label.type === 'place' ? Math.max(40, label.name.length * 5.5) : 24;
      const bh = active ? 24 : 17;
      const box = { left: x - bw / 2 - 3, right: x + bw / 2 + 3, top: y - bh / 2 - 2, bottom: y + bh / 2 + 2 };
      if (!active && occupied.some(other => box.left < other.right && box.right > other.left && box.top < other.bottom && box.bottom > other.top)) {
        element.style.display = 'none';
        continue;
      }
      occupied.push(box);
      element.style.display = '';
      element.style.left = `${x.toFixed(1)}px`;
      element.style.top = `${y.toFixed(1)}px`;
    }
  }

  function resize() {
    if (disposed) return;
    const rect = container.getBoundingClientRect();
    width = Math.max(1, rect.width);
    height = Math.max(1, rect.height);
    renderer.setSize(width, height, false);
    positionCamera();
    dirty = true;
  }

  function raycast(event) {
    const rect = canvas.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    return raycaster.intersectObjects(meshList, false)[0]?.object.userData.districtId || null;
  }

  function pan(dx, dy) {
    camera.updateMatrixWorld();
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    const units = 2 * halfHeight / height / target.zoom;
    target.x += (-right.x * dx + up.x * dy) * units;
    target.y += (-right.y * dx + up.y * dy) * units / Math.max(.5, Math.cos(target.tilt));
    dirty = true;
  }

  let drag = null;
  listen(canvas, 'pointerdown', event => {
    if (event.button !== 0 && event.button !== 2) return;
    canvas.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY, moved: false,
      rotate: event.button === 2 || event.shiftKey || event.altKey };
    canvas.style.cursor = 'grabbing';
  });
  listen(canvas, 'pointermove', event => {
    if (drag && drag.id === event.pointerId) {
      const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
      if (Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 4) drag.moved = true;
      if (drag.moved) {
        if (drag.rotate) {
          target.azimuth = clamp(target.azimuth + dx * .005, -.75, .75);
          target.tilt = clamp(target.tilt + dy * .004, .02, .88);
          dirty = true;
        } else pan(dx, dy);
      }
      drag.x = event.clientX;
      drag.y = event.clientY;
      return;
    }
    const id = raycast(event);
    if (hoverId !== id) { hoverId = id; updateAppearance(); }
    canvas.style.cursor = id ? 'pointer' : 'grab';
    options.onHover?.(id, event);
  });
  listen(canvas, 'pointerup', event => {
    if (!drag || drag.id !== event.pointerId) return;
    const clicked = !drag.moved && event.button === 0;
    drag = null;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    canvas.style.cursor = 'grab';
    if (clicked) {
      const id = raycast(event);
      if (id) { select(id); options.onSelect?.(id, event); }
    }
  });
  const cancelDrag = () => { drag = null; canvas.style.cursor = 'grab'; };
  listen(canvas, 'pointercancel', cancelDrag);
  listen(canvas, 'lostpointercapture', cancelDrag);
  listen(canvas, 'pointerleave', event => {
    if (!drag) { hoverId = null; updateAppearance(); options.onHover?.(null, event); }
  });
  listen(canvas, 'contextmenu', event => event.preventDefault());
  listen(canvas, 'wheel', event => {
    event.preventDefault();
    zoom(Math.exp(-clamp(event.deltaY, -400, 400) * .0015));
  }, { passive: false });
  listen(canvas, 'keydown', event => {
    const key = event.key;
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', '_', 'Home', '0'].includes(key)) event.preventDefault();
    if (key === 'ArrowLeft') pan(40, 0);
    if (key === 'ArrowRight') pan(-40, 0);
    if (key === 'ArrowUp') pan(0, 40);
    if (key === 'ArrowDown') pan(0, -40);
    if (key === '+' || key === '=') zoom(1.25);
    if (key === '-' || key === '_') zoom(.8);
    if (key === 'Home' || key === '0') reset();
  });
  listen(canvas, 'webglcontextlost', event => {
    event.preventDefault();
    contextLost = true;
    canvas.style.visibility = 'hidden';
    if (labelLayer) labelLayer.style.display = 'none';
    container.dataset.atlas3d = 'context-lost';
    container.dispatchEvent(new CustomEvent('atlas3dunavailable', { bubbles: true }));
  });
  listen(canvas, 'webglcontextrestored', () => {
    contextLost = false;
    canvas.style.visibility = '';
    if (labelLayer) labelLayer.style.display = '';
    container.dataset.atlas3d = 'ready';
    dirty = true;
  });

  const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
  observer?.observe(container);
  if (!observer) listen(window, 'resize', resize);

  function select(id) {
    const n = Number(id);
    selected = entries.has(n) ? n : null;
    updateAppearance();
  }
  function setColors(fn) {
    colorFor = fn;
    updateAppearance();
  }
  function setMode(mode) {
    currentMode = String(mode).toLowerCase();
    target.tilt = ['flat', '2d', 'top'].includes(currentMode) ? .001 : DEFAULT_TILT;
    if (target.tilt < .01) target.azimuth = 0;
    dirty = true;
  }
  function zoom(factor) {
    if (!Number.isFinite(Number(factor)) || Number(factor) <= 0) return;
    target.zoom = clamp(target.zoom * Number(factor), .72, 22);
    dirty = true;
  }
  function reset() {
    Object.assign(target, { x: 0, y: -.02, zoom: 1, azimuth: 0, tilt: ['flat', '2d', 'top'].includes(currentMode) ? .001 : DEFAULT_TILT });
    dirty = true;
  }
  function rotate() {
    target.azimuth = target.azimuth >= .45 ? -.3 : target.azimuth + .2;
    target.tilt = DEFAULT_TILT;
    dirty = true;
  }
  function focus(input) {
    const bounds = Array.isArray(input) ? input : input?.bounds || input?.viewBox;
    if (!bounds || bounds.length !== 4 || !bounds.every(Number.isFinite) || bounds[2] <= 0 || bounds[3] <= 0) return;
    const [x, y, w, h] = bounds;
    target.x = (x + w / 2 - 500) * UNIT;
    target.y = (390 - y - h / 2) * UNIT;
    target.zoom = clamp(viewFit(allBounds, 0, DEFAULT_TILT) / viewFit(bounds, target.azimuth, target.tilt), .72, 22);
    dirty = true;
  }

  function tick(time) {
    if (disposed) return;
    frame = requestAnimationFrame(tick);
    if (contextLost || document.hidden || time - lastFrame < 24) return;
    const dt = Math.min(50, time - (lastFrame || time));
    lastFrame = time;
    const moving = motionEnabled();
    const lerp = moving ? 1 - Math.exp(-dt / 90) : 1;
    let changing = false;
    for (const property of Object.keys(state)) {
      const difference = target[property] - state[property];
      if (Math.abs(difference) > .0001) { state[property] += difference * lerp; changing = true; }
      else state[property] = target[property];
    }
    for (const entry of entries.values()) {
      const diff = entry.targetRaised - entry.raised;
      if (Math.abs(diff) > .001) { entry.raised += diff * lerp; changing = true; }
      else entry.raised = entry.targetRaised;
      entry.group.scale.z = entry.raised;
    }
    if (moving) {
      // Restrained studio reflections; the official map itself does not drift.
      fill.intensity = 1.6 + Math.sin(time * .00038) * .11;
      key.position.x = -3.8 + Math.sin(time * .00017) * .3;
    }
    if (dirty || changing || moving) {
      positionCamera();
      scene.updateMatrixWorld(true);
      renderer.render(scene, camera);
      updateLabels();
      dirty = false;
    }
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    cancelAnimationFrame(frame);
    observer?.disconnect();
    listenerRemovers.splice(0).forEach(remove => remove());
    labelLayer?.remove();
    districts.traverse(object => {
      object.geometry?.dispose();
      (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material?.dispose());
    });
    groundGeometry.dispose();
    groundMaterial.dispose();
    key.shadow.map?.dispose();
    environment?.dispose();
    renderer.dispose();
    canvas.remove();
    delete container.dataset.atlas3d;
  }

  updateAppearance();
  resize();
  positionCamera();
  scene.updateMatrixWorld(true);
  renderer.render(scene, camera);
  updateLabels();
  container.dataset.atlas3d = 'ready';
  frame = requestAnimationFrame(tick);
  return { select, setColors, setMode, zoom, reset, rotate, focus, dispose };
}
