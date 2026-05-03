// ============================================================================
// opt_2s.js — Stochastic 2-opt
// Mirrors algorithm/opt_2s.py — like opt_2 but only samples `search` (i,j) pairs.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 'opt_2s',
  label: '2-opt (stochastic)',
  category: 'Local search',
  description: 'Stochastic 2-opt: sample `search` (i,j) pairs per pass.',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'search', label: 'Pairs sampled', type: 'int', default: 1000, min: 1, max: 100000 },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  const recursive = params.recursiveSeeding ?? -1;
  const search = params.search ?? 1000;

  let cityList = params._initialTour
    ? [params._initialTour.slice(0, -1), distanceCalc(distanceMatrix, params._initialTour)]
    : (() => { const s = seedFunction(distanceMatrix, rng); return [s[0].slice(0, -1), s[1]]; })();

  const close = arr => [...arr, arr[0]];
  yield {
    phase: 'init',
    tour: close(cityList[0]), bestTour: close(cityList[0]),
    distance: cityList[1], bestDistance: cityList[1],
    iteration: 0, message: `start ${cityList[1].toFixed(2)}`,
  };

  let priorBest = cityList[1] * 2;
  let count, target;
  if (recursive < 0) { count = -2; target = -1; }
  else { count = 0; target = recursive; }

  let pass = 0, attempts = 0, improvements = 0;

  while (count < target) {
    pass++;
    let improvedThisPass = false;

    // generate all (i, j) pairs as Python does
    const n = cityList[0].length;
    const allPairs = [];
    for (let i = 0; i < n; i++)
      for (let j = i + 1; j < n + (i > 0 ? 1 : 0); j++)
        allPairs.push([i, j]);

    // sample
    const k = Math.min(search, allPairs.length);
    for (let i = allPairs.length - 1; i > 0; i--) {
      const r = Math.floor(rng() * (i + 1));
      [allPairs[i], allPairs[r]] = [allPairs[r], allPairs[i]];
    }
    const pairs = allPairs.slice(0, k);

    for (const [i, j] of pairs) {
      attempts++;
      const cand = cityList[0].slice();
      const seg = cand.slice(i, j + 1).reverse();
      for (let s = 0; s < seg.length; s++) cand[i + s] = seg[s];
      const closed = close(cand);
      const d = distanceCalc(distanceMatrix, closed);
      if (d < cityList[1]) {
        cityList = [cand, d];
        improvedThisPass = true;
        improvements++;
        yield {
          phase: 'improvement',
          tour: closed, bestTour: closed,
          distance: d, bestDistance: d,
          highlight: { type: '2opt-segment', i, j, tour: closed, color: '#7dd594' },
          iteration: pass, attempts, improvements,
          message: `swap (${i},${j}): ${d.toFixed(2)}`,
        };
      }
    }

    if (!improvedThisPass) {
      yield { phase: 'pass-done',
              tour: close(cityList[0]), bestTour: close(cityList[0]),
              distance: cityList[1], bestDistance: cityList[1],
              iteration: pass, attempts, improvements,
              message: `pass ${pass}: no improvement` };
    }
    count++;
    if (priorBest > cityList[1] && recursive < 0) { priorBest = cityList[1]; count = -2; target = -1; }
    else if (cityList[1] >= priorBest && recursive < 0) { count = -1; target = -2; }
  }

  return { tour: close(cityList[0]), distance: cityList[1],
           summary: `2-opt-stoch: ${cityList[1].toFixed(2)} (${improvements}/${attempts})` };
}
