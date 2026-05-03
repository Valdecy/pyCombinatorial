// ============================================================================
// s_gui.js — Guided (Local) Search
// Mirrors algorithm/s_gui.py — augmented cost = real cost + λ × penalty;
// penalize utility-maximizing edges between iterations.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 's_gui',
  label: 'Guided Search',
  category: 'Local search',
  description: 'Penalize "bad" edges via augmented cost; iterate stochastic 2-opt.',
  params: [
    { key: 'iterations',  label: 'Iterations',     type: 'int',   default: 50,   min: 1,   max: 1000 },
    { key: 'maxAttempts', label: 'LS attempts',    type: 'int',   default: 20,   min: 1,   max: 1000 },
    { key: 'alpha',       label: 'α (penalty)',    type: 'float', default: 0.3,  min: 0,   max: 5, step: 0.05 },
    { key: 'optimaHint',  label: 'Optimum hint',   type: 'float', default: 1000, min: 0,   max: 1e7,
      hint: 'Reference local-optimum scale; tune to your instance.' },
    { key: 'seed',        label: 'Random seed',    type: 'int',   default: 42,   min: 0,   max: 99999 },
  ],
};

function key(c1, c2) { if (c2 < c1) [c1, c2] = [c2, c1]; return c1 * 1e6 + c2; }

function augCost(distanceMatrix, tour, penalty, limit) {
  let s = 0;
  for (let i = 0; i < tour.length - 1; i++) {
    let c1 = tour[i] - 1, c2 = tour[i + 1] - 1;
    if (c2 < c1) [c1, c2] = [c2, c1];
    s += distanceMatrix[c1][c2] + limit * (penalty.get(key(c1, c2)) || 0);
  }
  return s;
}

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

function gLocalSearch(distanceMatrix, tour, dist, penalty, limit, maxAttempts, rng) {
  let solution = [tour.slice(), dist];
  let agCost = augCost(distanceMatrix, solution[0], penalty, limit);
  let count = 0;
  while (count < maxAttempts) {
    const c = stoch2opt(distanceMatrix, solution[0], rng);
    const ag = augCost(distanceMatrix, c[0], penalty, limit);
    if (ag < agCost) { solution = c; agCost = ag; count = 0; }
    else count++;
  }
  return solution;
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let solution = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let best = [solution[0].slice(), solution[1]];

  const limit = (params.alpha ?? 0.3) * ((params.optimaHint ?? best[1]) / solution[0].length);
  const penalty = new Map();

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `λ=${limit.toFixed(3)}, start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 50;
  const maxAttempts = params.maxAttempts ?? 20;

  for (let it = 0; it < iterations; it++) {
    solution = gLocalSearch(distanceMatrix, solution[0], solution[1], penalty, limit, maxAttempts, rng);
    // utilities; penalize max-utility edges
    const us = new Array(solution[0].length).fill(0);
    let mx = -Infinity;
    for (let i = 0; i < solution[0].length - 1; i++) {
      let c1 = solution[0][i] - 1, c2 = solution[0][i + 1] - 1;
      if (c2 < c1) [c1, c2] = [c2, c1];
      const p = penalty.get(key(c1, c2)) || 0;
      us[i] = distanceMatrix[c1][c2] / (1 + p);
      if (us[i] > mx) mx = us[i];
    }
    for (let i = 0; i < solution[0].length - 1; i++) {
      if (us[i] === mx) {
        let c1 = solution[0][i] - 1, c2 = solution[0][i + 1] - 1;
        if (c2 < c1) [c1, c2] = [c2, c1];
        penalty.set(key(c1, c2), (penalty.get(key(c1, c2)) || 0) + 1);
      }
    }
    const improved = solution[1] < best[1];
    if (improved) best = [solution[0].slice(), solution[1]];
    yield {
      phase: improved ? 'improvement' : 'penalty-update',
      tour: solution[0], bestTour: best[0],
      distance: solution[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${solution[1].toFixed(2)}` : `${solution[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `Guided Search: ${best[1].toFixed(2)}` };
}
