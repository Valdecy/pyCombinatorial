// ============================================================================
// s_tabu.js — Tabu Search (simplified)
// Mirrors the structure of algorithm/s_tabu.py — short-term memory of recently
// reversed edge pairs, periodic diversification via 4-opt kick.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng, shuffle } from '../core/seed.js';
import { localSearch2Opt, perturb4opt } from './_shared.js';

export const meta = {
  id: 's_tabu',
  label: 'Tabu Search',
  category: 'Local search',
  description: 'Short-term memory blocks recently-used edge swaps; periodic diversification.',
  params: [
    { key: 'iterations',  label: 'Iterations',  type: 'int', default: 100, min: 1, max: 5000 },
    { key: 'tabuTenure',  label: 'Tabu tenure', type: 'int', default: 20,  min: 1, max: 200 },
    { key: 'seed',        label: 'Random seed', type: 'int', default: 42,  min: 0, max: 99999 },
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
  return [cand, distanceCalc(distanceMatrix, cand), [cand[i], cand[j]].sort()];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let cur = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let best = [cur[0].slice(), cur[1]];

  const tabu = [];   // queue of [a,b] keys
  const tabuSet = new Set();
  const tenure = params.tabuTenure ?? 20;
  const iterations = params.iterations ?? 100;

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `start ${best[1].toFixed(2)}`,
  };

  let noImprove = 0;
  for (let it = 0; it < iterations; it++) {
    // intensify with full 2-opt
    const [t2, d2] = localSearch2Opt(distanceMatrix, cur[0]);
    cur = [t2, d2];

    // pick the best non-tabu neighbour (sample 25 random swaps)
    let pickedCand = null;
    for (let s = 0; s < 25; s++) {
      const c = stoch2opt(distanceMatrix, cur[0], rng);
      const k = `${c[2][0]}-${c[2][1]}`;
      if (tabuSet.has(k) && c[1] >= best[1]) continue;     // tabu unless aspiration
      if (!pickedCand || c[1] < pickedCand[1]) pickedCand = [c[0], c[1], k];
    }
    if (pickedCand) {
      cur = [pickedCand[0], pickedCand[1]];
      tabu.push(pickedCand[2]); tabuSet.add(pickedCand[2]);
      while (tabu.length > tenure) {
        const k = tabu.shift();
        tabuSet.delete(k);
      }
    }

    const improved = cur[1] < best[1];
    if (improved) { best = [cur[0].slice(), cur[1]]; noImprove = 0; }
    else noImprove++;

    // diversification trigger
    if (noImprove > 0 && noImprove % Math.max(1, Math.floor(iterations / 5)) === 0) {
      cur = perturb4opt(distanceMatrix, cur[0], rng);
      noImprove = 0;
      yield {
        phase: 'diversify',
        tour: cur[0], bestTour: best[0],
        distance: cur[1], bestDistance: best[1],
        iteration: it + 1, message: `diversify → ${cur[1].toFixed(2)}`,
      };
      continue;
    }

    yield {
      phase: improved ? 'improvement' : 'tabu-step',
      tour: cur[0], bestTour: best[0],
      distance: cur[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${cur[1].toFixed(2)}` : `${cur[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `Tabu Search: ${best[1].toFixed(2)}` };
}
