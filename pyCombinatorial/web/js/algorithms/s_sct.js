// ============================================================================
// s_sct.js — Scatter Search
// Mirrors algorithm/s_sct.py — population of tours; combine via order-crossover
// + segment-reversal/scramble; refine with single-pass 2-opt.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng, shuffle } from '../core/seed.js';

export const meta = {
  id: 's_sct',
  label: 'Scatter Search',
  category: 'Metaheuristic',
  description: 'Population of tours; recombine via OX-style crossover with segment reversal/scramble.',
  params: [
    { key: 'iterations',     label: 'Iterations',     type: 'int',   default: 50, min: 1, max: 500 },
    { key: 'referenceSize',  label: 'Reference size', type: 'int',   default: 25, min: 4, max: 200 },
    { key: 'reverseProb',    label: 'Reverse prob',   type: 'float', default: 0.5, min: 0, max: 1, step: 0.05 },
    { key: 'scrambleProb',   label: 'Scramble prob',  type: 'float', default: 0.3, min: 0, max: 1, step: 0.05 },
    { key: 'seed',           label: 'Random seed',    type: 'int',   default: 42, min: 0, max: 99999 },
  ],
};

function singlePass2Opt(distanceMatrix, tour) {
  let cl = [tour.slice(), distanceCalc(distanceMatrix, tour)];
  for (let i = 0; i < cl[0].length - 2; i++) {
    for (let j = i + 1; j < cl[0].length - 1; j++) {
      const cand = cl[0].slice();
      const seg = cand.slice(i, j + 1).reverse();
      for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
      cand[cand.length - 1] = cand[0];
      const d = distanceCalc(distanceMatrix, cand);
      if (d < cl[1]) cl = [cand, d];
    }
  }
  return cl;
}

function crossover(distanceMatrix, refList, reverseProb, scrambleProb, rng) {
  const ix = Math.floor(rng() * refList.length);
  let iy = Math.floor(rng() * refList.length);
  if (iy === ix) iy = (iy + 1) % refList.length;
  let p1 = refList[ix][0].slice(0, -1);
  let p2 = refList[iy][0].slice(0, -1);

  let i = Math.floor(rng() * p1.length), j = Math.floor(rng() * p1.length);
  if (i > j) [i, j] = [j, i];
  if (rng() < reverseProb) {
    const seg = p1.slice(i, j + 1).reverse();
    for (let k = 0; k < seg.length; k++) p1[i + k] = seg[k];
  }
  const window = p1.slice(i, j + 1);
  const inside = new Set(window);
  const offspring = new Array(p1.length).fill(0);
  for (let k = i; k <= j; k++) offspring[k] = p1[k];
  let p2f = p2.filter(x => !inside.has(x));
  if (rng() < scrambleProb) shuffle(p2f, rng);
  let cnt = 0;
  for (let k = 0; k < offspring.length; k++) {
    if (offspring[k] === 0) { offspring[k] = p2f[cnt++]; }
  }
  offspring.push(offspring[0]);
  return [offspring, distanceCalc(distanceMatrix, offspring)];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);

  const refSize = params.referenceSize ?? 25;
  const refList = [];
  for (let i = 0; i < refSize; i++) refList.push(seedFunction(distanceMatrix, rng));
  refList.sort((a, b) => a[1] - b[1]);
  if (refList[0][1] < best[1]) best = [refList[0][0].slice(), refList[0][1]];

  yield {
    phase: 'init', tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0, message: `pop ${refSize}, start ${best[1].toFixed(2)}`,
  };

  const iterations = params.iterations ?? 50;
  const rev = params.reverseProb ?? 0.5;
  const scr = params.scrambleProb ?? 0.3;

  for (let it = 0; it < iterations; it++) {
    const cands = [];
    for (let i = 0; i < refSize; i++) cands.push(crossover(distanceMatrix, refList, rev, scr, rng));
    for (let i = 0; i < cands.length; i++) cands[i] = singlePass2Opt(distanceMatrix, cands[i][0]);
    refList.push(...cands);
    refList.sort((a, b) => a[1] - b[1]);
    refList.length = refSize;

    const improved = refList[0][1] < best[1];
    if (improved) best = [refList[0][0].slice(), refList[0][1]];
    yield {
      phase: improved ? 'improvement' : 'generation',
      tour: refList[0][0], bestTour: best[0],
      distance: refList[0][1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${refList[0][1].toFixed(2)}` : `gen ${it + 1}: ${refList[0][1].toFixed(2)}`,
    };
  }
  return { tour: best[0], distance: best[1], summary: `Scatter Search: ${best[1].toFixed(2)}` };
}
