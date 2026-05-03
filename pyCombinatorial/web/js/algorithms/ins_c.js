// ============================================================================
// ins_c.js — Cheapest Insertion
// Mirrors algorithm/ins_c.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { argMax, cheapestInsertionPos } from './_shared.js';

export const meta = {
  id: 'ins_c',
  label: 'Cheapest Insertion',
  category: 'Constructive',
  description: 'Start with the two farthest cities; insert each remaining city at the position of minimum cost increase.',
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;

  // start with the pair of cities maximizing distance
  let i0 = 0, j0 = 1, mx = -Infinity;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++)
      if (distanceMatrix[i][j] > mx) { mx = distanceMatrix[i][j]; i0 = i; j0 = j; }

  const tour0 = [i0, j0];
  const inTour = new Array(n).fill(false);
  inTour[i0] = true; inTour[j0] = true;

  const out = () => {
    const t = [...tour0.map(c => c + 1), tour0[0] + 1];
    return { tour: t, bestTour: t, distance: distanceCalc(distanceMatrix, t),
             bestDistance: distanceCalc(distanceMatrix, t) };
  };

  yield { phase: 'init', ...out(), iteration: 0,
          message: `seed: cities ${i0 + 1} ↔ ${j0 + 1} (Δ ${mx.toFixed(2)})` };

  let count = 0;
  while (tour0.length < n) {
    let bestCity = -1, bestPos = 1, bestDelta = Infinity;
    for (let k = 0; k < n; k++) {
      if (inTour[k]) continue;
      const r = cheapestInsertionPos(distanceMatrix, tour0, k);
      if (r.delta < bestDelta) { bestDelta = r.delta; bestCity = k; bestPos = r.pos; }
    }
    tour0.splice(bestPos, 0, bestCity);
    inTour[bestCity] = true;
    count++;
    yield { phase: 'insert', ...out(), iteration: count,
            highlight: { type: 'edge', from: tour0[(bestPos - 1 + tour0.length) % tour0.length], to: bestCity },
            message: `insert ${bestCity + 1} (Δ ${bestDelta.toFixed(2)})` };
  }

  const tour = [...tour0.map(c => c + 1), tour0[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Cheapest Insertion: ${distance.toFixed(2)}` };
}
