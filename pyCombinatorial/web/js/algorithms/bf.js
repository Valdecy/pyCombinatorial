// ============================================================================
// bf.js — Brute Force (exact)
// Mirrors algorithm/bf.py — enumerate all (n-1)!/2 permutations starting at 1.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'bf',
  label: 'Brute Force',
  category: 'Exact',
  description: 'Enumerate every (n-1)!/2 permutation. Optimal but factorial.',
  warnIf: { citiesAbove: 10, message: 'n! grows brutally; > 10 cities will hang.' },
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  if (n < 2) return { tour: null, distance: 0, summary: 'too few cities' };

  const rest = [];
  for (let i = 2; i <= n; i++) rest.push(i);

  let bestDist = Infinity, bestTour = null;
  let count = 0, totalAprox = 1;
  for (let i = 2; i <= n - 1; i++) totalAprox *= i;
  totalAprox = Math.floor(totalAprox / 2);

  function* permute(arr, start) {
    if (start === arr.length - 1) {
      yield arr.slice();
      return;
    }
    for (let i = start; i < arr.length; i++) {
      [arr[start], arr[i]] = [arr[i], arr[start]];
      yield* permute(arr, start + 1);
      [arr[start], arr[i]] = [arr[i], arr[start]];
    }
  }

  for (const perm of permute(rest, 0)) {
    // dedupe by canonical orientation: keep p <= reversed(p) as in Python
    let isCanon = true;
    for (let i = 0; i < perm.length; i++) {
      const a = perm[i], b = perm[perm.length - 1 - i];
      if (a < b) break;
      if (a > b) { isCanon = false; break; }
    }
    if (!isCanon) continue;

    const tour = [1, ...perm, 1];
    const d = distanceCalc(distanceMatrix, tour);
    count++;
    if (d < bestDist) {
      bestDist = d;
      bestTour = tour;
      yield {
        phase: 'improvement',
        tour, bestTour: tour,
        distance: d, bestDistance: bestDist,
        iteration: count,
        message: `★ ${d.toFixed(2)}  (${count}/${totalAprox})`,
      };
    } else if (count % Math.max(1, Math.floor(totalAprox / 50)) === 0) {
      yield {
        phase: 'enumerate',
        tour, bestTour: bestTour,
        distance: d, bestDistance: bestDist,
        iteration: count,
        message: `${count}/${totalAprox}  best ${bestDist.toFixed(2)}`,
      };
    }
  }

  return { tour: bestTour, distance: bestDist, summary: `Brute Force: ${bestDist.toFixed(2)} (${count} permutations)` };
}
