// ============================================================================
// cw.js — Clarke-Wright Savings
// Mirrors algorithm/cw.py — pair savings s(i,j) = d(i,0)+d(j,0)-d(i,j);
// extend a single route by always picking the pair with max remaining saving.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'cw',
  label: 'Clarke-Wright Savings',
  category: 'Constructive',
  description: 'Build one route greedily by maximum savings between endpoints and remaining nodes.',
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  const nodes = Array.from({ length: n }, (_, i) => i);
  const pairs = [];
  for (let i = 1; i < n - 1; i++)
    for (let j = i + 1; j < n; j++)
      pairs.push([nodes[i], nodes[j]]);
  const sav = pairs.map(([i, j]) => distanceMatrix[i][0] + distanceMatrix[j][0] - distanceMatrix[i][j]);

  // pick first pair (highest saving)
  let idx = 0; let mx = -Infinity;
  for (let i = 0; i < sav.length; i++) if (sav[i] > mx) { mx = sav[i]; idx = i; }
  let route = [...pairs[idx]];
  sav[idx] = -Infinity;

  yield { phase: 'init',
          tour: [...route.map(c => c + 1), route[0] + 1, 1, route[0] + 1],
          bestTour: null,
          distance: NaN, bestDistance: NaN,
          iteration: 0,
          message: `seed pair ${pairs[idx][0] + 1}-${pairs[idx][1] + 1} sav=${mx.toFixed(2)}` };

  // helper: index of pair (i,j) -> [min,max]
  const pairKey = (a, b) => `${Math.min(a, b)}-${Math.max(a, b)}`;
  const pairIdx = new Map();
  for (let p = 0; p < pairs.length; p++) pairIdx.set(pairKey(pairs[p][0], pairs[p][1]), p);

  while (route.length < n - 1) {
    const A = route[0], B = route[route.length - 1];

    // disable any pair that involves A or B paired with someone already in route
    if (route.length >= 3) {
      for (const i of route) {
        if (A !== i) { const k = pairIdx.get(pairKey(A, i)); if (k != null) sav[k] = -Infinity; }
        if (B !== i) { const k = pairIdx.get(pairKey(B, i)); if (k != null) sav[k] = -Infinity; }
      }
    }

    // build "memory": for each interior candidate node, its best saving paired with A or B
    let bestVal = -Infinity, bestCand = -1, prepend = true;
    for (let p = 0; p < pairs.length; p++) {
      if (sav[p] === -Infinity) continue;
      const [m, nn] = pairs[p];
      if (m === A) {
        if (sav[p] > bestVal && !route.includes(nn)) { bestVal = sav[p]; bestCand = nn; prepend = true; }
      } else if (nn === A) {
        if (sav[p] > bestVal && !route.includes(m)) { bestVal = sav[p]; bestCand = m; prepend = true; }
      } else if (m === B) {
        if (sav[p] > bestVal && !route.includes(nn)) { bestVal = sav[p]; bestCand = nn; prepend = false; }
      } else if (nn === B) {
        if (sav[p] > bestVal && !route.includes(m)) { bestVal = sav[p]; bestCand = m; prepend = false; }
      }
    }
    if (bestCand < 0) break;

    if (prepend) route.unshift(bestCand); else route.push(bestCand);
    const k = pairIdx.get(pairKey(prepend ? A : B, bestCand));
    if (k != null) sav[k] = -Infinity;

    const r1 = [0, ...route, 0].map(c => c + 1);
    yield { phase: 'extend',
            tour: r1,
            bestTour: r1,
            distance: distanceCalc(distanceMatrix, r1),
            bestDistance: NaN,
            iteration: route.length,
            currentCity: bestCand,
            message: `${prepend ? 'prepend' : 'append'} ${bestCand + 1} (sav ${bestVal.toFixed(2)})` };
  }

  const tour = [0, ...route, 0].map(c => c + 1);
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Clarke-Wright: ${distance.toFixed(2)}` };
}
