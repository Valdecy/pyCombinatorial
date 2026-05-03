// ============================================================================
// tbb.js — Truncated Branch & Bound (greedy reduced-cost insertion)
// Mirrors algorithm/tbb.py — Hungarian-style row/column reduction; pick the
// lowest reduced-cost extension at each step. Single-pass (no backtrack).
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'tbb',
  label: 'Truncated B&B',
  category: 'Constructive',
  description: 'Greedy reduced-cost matrix walk with row/column reduction (no backtracking).',
  params: [],
};

function reduceMatrix(M, n) {
  let totalReduction = 0;
  for (let i = 0; i < n; i++) {
    let mn = Infinity;
    for (let j = 0; j < n; j++) if (M[i][j] < mn) mn = M[i][j];
    if (mn !== Infinity && mn !== 0) {
      for (let j = 0; j < n; j++) if (M[i][j] !== Infinity) M[i][j] -= mn;
      totalReduction += mn;
    } else if (mn === Infinity) {
      // row already saturated, skip
    }
  }
  for (let j = 0; j < n; j++) {
    let mn = Infinity;
    for (let i = 0; i < n; i++) if (M[i][j] < mn) mn = M[i][j];
    if (mn !== Infinity && mn !== 0) {
      for (let i = 0; i < n; i++) if (M[i][j] !== Infinity) M[i][j] -= mn;
      totalReduction += mn;
    }
  }
  return totalReduction;
}

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  const dist = distanceMatrix.map(r => Array.from(r));
  for (let i = 0; i < n; i++) dist[i][i] = Infinity;
  let cost = reduceMatrix(dist, n);

  let k = 0;
  const route0 = [k];
  const remaining = new Set(Array.from({ length: n }, (_, i) => i));
  remaining.delete(k);
  let count = 0;

  while (remaining.size > 0) {
    let bestI = -1, bestC = Infinity;
    const remArr = [...remaining];
    for (const i of remArr) {
      // simulate going k → i
      const reduced = dist.map(r => [...r]);
      for (let j = 0; j < n; j++) reduced[k][j] = Infinity;
      for (let j = 0; j < n; j++) reduced[j][i] = Infinity;
      reduced[i][k] = Infinity;
      const sub = reduceMatrix(reduced, n);
      const total = cost + dist[k][i] + sub;
      if (total < bestC) { bestC = total; bestI = i; }
    }
    cost = bestC;
    for (let j = 0; j < n; j++) dist[k][j] = Infinity;
    for (let j = 0; j < n; j++) dist[j][bestI] = Infinity;
    k = bestI;
    route0.push(k);
    remaining.delete(k);
    count++;

    if (count % Math.max(1, Math.floor(n / 30)) === 0 || remaining.size === 0) {
      const t = [...route0.map(c => c + 1)];
      if (t.length > 1) t.push(t[0]);
      yield {
        phase: 'extend',
        tour: t.length > 2 ? t : null,
        bestTour: t.length > 2 ? t : null,
        distance: t.length > 2 ? distanceCalc(distanceMatrix, t) : 0,
        bestDistance: NaN,
        iteration: count,
        currentCity: k,
        message: `extend to ${k + 1} (lb ≈ ${cost.toFixed(2)})`,
      };
    }
  }

  const tour = [...route0.map(c => c + 1), route0[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Truncated B&B: ${distance.toFixed(2)}` };
}
