/* CPU-rendered relief atlas for environments without WebGL.
 * Every cap and wall is projected from the official polygon coordinates.
 * Coordinates, islands and holes are preserved; walls are batched by shade.
 */
const NS = 'http://www.w3.org/2000/svg';
const DEFAULT_YAW = -8 * Math.PI / 180;
const DEFAULT_TILT = .82;
let serial = 0;
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
const svgNode = (name, attrs = {}) => {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
};
const num = n => Number(n.toFixed(2));

function rgb(input) {
  if (typeof input === 'number') return [(input >> 16) & 255, (input >> 8) & 255, input & 255];
  if (input?.getHexString) input = `#${input.getHexString()}`;
  const s = String(input || '#929b9f').trim();
  if (/^#[0-9a-f]{6}$/i.test(s)) return [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
  if (/^#[0-9a-f]{3}$/i.test(s)) return [1, 2, 3].map(i => parseInt(s[i] + s[i], 16));
  const values = s.match(/[\d.]+/g)?.map(Number);
  if (/^rgb/i.test(s) && values?.length >= 3) return values.slice(0, 3);
  if (/^hsl/i.test(s) && values?.length >= 3) {
    const h = ((values[0] % 360) + 360) % 360 / 60, sat = values[1] / 100, light = values[2] / 100;
    const c = (1 - Math.abs(2 * light - 1)) * sat, x = c * (1 - Math.abs(h % 2 - 1)), m = light - c / 2;
    const v = h < 1 ? [c, x, 0] : h < 2 ? [x, c, 0] : h < 3 ? [0, c, x] : h < 4 ? [0, x, c] : h < 5 ? [x, 0, c] : [c, 0, x];
    return v.map(n => (n + m) * 255);
  }
  return [146, 155, 159];
}
const mix = (color, amount) => `rgb(${color.map(n => Math.round(clamp(amount >= 0 ? n + (255 - n) * amount : n * (1 + amount), 0, 255))).join(',')})`;

export function createAtlasSVG(container, geometry, options = {}) {
  if (!container || !geometry?.districts?.length || !geometry.districts.every(d => d.polygons?.length)) {
    throw new Error('The projected SVG atlas requires official district polygons.');
  }
  const prefix = `ny-relief-${++serial}`;
  const svg = svgNode('svg', { width: '100%', height: '100%', role: 'group', 'aria-label': 'Official New York Senate districts, projected relief map' });
  svg.dataset.renderer = 'svg3d';
  Object.assign(svg.style, { display: 'block', width: '100%', height: '100%', touchAction: 'none', overflow: 'hidden', cursor: 'grab' });
  svg.tabIndex = 0;
  const title = svgNode('title');
  title.textContent = 'Official New York State Senate map. Click a district. Drag to pan; Shift-drag to rotate; scroll to zoom.';
  svg.appendChild(title);
  const defs = svgNode('defs');
  svg.appendChild(defs);
  const shadowFilter = svgNode('filter', { id: `${prefix}-shadow`, x: '-25%', y: '-25%', width: '155%', height: '170%', 'color-interpolation-filters': 'sRGB' });
  shadowFilter.appendChild(svgNode('feDropShadow', { dx: '7', dy: '17', stdDeviation: '12', 'flood-color': '#000', 'flood-opacity': '.8' }));
  defs.appendChild(shadowFilter);
  const viewport = svgNode('g');
  const shadow = svgNode('path', { fill: '#020405', opacity: '.82', 'fill-rule': 'evenodd', filter: `url(#${prefix}-shadow)`, 'pointer-events': 'none' });
  const wallsLayer = svgNode('g', { 'aria-hidden': 'true' });
  const capsLayer = svgNode('g');
  const selectedWallsLayer = svgNode('g', { 'aria-hidden': 'true' });
  const selectedCapLayer = svgNode('g');
  viewport.append(shadow, wallsLayer, capsLayer, selectedWallsLayer, selectedCapLayer);
  svg.appendChild(viewport);
  container.appendChild(svg);

  const labels = document.createElement('div');
  labels.className = 'atlas-svg-label-layer';
  Object.assign(labels.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
  (options.labelsContainer || container).appendChild(labels);
  const listenerRemovers = [];
  const listen = (node, name, callback, settings) => {
    node.addEventListener(name, callback, settings);
    listenerRemovers.push(() => node.removeEventListener(name, callback, settings));
  };
  const entries = new Map();
  const labelEntries = [];
  const points = [];
  let selected = Number(options.selected) || null;
  let hovered = null;
  let colorFor = options.colorFor;
  let disposed = false;
  let mode = '3d';
  let width = 1, height = 1, baseScale = 1, depth = 24;
  let frameBox = { x: 0, y: 0, width: 1, height: 1 };
  let raf = 0, lastShimmer = 0;
  let isHome = true;
  let dirty = true;
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const view = { x: 0, y: 0, zoom: 1, yaw: DEFAULT_YAW, tilt: DEFAULT_TILT };
  let cos = Math.cos(view.yaw), sin = Math.sin(view.yaw), heightFactor = Math.sqrt(1 - view.tilt ** 2);
  const motion = () => options.motion !== false && !reduced?.matches && !document.body.classList.contains('motion-off');

  function project(point, z = 0) {
    const x = point[0] - 500, y = 390 - point[1];
    return [cos * x - sin * y, -(sin * x + cos * y) * view.tilt - z * heightFactor];
  }
  function projectCenter() {
    return [cos * view.x - sin * view.y, -(sin * view.x + cos * view.y) * view.tilt];
  }
  function inverse(x, y) {
    const up = -y / view.tilt;
    return [cos * x + sin * up, -sin * x + cos * up];
  }
  function projectedBounds(inputPoints, z = 0) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const point of inputPoints) {
      const [x, y] = project(point, z);
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
    }
    return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };
  }

  for (const district of geometry.districts) {
    const id = Number(district.id);
    for (const polygon of district.polygons) {
      if (!polygon.outer || polygon.outer.length < 3) throw new Error(`District ${id} has an incomplete polygon.`);
      points.push(...polygon.outer);
    }
    const gradient = svgNode('linearGradient', { id: `${prefix}-cap-${id}`, gradientUnits: 'userSpaceOnUse', x1: '-500', y1: '-390', x2: '540', y2: '440' });
    const stops = [0, .21, .42, .49, .55, .66, 1].map(offset => {
      const stop = svgNode('stop', { offset: String(offset) }); gradient.appendChild(stop); return stop;
    });
    defs.appendChild(gradient);
    const walls = svgNode('g', { 'data-district-id': id });
    const wallPaths = Array.from({ length: 4 }, () => {
      const path = svgNode('path', { stroke: 'none', 'stroke-linejoin': 'round' }); walls.appendChild(path); return path;
    });
    const cap = svgNode('path', {
      class: 'cpu-atlas-district', 'data-district-id': id,
      fill: `url(#${prefix}-cap-${id})`, 'fill-rule': 'evenodd',
      stroke: '#9da7ac', 'stroke-width': '.55', 'stroke-linejoin': 'round',
      'vector-effect': 'non-scaling-stroke', tabindex: '0', role: 'button',
      'aria-label': `Open Senate District ${id} dossier`,
    });
    const capTitle = svgNode('title'); capTitle.textContent = `Senate District ${id}`; cap.appendChild(capTitle);
    const label = document.createElement('button');
    label.type = 'button'; label.className = 'map-label district-label'; label.textContent = String(id);
    label.setAttribute('aria-label', `Open Senate District ${id} dossier`);
    label.style.pointerEvents = 'auto';
    labels.appendChild(label);
    const entry = { id, district, gradient, stops, walls, wallPaths, cap, label, cache: null };
    entries.set(id, entry);
    labelEntries.push({ entry, element: label, position: district.centroid, type: 'district' });
    listen(label, 'click', event => { event.stopPropagation(); select(id); options.onSelect?.(id, event); });
    listen(label, 'pointerenter', event => options.onHover?.(id, event));
    listen(label, 'pointerleave', event => options.onHover?.(null, event));
    listen(cap, 'keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(id); options.onSelect?.(id, event); }
    });
    wallsLayer.appendChild(walls); capsLayer.appendChild(cap);
  }
  for (const place of geometry.places || []) {
    const element = document.createElement('span');
    element.className = 'map-label place-label'; element.textContent = place.name;
    Object.assign(element.style, { fontSize: '9px', color: '#b8c0c2', letterSpacing: '.06em', whiteSpace: 'nowrap', pointerEvents: 'none' });
    labels.appendChild(element);
    labelEntries.push({ element, position: place.position, type: 'place', name: place.name });
  }

  function ringD(ring, z) {
    return ring.map((point, i) => {
      const [x, y] = project(point, z);
      return `${i ? 'L' : 'M'}${num(x)},${num(y)}`;
    }).join('') + 'Z';
  }
  function buildPaths(entry, z) {
    let cap = '';
    const walls = [[], [], [], []];
    for (const polygon of entry.district.polygons) {
      for (const [index, ring] of [polygon.outer, ...(polygon.holes || [])].entries()) {
        cap += ringD(ring, z);
        const base = ring.map(point => project(point, 0));
        const top = ring.map(point => project(point, z));
        let area = 0;
        for (let i = 0; i < base.length; i++) {
          const next = base[(i + 1) % base.length]; area += base[i][0] * next[1] - next[0] * base[i][1];
        }
        const sign = (area >= 0 ? 1 : -1) * (index ? -1 : 1);
        for (let i = 0; i < base.length; i++) {
          const next = (i + 1) % base.length;
          const a = base[i], b = base[next], c = top[next], d = top[i];
          const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy);
          if (length < .00001) continue;
          const light = sign * (dy * -.75 + dx * .66) / length;
          const shade = clamp(Math.floor((light + 1) * 2), 0, 3);
          walls[shade].push(`M${num(a[0])},${num(a[1])}L${num(b[0])},${num(b[1])}L${num(c[0])},${num(c[1])}L${num(d[0])},${num(d[1])}Z`);
        }
      }
    }
    return { cap, walls: walls.map(parts => parts.join('')) };
  }

  function updateColors() {
    for (const entry of entries.values()) {
      const active = entry.id === selected;
      const base = active ? [215, 183, 109] : rgb(typeof colorFor === 'function' ? colorFor(entry.id, entry.district) : '#929b9f');
      [.36, .09, -.24, .30, .57, -.03, -.32].forEach((shade, i) => entry.stops[i].setAttribute('stop-color', mix(base, shade)));
      [-.77, -.65, -.51, -.36].forEach((shade, i) => entry.wallPaths[i].setAttribute('fill', mix(base, shade)));
      entry.cap.setAttribute('stroke', active ? '#ffe5a4' : hovered === entry.id ? '#ecf4f5' : '#77858c');
      entry.cap.setAttribute('stroke-width', active ? '1.2' : hovered === entry.id ? '1' : '.55');
      entry.cap.setAttribute('aria-pressed', String(active));
      entry.label.classList.toggle('selected', active);
      entry.label.textContent = active ? `SD ${entry.id}` : String(entry.id);
    }
    dirty = true;
  }
  function applySelection() {
    const ordered = [...entries.values()].sort((a, b) => project(a.district.centroid)[1] - project(b.district.centroid)[1]);
    for (const entry of ordered) {
      if (!entry.cache) continue;
      const active = entry.id === selected;
      const paths = active ? entry.cache.raised : entry.cache.base;
      entry.cap.setAttribute('d', paths.cap);
      entry.wallPaths.forEach((path, i) => path.setAttribute('d', paths.walls[i]));
      (active ? selectedWallsLayer : wallsLayer).appendChild(entry.walls);
      (active ? selectedCapLayer : capsLayer).appendChild(entry.cap);
    }
    updateColors();
    updateView();
  }

  function rebuildGeometry() {
    cos = Math.cos(view.yaw); sin = Math.sin(view.yaw);
    heightFactor = Math.sqrt(Math.max(0, 1 - view.tilt ** 2));
    const bounds = projectedBounds(points);
    baseScale = .92 * Math.min(frameBox.width / bounds.width, frameBox.height / bounds.height);
    // About nine screen pixels of base relief in the statewide view.
    depth = mode === 'flat' ? 0 : clamp(9 / Math.max(.08, baseScale * heightFactor), 14, 56);
    if (isHome) {
      const [x, y] = inverse((bounds.minX + bounds.maxX) / 2, (bounds.minY + bounds.maxY) / 2);
      view.x = x; view.y = y;
    }
    let shadowD = '';
    for (const entry of entries.values()) {
      entry.cache = { base: buildPaths(entry, depth), raised: buildPaths(entry, depth * 1.5) };
      for (const polygon of entry.district.polygons) for (const ring of [polygon.outer, ...(polygon.holes || [])]) shadowD += ringD(ring, 0);
    }
    shadow.setAttribute('d', shadowD);
    shadow.style.display = mode === 'flat' ? 'none' : '';
    applySelection();
  }

  function screenPoint(point, z = depth) {
    const [x, y] = project(point, z), [cx, cy] = projectCenter(), scale = baseScale * view.zoom;
    return [frameBox.x + frameBox.width / 2 + (x - cx) * scale, frameBox.y + frameBox.height / 2 + (y - cy) * scale];
  }
  function updateLabels() {
    const occupied = [];
    const rank = item => item.entry?.id === selected ? 1000000 : item.type === 'place' ? 100000 : item.entry.district.areaKm2;
    const ordered = [...labelEntries].sort((a, b) => rank(b) - rank(a));
    for (const item of ordered) {
      const active = item.entry?.id === selected;
      const threshold = view.zoom >= 4 ? 0 : view.zoom > 1.7 ? 130 : 800;
      if (item.entry && !active && item.entry.district.areaKm2 < threshold) { item.element.style.display = 'none'; continue; }
      const [x, y] = screenPoint(item.position, depth * (active ? 1.5 : 1));
      const bw = active ? 46 : item.type === 'place' ? Math.max(38, item.name.length * 5.4) : 24;
      const bh = active ? 24 : 18;
      const box = { l: x - bw / 2 - 3, r: x + bw / 2 + 3, t: y - bh / 2 - 2, b: y + bh / 2 + 2 };
      const collision = occupied.some(other => box.l < other.r && box.r > other.l && box.t < other.b && box.b > other.t);
      if (x < 12 || x > width - 12 || y < 18 || y > height - 12 || (!active && collision)) { item.element.style.display = 'none'; continue; }
      occupied.push(box);
      item.element.style.display = '';
      item.element.style.left = `${num(x)}px`;
      item.element.style.top = `${num(y)}px`;
    }
  }
  function updateView() {
    const [cx, cy] = projectCenter(), scale = baseScale * view.zoom;
    viewport.setAttribute('transform', `translate(${num(frameBox.x + frameBox.width / 2)},${num(frameBox.y + frameBox.height / 2)}) scale(${scale}) translate(${-cx},${-cy})`);
    updateLabels();
    dirty = false;
  }
  function resize() {
    if (disposed) return;
    const rect = container.getBoundingClientRect();
    width = Math.max(1, rect.width); height = Math.max(1, rect.height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    const left = width >= 600 ? Math.min(150, width * .20) : width >= 450 ? 95 : 37;
    const top = height < 350 ? 37 : 44, bottom = 25;
    frameBox = { x: left, y: top, width: Math.max(100, width - left - 18), height: Math.max(100, height - top - bottom) };
    rebuildGeometry();
  }
  function getId(event) {
    const path = event.target?.closest?.('[data-district-id]');
    return path && svg.contains(path) ? Number(path.dataset.districtId) : null;
  }
  function pan(dx, dy) {
    const [x, y] = inverse(-dx / (baseScale * view.zoom), -dy / (baseScale * view.zoom));
    view.x += x; view.y += y; isHome = false;
    updateView();
  }

  let drag = null, pendingOrbit = false;
  listen(svg, 'pointerdown', event => {
    if (event.button !== 0 && event.button !== 2) return;
    svg.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY, moved: false,
      district: getId(event), rotate: event.shiftKey || event.altKey || event.button === 2 };
    svg.style.cursor = 'grabbing';
  });
  listen(svg, 'pointermove', event => {
    if (drag && drag.id === event.pointerId) {
      const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
      if (Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 4) drag.moved = true;
      if (drag.moved) {
        if (drag.rotate) {
          view.yaw = clamp(view.yaw + dx * .0025, -.5, .4);
          view.tilt = clamp(view.tilt - dy * .0018, .62, .96);
          pendingOrbit = true;
        } else pan(dx, dy);
      }
      drag.x = event.clientX; drag.y = event.clientY;
      return;
    }
    const id = getId(event);
    if (id !== hovered) { hovered = id; updateColors(); }
    svg.style.cursor = id ? 'pointer' : 'grab';
    options.onHover?.(id, event);
  });
  listen(svg, 'pointerup', event => {
    if (!drag || drag.id !== event.pointerId) return;
    const clicked = !drag.moved && event.button === 0;
    const id = drag.district;
    drag = null;
    if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
    svg.style.cursor = 'grab';
    if (clicked && id) { select(id); options.onSelect?.(id, event); }
  });
  const cancel = () => { drag = null; svg.style.cursor = 'grab'; };
  listen(svg, 'pointercancel', cancel); listen(svg, 'lostpointercapture', cancel);
  listen(svg, 'pointerleave', event => { if (!drag) { hovered = null; updateColors(); options.onHover?.(null, event); } });
  listen(svg, 'contextmenu', event => event.preventDefault());
  listen(svg, 'wheel', event => { event.preventDefault(); zoom(Math.exp(-clamp(event.deltaY, -400, 400) * .0015)); }, { passive: false });
  listen(svg, 'keydown', event => {
    if (event.target !== svg && ['Enter', ' '].includes(event.key)) return;
    const key = event.key;
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', '_', 'Home', '0'].includes(key)) event.preventDefault();
    if (key === 'ArrowLeft') pan(40, 0); if (key === 'ArrowRight') pan(-40, 0);
    if (key === 'ArrowUp') pan(0, 40); if (key === 'ArrowDown') pan(0, -40);
    if (key === '+' || key === '=') zoom(1.25); if (key === '-' || key === '_') zoom(.8);
    if (key === 'Home' || key === '0') reset();
  });

  function select(id) { selected = entries.has(Number(id)) ? Number(id) : null; applySelection(); }
  function setColors(fn) { colorFor = fn; updateColors(); }
  function setMode(value) {
    mode = ['2d', 'flat', 'top'].includes(String(value).toLowerCase()) ? 'flat' : '3d';
    view.yaw = mode === 'flat' ? 0 : DEFAULT_YAW;
    view.tilt = mode === 'flat' ? 1 : DEFAULT_TILT;
    rebuildGeometry();
  }
  function zoom(factor) {
    if (!Number.isFinite(Number(factor)) || Number(factor) <= 0) return;
    view.zoom = clamp(view.zoom * Number(factor), .72, 22);
    updateView();
  }
  function reset() {
    isHome = true;
    Object.assign(view, { x: 0, y: 0, zoom: 1, yaw: mode === 'flat' ? 0 : DEFAULT_YAW, tilt: mode === 'flat' ? 1 : DEFAULT_TILT });
    rebuildGeometry();
  }
  function rotate() {
    mode = '3d';
    view.yaw = view.yaw >= .2 ? -.3 : view.yaw + .14;
    view.tilt = DEFAULT_TILT;
    rebuildGeometry();
  }
  function focus(input) {
    const bounds = Array.isArray(input) ? input : input?.bounds || input?.viewBox;
    if (!bounds || bounds.length !== 4 || !bounds.every(Number.isFinite) || bounds[2] <= 0 || bounds[3] <= 0) return;
    const [x, y, w, h] = bounds;
    // Aim at the cap plane so close views do not shift upward by the relief.
    const b = projectedBounds([[x, y], [x + w, y], [x, y + h], [x + w, y + h]], depth);
    [view.x, view.y] = inverse((b.minX + b.maxX) / 2, (b.minY + b.maxY) / 2);
    view.zoom = clamp(.85 * Math.min(frameBox.width / b.width, frameBox.height / b.height) / baseScale, .72, 22);
    isHome = false;
    updateView();
  }

  function tick(time) {
    if (disposed) return;
    raf = requestAnimationFrame(tick);
    if (document.hidden) return;
    if (pendingOrbit) { pendingOrbit = false; rebuildGeometry(); }
    if (dirty) updateView();
    if (motion() && time - lastShimmer > 100) {
      const shift = Math.sin(time * .00022) * 62;
      for (const entry of entries.values()) entry.gradient.setAttribute('gradientTransform', `translate(${num(shift)},${num(shift * .45)})`);
      lastShimmer = time;
    }
  }
  const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
  observer?.observe(container);
  if (!observer) listen(window, 'resize', resize);
  function dispose() {
    if (disposed) return;
    disposed = true; cancelAnimationFrame(raf); observer?.disconnect();
    listenerRemovers.splice(0).forEach(remove => remove());
    svg.remove(); labels.remove();
    delete container.dataset.atlas3d;
  }
  resize();
  container.dataset.atlas3d = 'svg-ready';
  raf = requestAnimationFrame(tick);
  return { select, setColors, setMode, zoom, reset, rotate, focus, dispose };
}
