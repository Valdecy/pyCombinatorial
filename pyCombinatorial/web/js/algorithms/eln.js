// ============================================================================
// eln.js — Elastic Net for TSP
// Mirrors algorithm/eln.py — ring of neurons deforms to fit cities, balanced
// between data-attraction and elastic spring forces.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'eln',
  label: 'Elastic Net',
  category: 'Neural',
  description: 'A ring of neurons relaxes into a tour under data + elastic forces (Durbin-Willshaw).',
  needsCoords: true,
  params: [
    { key: 'iterations',   label: 'Iterations',   type: 'int',   default: 1500,    min: 100, max: 50000 },
    { key: 'alpha',        label: 'α (data)',     type: 'float', default: 0.2,     min: 0.001, max: 1, step: 0.01 },
    { key: 'beta',         label: 'β (elastic)',  type: 'float', default: 2.0,     min: 0.001, max: 10, step: 0.1 },
    { key: 'k',            label: 'k (initial)',  type: 'float', default: 0.2,     min: 0.001, max: 1, step: 0.01 },
    { key: 'learningRate', label: 'k decay',      type: 'float', default: 0.99,    min: 0.5,   max: 1, step: 0.001 },
    { key: 'learningUpt',  label: 'k decay every',type: 'int',   default: 25,      min: 1,     max: 1000 },
    { key: 'nNeurons',     label: 'Neurons',      type: 'int',   default: 100,     min: 10,    max: 1000,
      hint: 'Actual count = max(2.5 × cities, this).' },
    { key: 'radius',       label: 'Init radius',  type: 'float', default: 0.1,     min: 0.01,  max: 1, step: 0.01 },
    { key: 'yieldEvery',   label: 'Yield every',  type: 'int',   default: 25,      min: 1,     max: 1000 },
    { key: 'seed',         label: 'Random seed',  type: 'int',   default: 42,      min: 0,     max: 99999 },
  ],
};

function decodeFromDS(ds, n) {
  // ds: m × n matrix of squared distances from each city to each neuron.
  // For each city, find its closest neuron.
  // Then sort cities by neuron index.
  const m = ds[0].length;
  const closest = new Array(n);
  for (let i = 0; i < n; i++) {
    let bj = 0, bv = Infinity;
    for (let j = 0; j < m; j++) if (ds[i][j] < bv) { bv = ds[i][j]; bj = j; }
    closest[i] = bj;
  }
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => closest[a] - closest[b]);
  return order;
}

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const rng = mulberry32(params.seed ?? 42);
  const M = Math.max(Math.floor(2.5 * n), params.nNeurons ?? 100);

  // normalize coords to [0,1]
  let mn = Infinity, mx = -Infinity;
  for (const [x, y] of coords) {
    if (x < mn) mn = x; if (y < mn) mn = y;
    if (x > mx) mx = x; if (y > mx) mx = y;
  }
  const span = (mx - mn) + 1e-15;
  const cN = coords.map(([x, y]) => [(x - mn) / span, (y - mn) / span]);
  const centroid = [0, 0];
  for (const c of cN) { centroid[0] += c[0]; centroid[1] += c[1]; }
  centroid[0] /= n; centroid[1] /= n;

  // init neurons: ring of radius `radius` around centroid
  const radius = params.radius ?? 0.1;
  const neurons = [];
  for (let i = 0; i < M; i++) {
    const t = (i / M) * 2 * Math.PI;
    neurons.push([centroid[0] + radius * Math.cos(t), centroid[1] + radius * Math.sin(t)]);
  }

  let k = params.k ?? 0.2;
  const alpha = params.alpha ?? 0.2;
  const beta = params.beta ?? 2.0;
  const lr = params.learningRate ?? 0.99;
  const lrUpt = params.learningUpt ?? 25;
  const iterations = params.iterations ?? 1500;
  const yieldEvery = Math.max(1, params.yieldEvery ?? 25);

  // helper: denormalize neurons for renderer
  const denorm = () => neurons.map(([x, y]) => [x * span + mn, y * span + mn]);

  yield {
    phase: 'init',
    neurons: denorm(),
    iteration: 0, bestDistance: NaN,
    message: `init: ${M} neurons, k=${k.toFixed(3)}`,
  };

  let bestDist = Infinity, bestTour = null;

  for (let it = 0; it < iterations; it++) {
    if (it > 0 && it % lrUpt === 0) k = Math.max(0.01, k * lr);

    // ds: n × M squared distances; ws: n × M weights softmax-like
    const ds = Array.from({ length: n }, () => new Float64Array(M));
    const dt = Array.from({ length: n }, () => new Array(M));
    const ws = Array.from({ length: n }, () => new Float64Array(M));
    for (let i = 0; i < n; i++) {
      let sum = 0;
      for (let j = 0; j < M; j++) {
        const dx = cN[i][0] - neurons[j][0], dy = cN[i][1] - neurons[j][1];
        const d2 = dx * dx + dy * dy;
        ds[i][j] = d2;
        dt[i][j] = [dx, dy];
        const w = Math.exp(-d2 / (2 * k * k));
        ws[i][j] = w; sum += w;
      }
      if (sum > 0) for (let j = 0; j < M; j++) ws[i][j] /= sum;
    }

    // D_force[j] = sum over cities of ws[i][j] * dt[i][j]
    const D_force = Array.from({ length: M }, () => [0, 0]);
    for (let j = 0; j < M; j++)
      for (let i = 0; i < n; i++) {
        D_force[j][0] += ws[i][j] * dt[i][j][0];
        D_force[j][1] += ws[i][j] * dt[i][j][1];
      }

    // L_force = neurons[j-1] - 2 neurons[j] + neurons[j+1]   (cyclic)
    const L_force = Array.from({ length: M }, () => [0, 0]);
    for (let j = 0; j < M; j++) {
      const prev = neurons[(j - 1 + M) % M], curr = neurons[j], next = neurons[(j + 1) % M];
      L_force[j][0] = prev[0] - 2 * curr[0] + next[0];
      L_force[j][1] = prev[1] - 2 * curr[1] + next[1];
    }

    for (let j = 0; j < M; j++) {
      neurons[j][0] += alpha * D_force[j][0] + beta * k * L_force[j][0];
      neurons[j][1] += alpha * D_force[j][1] + beta * k * L_force[j][1];
    }

    if (it % yieldEvery === 0 || it === iterations - 1) {
      const order = decodeFromDS(ds, n);
      const tour = [...order.map(c => c + 1), order[0] + 1];
      const d = distanceCalc(distanceMatrix, tour);
      const improved = d < bestDist;
      if (improved) { bestDist = d; bestTour = tour; }
      yield {
        phase: improved ? 'improvement' : 'training',
        tour, bestTour,
        neurons: denorm(),
        distance: d, bestDistance: bestDist,
        iteration: it + 1, temperature: k,
        message: improved ? `★ ${d.toFixed(2)}` : `it ${it + 1}: k=${k.toFixed(3)}  d=${d.toFixed(2)}`,
      };
    }
  }
  return { tour: bestTour, distance: bestDist, summary: `Elastic Net: ${bestDist.toFixed(2)}` };
}
