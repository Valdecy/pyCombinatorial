// ============================================================================
// s_vns.js — Variable Neighborhood Search
// Mirrors algorithm/s_vns.py — apply increasing neighbourhood depth, jump out
// of local optima by stochastic 2-opt cascades.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 's_vns',
  label: 'Variable Neighborhood Search',
  category: 'Local search',
  description: 'VNS: cascading random 2-opt kicks of increasing depth, with local search.',
  params: [
    { key: 'iterations',        label: 'Iterations',   type: 'int', default: 50, min: 1, max: 1000 },
    { key: 'neighbourhoodSize', label: 'Neigh. size',  type: 'int', default: 5,  min: 1, max: 50 },
    { key: 'maxAttempts',       label: 'LS attempts',  type: 'int', default: 20, min: 1, max: 1000 },
    { key: 'seed',              label: 'Random seed',  type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

function stoch2opt(distanceMatrix, tour, rng) {
  const n = tour.length - 1;
  let i = Math.floor(rng() * n), j = Math.floor(rng() * n);
  if (i === j) j = (j + 1) % n;
  if (i > j) [i, j] = [j, i];
  const cand = tour.slice();
  const seg = cand.slice(i, j + 1).reverse();
  for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
  cand[cand.length - 1] = cand[0];
  return [cand, distanceCalc(distanceMatrix, cand)];
}

function localSearch(distanceMatrix, tour, dist, maxAttempts, neighSize, rng) {
  let count = 0;
  let best = [tour.slice(), dist];
  while (count < maxAttempts) {
    let cand;
    for (let i = 0; i < neighSize; i++) cand = stoch2opt(distanceMatrix, best[0], rng);
    if (cand[1] < best[1]) { best = cand; count = 0; } else count++;
  }
  return best;
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 50;
  const neigh = params.neighbourhoodSize ?? 5;
  const maxAttempts = params.maxAttempts ?? 20;

  for (let it = 0; it < iterations; it++) {
    let progress = false;
    for (let i = 0; i < neigh; i++) {
      let solution = [best[0].slice(), best[1]];
      for (let j = 0; j < neigh; j++) solution = stoch2opt(distanceMatrix, solution[0], rng);
      solution = localSearch(distanceMatrix, solution[0], solution[1], maxAttempts, neigh, rng);
      if (solution[1] < best[1]) {
        best = [solution[0].slice(), solution[1]];
        progress = true;
        break;
      }
    }
    yield {
      phase: progress ? 'improvement' : 'no-improvement',
      tour: best[0], bestTour: best[0],
      distance: best[1], bestDistance: best[1],
      iteration: it + 1,
      message: progress ? `★ ${best[1].toFixed(2)}` : `iter ${it + 1}: ${best[1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `VNS: ${best[1].toFixed(2)}` };
}
