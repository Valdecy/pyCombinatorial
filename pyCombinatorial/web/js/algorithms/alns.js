// ============================================================================
// alns.js — Adaptive Large Neighborhood Search
// Mirrors algorithm/alns.py — LNS with SA-style acceptance and adaptive
// operator weights (single removal/insertion op so weights are mostly
// illustrative).
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'alns',
  label: 'Adaptive Large Neighborhood Search',
  category: 'Metaheuristic',
  description: 'LNS with simulated-annealing acceptance and adaptive operator weights.',
  params: [
    { key: 'iterations',      label: 'Iterations',     type: 'int',   default: 200, min: 1,  max: 50000 },
    { key: 'removalFraction', label: 'Removal frac',   type: 'float', default: 0.2, min: 0.05, max: 0.9, step: 0.05 },
    { key: 'rho',             label: 'ρ (weight LR)',  type: 'float', default: 0.1, min: 0,    max: 0.99, step: 0.01 },
    { key: 'sa',              label: 'SA acceptance',  type: 'bool',  default: true },
    { key: 'cooling',         label: 'Cooling α',      type: 'float', default: 0.995, min: 0.5, max: 0.9999, step: 0.001 },
    { key: 'seed',            label: 'Random seed',    type: 'int',   default: 42,  min: 0, max: 99999 },
  ],
};

function distance0(dm, route0) {
  let s = 0;
  for (let i = 0; i < route0.length; i++) s += dm[route0[i]][route0[(i + 1) % route0.length]];
  return s;
}

function shuffleIdx(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function randomRemoval(route0, n, rng) {
  const idxs = Array.from({ length: route0.length - 1 }, (_, i) => i + 1);
  shuffleIdx(idxs, rng);
  return idxs.slice(0, Math.max(1, Math.min(n, idxs.length))).sort((a, b) => b - a);
}

function cheapestReinsert(dm, route0, removed) {
  for (const node of removed) {
    let bestC = Infinity, bestI = 1;
    for (let i = 1; i <= route0.length; i++) {
      const last = route0[i - 1], nxt = route0[i % route0.length];
      const c = dm[last][node] + dm[node][nxt] - dm[last][nxt];
      if (c < bestC) { bestC = c; bestI = i; }
    }
    route0.splice(bestI, 0, node);
  }
  return route0;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
  let route0;
  if (params._initialTour) {
    route0 = params._initialTour.slice(0, -1).map(c => c - 1);
  } else {
    route0 = Array.from({ length: n }, (_, i) => i);
    shuffleIdx(route0, rng);
  }
  let dist = distance0(distanceMatrix, route0);
  let best = [route0.slice(), dist];

  // operator weights (we have one of each; adaptive update is illustrative)
  let wRem = 1.0, wIns = 1.0;
  const rho = params.rho ?? 0.1;
  let temp = Math.max(dist, 1e-12);
  const cooling = params.cooling ?? 0.995;

  const close1 = r => [...r.map(c => c + 1), r[0] + 1];
  yield {
    phase: 'init', tour: close1(route0), bestTour: close1(best[0]),
    distance: dist, bestDistance: best[1],
    iteration: 0, temperature: temp, message: `start T=${temp.toFixed(2)}, ${dist.toFixed(2)}`,
  };

  const iterations = params.iterations ?? 200;
  const frac = params.removalFraction ?? 0.2;
  const useSa = params.sa ?? true;

  for (let it = 0; it < iterations; it++) {
    const removeIdx = randomRemoval(route0, Math.max(1, Math.floor(frac * n)), rng);
    const removed = removeIdx.map(i => route0[i]);
    const work = route0.slice();
    for (const i of removeIdx) work.splice(i, 1);
    const candidate = cheapestReinsert(distanceMatrix, work, removed);
    const candDist = distance0(distanceMatrix, candidate);
    const delta = candDist - dist;
    let accept = delta < 0;
    if (!accept && useSa) accept = (rng() < Math.exp(-delta / temp));

    if (accept) {
      route0 = candidate; dist = candDist;
      wRem *= 1 + rho; wIns *= 1 + rho;
      if (dist < best[1]) best = [route0.slice(), dist];
    } else {
      wRem *= 1 - rho; wIns *= 1 - rho;
    }
    // normalize (vacuous with 1 op each but matches structure)
    const tw = wRem + wIns;
    wRem /= tw; wIns /= tw;
    if (useSa) temp = Math.max(temp * cooling, 1e-12);

    if (accept || it % Math.max(1, Math.floor(iterations / 80)) === 0 || it === iterations - 1) {
      yield {
        phase: accept ? (delta < 0 ? 'accept-down' : 'accept-up') : 'reject',
        tour: close1(route0), bestTour: close1(best[0]),
        distance: dist, bestDistance: best[1],
        iteration: it + 1, temperature: temp,
        message: `${accept ? '✓' : '✗'} Δ=${delta.toFixed(2)}  T=${temp.toFixed(2)}`,
      };
    }
  }
  const out = close1(best[0]);
  return { tour: out, distance: best[1], summary: `ALNS: ${best[1].toFixed(2)}` };
}
