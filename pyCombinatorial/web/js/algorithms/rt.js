// ============================================================================
// rt.js — Random Tour Search
// Mirrors algorithm/rt.py — sample random tours, keep the best.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { randomTour, mulberry32 } from './_shared.js';

export const meta = {
  id: 'rt',
  label: 'Random Tour Search',
  category: 'Constructive',
  description: 'Sample N random permutations; keep the best tour found.',
  params: [
    { key: 'search', label: 'Samples', type: 'int', default: 25, min: 1, max: 10000 },
    { key: 'seed',   label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const rng = mulberry32(params.seed ?? 42);
  const search = Math.max(1, params.search ?? 25);

  let bestTour = null, bestDist = Infinity;
  for (let it = 0; it < search; it++) {
    const t = randomTour(n, rng);
    const d = distanceCalc(distanceMatrix, t);
    const improved = d < bestDist;
    if (improved) { bestDist = d; bestTour = t; }
    yield {
      phase: improved ? 'improvement' : 'sample',
      tour: t, bestTour: bestTour,
      distance: d, bestDistance: bestDist,
      iteration: it + 1,
      message: improved ? `★ ${d.toFixed(2)} (best)` : `${d.toFixed(2)}  best ${bestDist.toFixed(2)}`,
    };
  }
  return { tour: bestTour, distance: bestDist, summary: `Random Tour best: ${bestDist.toFixed(2)} over ${search} samples` };
}
