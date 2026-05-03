// ============================================================================
// som.js — Self-Organizing Maps for TSP
// Mirrors algorithm/som.py (without internal 2-opt; use the post-step refiner).
// Adapted from https://github.com/diego-vicente/som-tsp
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { makeRng } from '../core/seed.js';

export const meta = {
  id: 'som',
  label: 'Self-Organizing Map',
  category: 'Neural',
  description: 'A ring of neurons deforms to fit the cities; final order = tour.',
  needsCoords: true,
  params: [
    { key: 'sizeMultiplier', label: 'Ring × cities',  type: 'int',   default: 4,       min: 1,  max: 12 },
    { key: 'iterations',     label: 'Iterations',     type: 'int',   default: 8000,    min: 100, max: 100000 },
    { key: 'learningRate',   label: 'Learning rate',  type: 'float', default: 0.80,    min: 0.01, max: 1.0, step: 0.01 },
    { key: 'decayLr',        label: 'LR decay',       type: 'float', default: 0.99997, min: 0.9,  max: 1.0, step: 0.00001 },
    { key: 'decayNr',        label: 'Radius decay',   type: 'float', default: 0.99997, min: 0.9,  max: 1.0, step: 0.00001 },
    { key: 'yieldEvery',     label: 'Yield every',    type: 'int',   default: 25,      min: 1,    max: 1000,
      hint: 'How often (in iterations) to emit a frame. Higher = faster animation.' },
    { key: 'seed',           label: 'Random seed',    type: 'int',   default: 42,      min: 0,    max: 99999 },
  ],
};

function selectNeuron(neurons, ind) {
  let best = -1, bestD = Infinity;
  for (let i = 0; i < neurons.length; i++) {
    const dx = neurons[i][0] - ind[0];
    const dy = neurons[i][1] - ind[1];
    const d = dx * dx + dy * dy;
    if (d < bestD) { bestD = d; best = i; }
  }
  return best;
}

function updateNeurons(neurons, idx, nr, lr, ind, nCoordsLen) {
  const m = neurons.length;
  const radius = Math.max(1, Math.min(Math.floor(nr / 10), Math.floor(nCoordsLen / 10) || 1));
  const r2 = 2 * radius * radius;
  for (let i = 0; i < m; i++) {
    const delt = Math.abs(idx - i);
    const dist = Math.min(delt, m - delt);
    const noise = Math.exp(-(dist * dist) / r2);
    const w = noise * lr;
    neurons[i][0] += w * (ind[0] - neurons[i][0]);
    neurons[i][1] += w * (ind[1] - neurons[i][1]);
  }
}

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const rng = makeRng(params.seed ?? 42);

  // normalize coords to [0,1]^2
  let mn = Infinity, mx = -Infinity;
  for (const [x, y] of coords) {
    if (x < mn) mn = x; if (y < mn) mn = y;
    if (x > mx) mx = x; if (y > mx) mx = y;
  }
  const span = (mx - mn) || 1e-15;
  const nCoord = coords.map(([x, y]) => [(x - mn) / span, (y - mn) / span]);

  // init neurons (we'll keep them in NORMALIZED space, denormalize for rendering)
  const M = n * (params.sizeMultiplier ?? 4);
  const neurons = Array.from({ length: M }, () => [rng(), rng()]);

  // helper: denormalize neurons for renderer (renderer expects same space as coords)
  const denorm = () => neurons.map(([x, y]) => [x * span + mn, y * span + mn]);

  let lr = params.learningRate ?? 0.8;
  let nr = n;
  const totalIters = params.iterations ?? 8000;
  const yieldEvery = Math.max(1, params.yieldEvery ?? 25);
  const decayLr = params.decayLr ?? 0.99997;
  const decayNr = params.decayNr ?? 0.99997;

  yield {
    phase: 'init',
    neurons: denorm(),
    iteration: 0,
    distance: NaN,
    bestDistance: NaN,
    message: `init: ${M} neurons, lr=${lr.toFixed(3)}, nr=${nr.toFixed(2)}`,
  };

  let count = 0;
  while (count <= totalIters) {
    const cityIdx = Math.floor(rng() * n);
    const ind = nCoord[cityIdx];
    const bmu = selectNeuron(neurons, ind);
    updateNeurons(neurons, bmu, nr, lr, ind, n);

    if (count % yieldEvery === 0) {
      yield {
        phase: 'training',
        neurons: denorm(),
        bmu,
        currentCity: cityIdx,
        iteration: count,
        distance: NaN,
        bestDistance: NaN,
        temperature: lr,                                 // reuse 'temperature' slot for LR display
        extras: { lr, nr, radius: Math.max(1, Math.floor(nr / 10)) },
        message: `it=${count}  lr=${lr.toFixed(3)}  nr=${nr.toFixed(2)}`,
      };
    }

    lr *= decayLr;
    nr *= decayNr;
    if (nr < 1)         { yield { phase: 'note', neurons: denorm(), iteration: count, message: 'radius decayed' }; break; }
    if (lr < 0.001)     { yield { phase: 'note', neurons: denorm(), iteration: count, message: 'learning rate decayed' }; break; }
    count++;
  }

  // build the tour: assign each city to its nearest neuron, sort cities by neuron index
  const selected = nCoord.map(c => selectNeuron(neurons, c));
  const order = Array.from({ length: n }, (_, i) => i);
  order.sort((a, b) => selected[a] - selected[b]);
  const tour = order.map(i => i + 1);
  tour.push(tour[0]);
  const dist = distanceCalc(distanceMatrix, tour);

  yield {
    phase: 'tour-extract',
    tour: [...tour],
    bestTour: [...tour],
    neurons: denorm(),
    distance: dist,
    bestDistance: dist,
    iteration: count,
    message: `extracted tour: ${dist.toFixed(2)}`,
  };

  return {
    tour,
    distance: dist,
    summary: `SOM complete: ${dist.toFixed(2)} (${count} iterations)`,
  };
}
