// ============================================================================
// sa.js — Simulated Annealing
// Mirrors algorithm/sa.py (with 4-opt double-bridge perturbation)
// Internal 2-opt is omitted for visualization clarity; use the post-step refiner.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 'sa',
  label: 'Simulated Annealing',
  category: 'Metaheuristic',
  description: 'Random 4-opt perturbations accepted with probability exp(-Δ/T).',
  params: [
    { key: 'initialTemperature',  label: 'Initial T',    type: 'float', default: 1.0,    min: 0.001, max: 100, step: 0.1 },
    { key: 'temperatureIters',    label: 'Iters per T',  type: 'int',   default: 10,     min: 1,     max: 1000 },
    { key: 'finalTemperature',    label: 'Final T',      type: 'float', default: 0.0001, min: 1e-6,  max: 1, step: 1e-4 },
    { key: 'alpha',               label: 'Cooling α',    type: 'float', default: 0.9,    min: 0.5,   max: 0.999, step: 0.01 },
    { key: 'seed',                label: 'Random seed',  type: 'int',   default: 42,     min: 0,     max: 99999 },
  ],
};

/* 4-opt double-bridge style perturbation, mirroring update_solution() */
function perturb4opt(distanceMatrix, guess, rng) {
  const seq = guess[0].slice(0, -1);
  const n = seq.length;
  const idx = [];
  while (idx.length < 4) {
    const k = Math.floor(rng() * n);
    if (!idx.includes(k)) idx.push(k);
  }
  idx.sort((a, b) => a - b);
  const [i, j, k, L] = idx;
  const A = seq.slice(0, i + 1).concat(seq.slice(i + 1, j + 1));
  const B = seq.slice(j + 1, k + 1);
  const C = seq.slice(k + 1, L + 1);
  const D = seq.slice(L + 1);
  const b = [...B].reverse();
  const c = [...C].reverse();
  const d = [...D].reverse();

  const trials = [
    A.concat(b, c, d), A.concat(C, B, d), A.concat(C, b, d), A.concat(c, B, d), A.concat(D, B, c),
    A.concat(D, b, C), A.concat(d, B, c), A.concat(d, b, C), A.concat(d, b, c), A.concat(b, D, C),
    A.concat(b, D, c), A.concat(b, d, C), A.concat(C, d, B), A.concat(C, d, b), A.concat(c, D, B),
    A.concat(c, D, b), A.concat(c, d, b), A.concat(D, C, b), A.concat(D, c, B), A.concat(d, C, B),
    A.concat(b, C, d), A.concat(D, b, c), A.concat(c, d, B), A.concat(D, C, B), A.concat(d, C, b),
  ];

  const item = trials[Math.floor(rng() * trials.length)];
  const newSeq = item.concat([item[0]]);
  return [newSeq, distanceCalc(distanceMatrix, newSeq)];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  const T0    = params.initialTemperature ?? 1.0;
  const Tend  = params.finalTemperature   ?? 1e-4;
  const alpha = params.alpha              ?? 0.9;
  const iters = params.temperatureIters   ?? 10;

  let guess = params._initialTour
    ? [params._initialTour, distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let best = [[...guess[0]], guess[1]];
  let T = T0;
  let totalSteps = 0;
  let accepted = 0;
  let rejected = 0;
  let uphill = 0;

  yield {
    phase: 'init',
    tour: [...guess[0]],
    bestTour: [...best[0]],
    distance: guess[1],
    bestDistance: best[1],
    temperature: T,
    iteration: 0,
    message: `T₀=${T.toFixed(4)}, start ${guess[1].toFixed(2)}`,
  };

  while (T > Tend) {
    for (let r = 0; r < iters; r++) {
      const fxOld = guess[1];
      const cand  = perturb4opt(distanceMatrix, guess, rng);
      const delta = cand[1] - fxOld;
      const p     = Math.exp(-delta / T);
      const u     = rng();
      const accept = (delta < 0) || (u <= p);
      totalSteps++;

      if (accept) {
        guess = cand;
        accepted++;
        if (delta > 0) uphill++;
      } else {
        rejected++;
      }
      if (cand[1] < best[1]) best = [[...cand[0]], cand[1]];

      yield {
        phase: accept ? (delta < 0 ? 'accept-down' : 'accept-up') : 'reject',
        tour: [...guess[0]],
        bestTour: [...best[0]],
        distance: guess[1],
        bestDistance: best[1],
        temperature: T,
        iteration: totalSteps,
        message: `T=${T.toFixed(4)}  Δ=${delta.toFixed(2)}  ${accept ? '✓' : '✗'}`,
      };
    }
    T *= alpha;
  }

  return {
    tour: best[0],
    distance: best[1],
    summary: `SA complete: ${best[1].toFixed(2)} (acc=${accepted}, rej=${rejected}, uphill=${uphill})`,
  };
}
