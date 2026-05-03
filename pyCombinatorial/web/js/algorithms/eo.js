// ============================================================================
// eo.js — Extremal Optimization
// Mirrors algorithm/eo.py — rank-based τ-EO that swaps "worst" cities with
// random partners drawn from a power-law biased distribution.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';
import { seedFunction } from '../core/seed.js';

export const meta = {
  id: 'eo',
  label: 'Extremal Optimization',
  category: 'Metaheuristic',
  description: 'τ-EO: identify worst-positioned cities by rank; swap with power-law biased partner.',
  params: [
    { key: 'iterations', label: 'Iterations',  type: 'int',   default: 50,  min: 1, max: 5000 },
    { key: 'tau',        label: 'τ',           type: 'float', default: 1.8, min: 0.5, max: 5, step: 0.1 },
    { key: 'seed',       label: 'Random seed', type: 'int',   default: 42,  min: 0, max: 99999 },
  ],
};

function ranking(distanceMatrix, city, tau) {
  // returns array of [origDist, cityId(1-indexed), rank, prob, cumProb] sorted by cum prob
  const n = distanceMatrix.length;
  const rows = Array.from({ length: n }, (_, i) => [distanceMatrix[i][city], i + 1, 0, 0]);
  rows.sort((a, b) => a[0] - b[0]);
  for (let i = 0; i < n; i++) {
    rows[i][2] = i;
    rows[i][3] = i > 0 ? Math.pow(i, -tau) : 0;
  }
  let sum = 0;
  for (const r of rows) sum += r[3];
  for (const r of rows) r[3] /= sum;
  // sort by prob ascending; build CDF
  rows.sort((a, b) => a[3] - b[3]);
  for (let i = 1; i < n; i++) rows[i][3] += rows[i - 1][3];
  return rows;
}

function rouletteWheel(rank, cityTour, tau, rng) {
  // fitness rows: [city, prevCity, nextCity, score, prob]
  const n = cityTour.length - 1;
  const fitness = [];
  for (let i = 0; i < n; i++) {
    const city = cityTour[i];
    const prev = i === 0 ? cityTour[n - 1] : cityTour[i - 1];
    const next = cityTour[i + 1];
    fitness.push([city, prev, next, 0, 0]);
  }
  for (let i = 0; i < n; i++) {
    const left = rank.find(r => r[1] === fitness[i][1]);
    const right = rank.find(r => r[1] === fitness[i][2]);
    if (!left || !right) continue;
    fitness[i][3] = 3 / (left[2] + right[2] + 1e-12);
    fitness[i][4] = Math.pow(fitness[i][3], -tau);
  }
  let sum = 0;
  for (const f of fitness) sum += f[4];
  for (const f of fitness) f[4] /= sum + 1e-12;
  fitness.sort((a, b) => a[4] - b[4]);
  for (let i = 1; i < n; i++) fitness[i][4] += fitness[i - 1][4];

  let ix = 1, iy = -1, iz = -1, iw = 1;
  const r = rng();
  for (let i = 0; i < n; i++) {
    if (r <= fitness[i][4]) {
      ix = fitness[i][0];
      iw = fitness[i][0];
      const left = rank.find(rr => rr[1] === fitness[i][1]);
      const right = rank.find(rr => rr[1] === fitness[i][2]);
      if (left[0] > right[0]) { iy = fitness[i][1]; iz = -1; }
      else { iy = -1; iz = fitness[i][2]; }
      break;
    }
  }
  let safety = 0;
  while (ix === iw && safety < 200) {
    const r2 = rng();
    for (let i = 0; i < rank.length; i++) {
      if (r2 <= rank[i][3]) { iw = fitness[i] ? fitness[i][0] : iw; break; }
    }
    safety++;
  }
  return [iy, ix, iz, iw];
}

function exchange(distanceMatrix, cityTour, iy, ix, iz, iw) {
  const tour = cityTour.slice();
  const cur = cityTour.slice();
  const idxOf = c => cur.indexOf(c);
  const reverse = (arr, i, j) => {
    const seg = arr.slice(i, j + 1).reverse();
    for (let k = 0; k < seg.length; k++) arr[i + k] = seg[k];
    arr[arr.length - 1] = arr[0];
  };
  let cand = cur.slice();
  if (iy === -1 && idxOf(iw) < idxOf(ix)) {
    reverse(cand, idxOf(ix) - 1, idxOf(ix));
    reverse(cand, idxOf(iw), idxOf(ix) - 1);
  } else if (iy === -1 && idxOf(iw) > idxOf(ix)) {
    reverse(cand, idxOf(ix), idxOf(iw));
  } else if (iz === -1 && idxOf(iw) < idxOf(ix)) {
    reverse(cand, idxOf(iw), idxOf(ix));
  } else if (iz === -1 && idxOf(iw) > idxOf(ix)) {
    reverse(cand, idxOf(ix), idxOf(ix) + 1);
    reverse(cand, idxOf(ix) + 1, idxOf(iw));
  }
  const dCand = distanceCalc(distanceMatrix, cand);
  const dTour = distanceCalc(distanceMatrix, tour);
  if (dCand < dTour) return [cand, dCand];
  return [tour, dTour];
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const tau = params.tau ?? 1.8;
  const iterations = params.iterations ?? 50;

  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : seedFunction(distanceMatrix, rng);
  let cur = [best[0].slice(), best[1]];

  yield {
    phase: 'init',
    tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0,
    message: `τ=${tau}, start ${best[1].toFixed(2)}`,
  };

  const n = distanceMatrix.length;
  for (let it = 0; it < iterations; it++) {
    for (let i = 0; i < n; i++) {
      const rank = ranking(distanceMatrix, i, tau);
      const [iy, ix, iz, iw] = rouletteWheel(rank, cur[0], tau, rng);
      cur = exchange(distanceMatrix, cur[0], iy, ix, iz, iw);
    }
    const improved = cur[1] < best[1];
    if (improved) best = [cur[0].slice(), cur[1]];
    cur = [best[0].slice(), best[1]];   // restart from best (per Python)
    yield {
      phase: improved ? 'improvement' : 'iteration',
      tour: cur[0], bestTour: best[0],
      distance: cur[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${cur[1].toFixed(2)}` : `iter ${it + 1}: ${cur[1].toFixed(2)}`,
    };
  }

  return { tour: best[0], distance: best[1], summary: `EO: ${best[1].toFixed(2)}` };
}
