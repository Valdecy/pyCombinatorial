// ============================================================================
// lns.js — Large Neighborhood Search
// Mirrors algorithm/lns.py — random removal + cheapest-insertion reconstruction.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';
import { shuffle } from '../core/seed.js';

export const meta = {
  id: 'lns',
  label: 'Large Neighborhood Search',
  category: 'Metaheuristic',
  description: 'Repeatedly remove a few cities and reinsert at cheapest position.',
  params: [
    { key: 'iterations',        label: 'Iterations',    type: 'int', default: 1000, min: 1,  max: 50000 },
    { key: 'neighborhoodSize',  label: 'Neigh. size',   type: 'int', default: 4,    min: 1,  max: 50,
      hint: 'Number of cities to remove and reinsert per iteration.' },
    { key: 'seed',              label: 'Random seed',   type: 'int', default: 42,   min: 0,  max: 99999 },
  ],
};

function shuffleIdx(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function distance0(dm, route0) {
  let s = 0;
  for (let i = 0; i < route0.length; i++) s += dm[route0[i]][route0[(i + 1) % route0.length]];
  return s;
}

function bestInsertion0(dm, route0, removed) {
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

  const close1 = r => [...r.map(c => c + 1), r[0] + 1];
  yield {
    phase: 'init', tour: close1(route0), bestTour: close1(route0),
    distance: dist, bestDistance: dist,
    iteration: 0, message: `start ${dist.toFixed(2)}`,
  };

  const iterations = params.iterations ?? 1000;
  const neigh = Math.max(1, Math.min(params.neighborhoodSize ?? 4, n - 2));

  for (let it = 0; it < iterations; it++) {
    // pick neigh distinct cities (excluding the very first, mirroring Python's [1:])
    const idxs = Array.from({ length: route0.length - 1 }, (_, i) => i + 1);
    shuffleIdx(idxs, rng);
    const removeIdx = idxs.slice(0, neigh).sort((a, b) => b - a);
    const removed = removeIdx.map(i => route0[i]);
    const work = route0.slice();
    for (const i of removeIdx) work.splice(i, 1);
    const candidate = bestInsertion0(distanceMatrix, work, removed);
    const candDist = distance0(distanceMatrix, candidate);
    const improved = candDist < dist;
    if (improved) { route0 = candidate; dist = candDist; }
    if (improved || it % Math.max(1, Math.floor(iterations / 80)) === 0 || it === iterations - 1) {
      yield {
        phase: improved ? 'improvement' : 'no-improvement',
        tour: close1(route0), bestTour: close1(route0),
        distance: dist, bestDistance: dist,
        iteration: it + 1,
        message: improved ? `★ ${dist.toFixed(2)}` : `iter ${it + 1}: ${dist.toFixed(2)}`,
      };
    }
  }
  const out = close1(route0);
  return { tour: out, distance: distanceCalc(distanceMatrix, out),
           summary: `LNS: ${distanceCalc(distanceMatrix, out).toFixed(2)}` };
}
