// ============================================================================
// renderer.js — canvas drawing for cities, tour, highlights, overlays
// ============================================================================

import { boundingBox } from './dataset.js';

/* CSS-variable-aware palette so it always matches the stylesheet */
function cssVar(name, fallback) {
  if (typeof document === 'undefined') return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name);
  return v?.trim() || fallback;
}

const COLORS = {
  city:        () => cssVar('--cyan',         '#5dd5e6'),
  cityFill:    () => cssVar('--bg-deep',      '#07090f'),
  tour:        () => cssVar('--amber',        '#f5b452'),
  tourGhost:   () => 'rgba(245,180,82,0.18)',
  highlight:   () => cssVar('--good',         '#7dd594'),
  reject:      () => cssVar('--bad',          '#e07a6b'),
  candidate:   () => 'rgba(93,213,230,0.45)',
  text:        () => cssVar('--text-primary', '#e6e2d6'),
  faint:       () => cssVar('--text-tertiary','#5a6373'),
  rule:        () => cssVar('--rule',         '#1d2533'),
};

export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.coords = [];
    this.bbox = null;
    this.dpr = window.devicePixelRatio || 1;
    this.cityRadius = 4;

    // optional secondary point set (for SOM neurons etc.)
    this.secondary = null;

    this._resize();
    window.addEventListener('resize', () => { this._resize(); this.redraw(); });
  }

  _resize() {
    const r = this.canvas.getBoundingClientRect();
    this.canvas.width = r.width * this.dpr;
    this.canvas.height = r.height * this.dpr;
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    this.cssW = r.width;
    this.cssH = r.height;
  }

  setCoords(coords) {
    this.coords = coords;
    this.bbox = boundingBox(coords, 0.06);
    this.lastState = null;
  }

  /** transform a coord [x,y] into canvas px */
  _t(x, y) {
    const b = this.bbox;
    if (!b) return [0, 0];
    const margin = 40;
    const w = this.cssW - margin * 2;
    const h = this.cssH - margin * 2;
    const sx = w / b.width;
    const sy = h / b.height;
    const s = Math.min(sx, sy);
    const offX = margin + (w - b.width * s) / 2;
    const offY = margin + (h - b.height * s) / 2;
    return [offX + (x - b.minX) * s, offY + (y - b.minY) * s];
  }

  clear() {
    this.ctx.clearRect(0, 0, this.cssW, this.cssH);
  }

  /** render full state — main entry point called by the stepper */
  render(state) {
    if (!state) return;
    this.lastState = state;
    this.clear();
    this._drawGrid();

    // extra edges (MST, hull, candidate forest, etc.) — drawn underneath tour
    if (state.extraEdges) this._drawExtraEdges(state.extraEdges);

    // optional secondary points (e.g. SOM neurons), drawn UNDER the tour
    if (state.neurons) this._drawNeurons(state.neurons, state.bmu);

    if (state.tour && state.tour.length > 1) {
      this._drawTour(state.tour, {
        color: state.tourColor || COLORS.tour(),
        width: 1.6,
        glow: true,
      });
    }

    if (state.bestTour && state.bestTour !== state.tour) {
      this._drawTour(state.bestTour, {
        color: COLORS.highlight(),
        width: 1.0,
        dash: [4, 4],
        alpha: 0.4,
      });
    }

    if (state.partialPath && state.partialPath.length > 1) {
      this._drawPartial(state.partialPath);
    }

    if (state.highlight) this._drawHighlight(state.highlight);
    if (state.candidates) this._drawCandidates(state.candidates);

    this._drawCities(state);
  }

  redraw() {
    if (this.lastState) this.render(this.lastState);
    else if (this.coords.length) {
      this.clear();
      this._drawGrid();
      this._drawCities(null);
    }
  }

  // ----- primitives ---------------------------------------------------------

  _drawGrid() {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = COLORS.rule();
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.35;
    const step = 40;
    ctx.beginPath();
    for (let x = step; x < this.cssW; x += step) {
      ctx.moveTo(x, 0); ctx.lineTo(x, this.cssH);
    }
    for (let y = step; y < this.cssH; y += step) {
      ctx.moveTo(0, y); ctx.lineTo(this.cssW, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  _drawCities(state) {
    const ctx = this.ctx;
    const r = this.cityRadius;

    for (let i = 0; i < this.coords.length; i++) {
      const [x, y] = this._t(this.coords[i][0], this.coords[i][1]);

      // halo for the "current" city if specified
      const isCurrent = state?.currentCity === i;
      const isVisited = state?.visited && state.visited[i];

      if (isCurrent) {
        ctx.save();
        ctx.fillStyle = COLORS.tour();
        ctx.globalAlpha = 0.25;
        ctx.beginPath();
        ctx.arc(x, y, r * 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      ctx.fillStyle = COLORS.cityFill();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();

      ctx.lineWidth = 1.4;
      ctx.strokeStyle = isCurrent ? COLORS.tour()
                      : isVisited ? COLORS.highlight()
                      : COLORS.city();
      ctx.stroke();
    }
  }

  _drawTour(tour1, opts = {}) {
    if (tour1.length < 2) return;
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = opts.color || COLORS.tour();
    ctx.lineWidth = opts.width || 1.6;
    if (opts.alpha != null) ctx.globalAlpha = opts.alpha;
    if (opts.dash) ctx.setLineDash(opts.dash);

    if (opts.glow) {
      ctx.shadowColor = opts.color || COLORS.tour();
      ctx.shadowBlur = 8;
    }

    ctx.beginPath();
    for (let i = 0; i < tour1.length; i++) {
      const idx = tour1[i] - 1;
      const [px, py] = this._t(this.coords[idx][0], this.coords[idx][1]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.restore();
  }

  /** partial path uses 0-indexed ids (used by branch & bound) */
  _drawPartial(path0) {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = COLORS.tour();
    ctx.lineWidth = 2;
    ctx.shadowColor = COLORS.tour();
    ctx.shadowBlur = 10;
    ctx.beginPath();
    for (let i = 0; i < path0.length; i++) {
      if (path0[i] < 0) break;
      const [px, py] = this._t(this.coords[path0[i]][0], this.coords[path0[i]][1]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.restore();
  }

  _drawHighlight(h) {
    const ctx = this.ctx;
    if (h.type === 'edge' && h.from != null && h.to != null) {
      const [ax, ay] = this._t(this.coords[h.from][0], this.coords[h.from][1]);
      const [bx, by] = this._t(this.coords[h.to][0], this.coords[h.to][1]);
      ctx.save();
      ctx.strokeStyle = h.color || COLORS.highlight();
      ctx.lineWidth = 2.4;
      ctx.shadowColor = h.color || COLORS.highlight();
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
      ctx.stroke();
      ctx.restore();
    } else if (h.type === '2opt-segment') {
      // highlight the i..j segment that was reversed (uses 1-indexed tour)
      const tour = h.tour;
      ctx.save();
      ctx.strokeStyle = h.color || COLORS.highlight();
      ctx.lineWidth = 2.6;
      ctx.shadowColor = h.color || COLORS.highlight();
      ctx.shadowBlur = 14;
      ctx.beginPath();
      for (let k = h.i; k <= h.j + 1; k++) {
        const idx = tour[k] - 1;
        const [px, py] = this._t(this.coords[idx][0], this.coords[idx][1]);
        if (k === h.i) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
      ctx.restore();
    }
  }

  _drawCandidates(cands) {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = COLORS.candidate();
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);
    ctx.beginPath();
    for (const [a, b] of cands) {
      const [ax, ay] = this._t(this.coords[a][0], this.coords[a][1]);
      const [bx, by] = this._t(this.coords[b][0], this.coords[b][1]);
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
    }
    ctx.stroke();
    ctx.restore();
  }

  /**
   * Extra edges — for MST, convex hull, candidate forests, etc.
   * Each edge: [a, b] (0-indexed) or { a, b, color?, alpha?, width?, dash? }.
   */
  _drawExtraEdges(edges) {
    const ctx = this.ctx;
    for (const e of edges) {
      const a = Array.isArray(e) ? e[0] : e.a;
      const b = Array.isArray(e) ? e[1] : e.b;
      const opts = Array.isArray(e) ? {} : e;
      const [ax, ay] = this._t(this.coords[a][0], this.coords[a][1]);
      const [bx, by] = this._t(this.coords[b][0], this.coords[b][1]);
      ctx.save();
      ctx.strokeStyle = opts.color || COLORS.faint();
      ctx.lineWidth = opts.width || 1;
      ctx.globalAlpha = opts.alpha != null ? opts.alpha : 0.7;
      if (opts.dash) ctx.setLineDash(opts.dash);
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
      ctx.stroke();
      ctx.restore();
    }
  }

  /** SOM neurons: draws the closed ring of neuron positions */
  _drawNeurons(neurons, bmuIdx) {
    const ctx = this.ctx;
    if (!neurons || neurons.length < 2) return;

    // ring line
    ctx.save();
    ctx.strokeStyle = COLORS.tour();
    ctx.lineWidth = 1.4;
    ctx.shadowColor = COLORS.tour();
    ctx.shadowBlur = 8;
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    for (let i = 0; i <= neurons.length; i++) {
      const n = neurons[i % neurons.length];
      const [px, py] = this._t(n[0], n[1]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.restore();

    // dots
    for (let i = 0; i < neurons.length; i++) {
      const [px, py] = this._t(neurons[i][0], neurons[i][1]);
      ctx.fillStyle = i === bmuIdx ? COLORS.highlight() : COLORS.tour();
      ctx.globalAlpha = i === bmuIdx ? 1 : 0.5;
      ctx.beginPath();
      ctx.arc(px, py, i === bmuIdx ? 3 : 1.6, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  /** Convert canvas-px (clientX/Y minus rect) back into world coords */
  invert(px, py) {
    const b = this.bbox;
    if (!b) return [0, 0];
    const margin = 40;
    const w = this.cssW - margin * 2;
    const h = this.cssH - margin * 2;
    const s = Math.min(w / b.width, h / b.height);
    const offX = margin + (w - b.width * s) / 2;
    const offY = margin + (h - b.height * s) / 2;
    return [(px - offX) / s + b.minX, (py - offY) / s + b.minY];
  }

  drawEmpty() {
    this.clear();
    this._drawGrid();
  }
}
