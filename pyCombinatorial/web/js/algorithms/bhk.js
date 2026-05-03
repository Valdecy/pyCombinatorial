// ============================================================================
// bhk.js — Bellman-Held-Karp Dynamic Programming (exact)
// Mirrors algorithm/bhk.py — O(n²·2ⁿ) bitmask DP.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'bhk',
  label: 'Bellman-Held-Karp',
  category: 'Exact',
  description: 'Bitmask DP over subsets of cities. Optimal in O(n²·2ⁿ) time and memory.',
  warnIf: { citiesAbove: 18, message: 'memory grows as n·2ⁿ; > 18 cities will fail in browser.' },
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  if (n < 2) return { tour: null, distance: 0, summary: 'too few cities' };
  if (n > 20) return { tour: null, distance: 0, summary: 'BHK refused: n > 20 would exhaust memory' };

  // C[(bits, k)] = (min_cost, prev_node) where bits is subset including k, starting at 0
  // we store as Map<int, Map<int, [number, number]>> but flat 2D arrays are faster.
  // Index by bits * n + k. Note bits has bit 0 == "city 0 included" but city 0 is always the start
  // and not part of the bitmask in original; bits range over subsets of {1..n-1}.
  const totalBits = 1 << n;
  // Use sparse Map keyed by `bits * n + k` to keep memory tractable.
  const C = new Map();
  const key = (bits, k) => bits * n + k;

  // base: visit only city k (from 0)
  for (let k = 1; k < n; k++) {
    C.set(key(1 << k, k), [distanceMatrix[0][k], 0]);
  }

  yield {
    phase: 'init',
    iteration: 0, bestDistance: NaN,
    message: `BHK DP, n=${n}, table entries = ~${n * (1 << (n - 1))}`,
  };

  // build subsets of size j, j = 2..n-1 (matching the Python loop)
  for (let j = 2; j < n; j++) {
    // enumerate all combinations of j cities chosen from {1..n-1}
    const indices = [];
    const cur = [];
    function* combos(start, depth) {
      if (depth === j) { yield cur.slice(); return; }
      for (let i = start; i < n; i++) {
        cur.push(i); yield* combos(i + 1, depth + 1); cur.pop();
      }
    }
    let comboCount = 0;
    for (const subset of combos(1, 0)) {
      let bits = 0;
      for (const b of subset) bits |= (1 << b);
      for (const k of subset) {
        const prev = bits ^ (1 << k);
        let best = Infinity, bestM = -1;
        for (const m of subset) {
          if (m === 0 || m === k) continue;
          const c = C.get(key(prev, m));
          if (!c) continue;
          const cost = c[0] + distanceMatrix[m][k];
          if (cost < best) { best = cost; bestM = m; }
        }
        if (bestM >= 0) C.set(key(bits, k), [best, bestM]);
      }
      comboCount++;
    }
    yield {
      phase: 'dp',
      iteration: j, bestDistance: NaN,
      message: `subset size ${j}: ${comboCount} combinations`,
    };
  }

  // find optimal closing
  const allBits = ((1 << n) - 1) - 1;        // all bits set except bit 0
  let bestDist = Infinity, bestK = -1;
  for (let k = 1; k < n; k++) {
    const c = C.get(key(allBits, k));
    if (!c) continue;
    const total = c[0] + distanceMatrix[k][0];
    if (total < bestDist) { bestDist = total; bestK = k; }
  }

  // reconstruct
  let bits = allBits, k = bestK;
  const path = [];
  for (let i = 0; i < n - 1; i++) {
    path.push(k);
    const c = C.get(key(bits, k));
    const newBits = bits ^ (1 << k);
    bits = newBits;
    k = c[1];
  }
  path.reverse();
  const tour = [1, ...path.map(c => c + 1), 1];

  yield {
    phase: 'recover',
    tour, bestTour: tour,
    distance: bestDist, bestDistance: bestDist,
    iteration: n,
    message: `recovered tour: ${bestDist.toFixed(2)}`,
  };

  return { tour, distance: distanceCalc(distanceMatrix, tour),
           summary: `Bellman-Held-Karp: ${distanceCalc(distanceMatrix, tour).toFixed(2)}` };
}
