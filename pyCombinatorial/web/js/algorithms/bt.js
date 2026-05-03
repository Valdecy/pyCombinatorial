// ============================================================================
// bt.js — Bitonic Tour (Dynamic Programming)
// Mirrors algorithm/bt.py — DP over x-sorted points; tour goes strictly right
// then strictly left.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'bt',
  label: 'Bitonic Tour',
  category: 'Exact',
  description: 'DP over x-sorted points (strictly-monotone-x tour). Optimal among bitonic tours.',
  needsCoords: true,
  params: [],
};

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  if (n < 3) return { tour: null, distance: 0, summary: 'too few cities' };

  const sortedIdx = Array.from({ length: n }, (_, i) => i).sort((a, b) => coords[a][0] - coords[b][0]);
  const ds = (a, b) => distanceMatrix[sortedIdx[a]][sortedIdx[b]];

  const dp = Array.from({ length: n }, () => new Float64Array(n).fill(Infinity));
  const parent = Array.from({ length: n }, () => new Array(n).fill(null));
  dp[0][1] = ds(0, 1);

  yield { phase: 'sort', iteration: 0, bestDistance: NaN,
          message: `sorted by x; building DP table…` };

  for (let j = 2; j < n; j++) {
    for (let i = 0; i < j; i++) {
      if (i === 0) {
        dp[0][j] = dp[0][j - 1] + ds(j - 1, j);
        parent[0][j] = [0, j - 1];
      } else {
        let bestV = Infinity, bestK = null;
        for (let k = 0; k < i; k++) {
          const cand = dp[k][i] + ds(k, j);
          if (cand < bestV) { bestV = cand; bestK = k; }
        }
        dp[i][j] = bestV;
        parent[i][j] = [bestK, i];
      }
    }
    if (j % Math.max(1, Math.floor(n / 25)) === 0 || j === n - 1) {
      yield { phase: 'dp', iteration: j, bestDistance: NaN,
              message: `DP column ${j + 1}/${n}` };
    }
  }

  const distance = dp[0][n - 1] + ds(0, n - 1);
  let routeIdx = [n - 1];
  let i = 0, j = n - 1;
  while (true) {
    const p = parent[i][j];
    if (p == null) { routeIdx.push(i); break; }
    routeIdx.push(p[1]);
    [i, j] = p;
  }
  routeIdx.reverse();
  const tour = [...routeIdx.map(k => sortedIdx[k] + 1), sortedIdx[routeIdx[0]] + 1];
  const tourDist = distanceCalc(distanceMatrix, tour);

  yield { phase: 'recover', tour, bestTour: tour,
          distance: tourDist, bestDistance: tourDist,
          iteration: n, message: `tour reconstructed: ${tourDist.toFixed(2)}` };

  return { tour, distance: tourDist, summary: `Bitonic Tour: ${tourDist.toFixed(2)} (DP optimum: ${distance.toFixed(2)})` };
}
