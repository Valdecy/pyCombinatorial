// ============================================================================
// s_itr.js — Iterated Search
// Mirrors algorithm/s_itr.py — random 4-opt perturbation + stochastic 2-opt
// local search; keep best.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng, shuffle } from '../core/seed.js';

export const meta = {
  id: 's_itr',
  label: 'Iterated Search',
  category: 'Local search',
  description: 'Stochastic 4-opt kick + random-2-opt local search, restart on plateau.',
  params: [
    { key: 'iterations',  label: 'Iterations',   type: 'int', default: 50, min: 1, max: 1000 },
    { key: 'maxAttempts', label: 'LS attempts',  type: 'int', default: 20, min: 1, max: 1000 },
    { key: 'seed',        label: 'Random seed',  type: 'int', default: 42, min: 0, max: 99999 },
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

function localSearch(distanceMatrix, tour, dist, maxAttempts, rng) {
  let count = 0;
  let best = [tour.slice(), dist];
  while (count < maxAttempts) {
    const c = stoch2opt(distanceMatrix, best[0], rng);
    if (c[1] < best[1]) { best = c; count = 0; }
    else count++;
  }
  return best;
}

// 4-opt perturbation (selects from a fixed trial list — see s_itr.py)
const TRIALS = [
  // sequential and non-sequential 4-opt rearrangements (25 combos)
  ['A','b','c','d'],['A','C','B','d'],['A','C','b','d'],['A','c','B','d'],['A','D','B','c'],
  ['A','D','b','C'],['A','d','B','c'],['A','d','b','C'],['A','d','b','c'],['A','b','D','C'],
  ['A','b','D','c'],['A','b','d','C'],['A','C','d','B'],['A','C','d','b'],['A','c','D','B'],
  ['A','c','D','b'],['A','c','d','b'],['A','D','C','b'],['A','D','c','B'],['A','d','C','B'],
  ['A','b','C','d'],['A','D','b','c'],['A','c','d','B'],['A','D','C','B'],['A','d','C','b'],
];
function lookupSeg(letter, A, B, b, C, c, D, d) {
  switch (letter) {
    case 'A': return A; case 'B': return B; case 'b': return b;
    case 'C': return C; case 'c': return c;
    case 'D': return D; case 'd': return d;
  }
}

function pertub4opt(distanceMatrix, tour, rng) {
  const open = tour.slice(0, -1);
  const n = open.length;
  if (n < 5) return [tour.slice(), distanceCalc(distanceMatrix, tour)];
  const idx = Array.from({ length: n }, (_, i) => i);
  shuffle(idx, rng);
  const [i, j, k, L] = idx.slice(0, 4).sort((a, b) => a - b);
  const A = open.slice(0, i + 1).concat(open.slice(i + 1, j + 1));
  const B = open.slice(j + 1, k + 1);
  const b = [...B].reverse();
  const C = open.slice(k + 1, L + 1);
  const c = [...C].reverse();
  const D = open.slice(L + 1);
  const d = [...D].reverse();
  const t = TRIALS[Math.floor(rng() * TRIALS.length)];
  const segs = t.map(l => lookupSeg(l, A, B, b, C, c, D, d));
  const newOpen = [].concat(...segs);
  newOpen.push(newOpen[0]);
  return [newOpen, distanceCalc(distanceMatrix, newOpen)];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let solution = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let best = [solution[0].slice(), solution[1]];

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 50;
  const maxAttempts = params.maxAttempts ?? 20;

  for (let it = 0; it < iterations; it++) {
    if (distanceMatrix.length > 4) solution = pertub4opt(distanceMatrix, solution[0], rng);
    solution = localSearch(distanceMatrix, solution[0], solution[1], maxAttempts, rng);
    const improved = solution[1] < best[1];
    if (improved) best = [solution[0].slice(), solution[1]];
    yield {
      phase: improved ? 'improvement' : 'kick',
      tour: solution[0], bestTour: best[0],
      distance: solution[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${solution[1].toFixed(2)}` : `${solution[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `Iterated Search: ${best[1].toFixed(2)}` };
}
