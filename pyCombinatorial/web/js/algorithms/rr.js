// ============================================================================
// rr.js — Ruin & Recreate
// Mirrors algorithm/rr.py — remove a fraction of cities; reinsert using
// Regret-2 (max regret = 2nd-best minus best insertion delta).
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng, shuffle } from '../core/seed.js';

export const meta = {
  id: 'rr',
  label: 'Ruin & Recreate',
  category: 'Metaheuristic',
  description: 'Remove a random fraction of cities; greedily reinsert by regret-2.',
  params: [
    { key: 'iterations', label: 'Iterations',  type: 'int',   default: 100, min: 1, max: 5000 },
    { key: 'ruinRate',   label: 'Ruin rate',   type: 'float', default: 0.5, min: 0.05, max: 0.95, step: 0.05 },
    { key: 'seed',       label: 'Random seed', type: 'int',   default: 42,  min: 0, max: 99999 },
  ],
};

function regret2Insertion(distanceMatrix, partial, removed) {
  // partial: 1-indexed closed tour (with start at end)
  // removed: 1-indexed cities to insert
  const work0 = partial.slice(0, -1).map(c => c - 1);
  const toInsert = removed.map(c => c - 1);
  const remaining = new Set(toInsert);

  while (remaining.size > 0) {
    let bestRegret = -Infinity, bestCity = -1, bestPos = -1;
    for (const city of remaining) {
      const costs = [];
      for (let j = 0; j < work0.length - 1; j++) {
        const prev = work0[j], nxt = work0[j + 1];
        const delta = distanceMatrix[prev][city] + distanceMatrix[city][nxt] - distanceMatrix[prev][nxt];
        costs.push([delta, j + 1]);
      }
      // also try inserting at the end (closing edge)
      if (work0.length >= 2) {
        const prev = work0[work0.length - 1], nxt = work0[0];
        const delta = distanceMatrix[prev][city] + distanceMatrix[city][nxt] - distanceMatrix[prev][nxt];
        costs.push([delta, work0.length]);
      }
      if (costs.length === 0) continue;
      costs.sort((a, b) => a[0] - b[0]);
      const d1 = costs[0][0], p1 = costs[0][1];
      const d2 = costs.length > 1 ? costs[1][0] : d1;
      const regret = d2 - d1;
      if (regret > bestRegret) { bestRegret = regret; bestCity = city; bestPos = p1; }
    }
    if (bestCity < 0) break;
    work0.splice(bestPos, 0, bestCity);
    remaining.delete(bestCity);
  }
  return [...work0.map(c => c + 1), work0[0] + 1];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let cur = [best[0].slice(), best[1]];

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 100;
  const ruin = params.ruinRate ?? 0.5;

  for (let it = 0; it < iterations; it++) {
    const removable = cur[0].slice(0, -1);
    const nRemove = Math.max(1, Math.floor(removable.length * ruin));
    const idxs = Array.from({ length: removable.length }, (_, i) => i);
    shuffle(idxs, rng);
    const toRemove = idxs.slice(0, Math.min(nRemove, removable.length)).map(i => removable[i]);
    const removeSet = new Set(toRemove);
    let partial = cur[0].filter(c => !removeSet.has(c));
    if (partial.length < 2) partial = cur[0].slice();
    if (partial[0] !== partial[partial.length - 1]) partial.push(partial[0]);
    const recreated = regret2Insertion(distanceMatrix, partial, toRemove);
    const d = distanceCalc(distanceMatrix, recreated);
    const improved = d < best[1];
    if (improved) best = [recreated.slice(), d];
    cur = [recreated, d];
    yield {
      phase: improved ? 'improvement' : 'recreate',
      tour: cur[0], bestTour: best[0],
      distance: cur[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${cur[1].toFixed(2)}` : `iter ${it + 1}: ${cur[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }

  return { tour: best[0], distance: best[1], summary: `Ruin & Recreate: ${best[1].toFixed(2)}` };
}
