// ============================================================================
// s_shc.js — Stochastic Hill Climbing
// Mirrors algorithm/s_shc.py — random swap + small 2-opt; keep best.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';
import { localSearch2Opt } from './_shared.js';

export const meta = {
  id: 's_shc',
  label: 'Stochastic Hill Climbing',
  category: 'Local search',
  description: 'Random pair-swap mutation + bounded 2-opt; keep the best ever.',
  params: [
    { key: 'iterations', label: 'Iterations',  type: 'int', default: 50, min: 1, max: 5000 },
    { key: 'seed',       label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

function mutateCandidate(distanceMatrix, candidate, rng) {
  const tour = candidate[0];
  const n = tour.length - 1;
  // pick two distinct positions in (0, n)
  let k1 = 1 + Math.floor(rng() * (n - 1));
  let k2 = 1 + Math.floor(rng() * (n - 1));
  while (k2 === k1) k2 = 1 + Math.floor(rng() * (n - 1));
  const cand = [tour.slice(), 0];
  [cand[0][k1], cand[0][k2]] = [cand[0][k2], cand[0][k1]];
  cand[0][cand[0].length - 1] = cand[0][0];
  cand[1] = distanceCalc(distanceMatrix, cand[0]);
  // bounded 2-opt
  const [t2, d2] = localSearch2Opt(distanceMatrix, cand[0]);
  return [t2, d2];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let candidate = [best[0].slice(), best[1]];

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 50;
  for (let it = 0; it < iterations; it++) {
    candidate = mutateCandidate(distanceMatrix, candidate, rng);
    const improved = candidate[1] < best[1];
    if (improved) best = [candidate[0].slice(), candidate[1]];
    yield {
      phase: improved ? 'improvement' : 'mutate',
      tour: candidate[0], bestTour: best[0],
      distance: candidate[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${candidate[1].toFixed(2)}` : `${candidate[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `SHC: ${best[1].toFixed(2)}` };
}
