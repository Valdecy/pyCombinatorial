// ============================================================================
// frnn.js — Fixed-Radius Near-Neighbor 2-opt
// Mirrors algorithm/frnn.py — uses radial neighbour search instead of KDTree.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'frnn',
  label: 'Fixed-Radius NN 2-opt',
  category: 'Local search',
  description: 'Restrict 2-opt swap candidates to neighbours within a fixed radius.',
  needsCoords: true,
  params: [
    { key: 'ratio', label: 'Radius ratio', type: 'float', default: 1.5, min: 0.1, max: 10, step: 0.1,
      hint: 'Multiplier on the average pairwise distance.' },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const rng = mulberry32(params.seed ?? 42);

  // initial random tour
  const route = Array.from({ length: n }, (_, i) => i);
  for (let i = route.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [route[i], route[j]] = [route[j], route[i]];
  }
  let tour = [...route.map(c => c + 1), route[0] + 1];
  let dist = distanceCalc(distanceMatrix, tour);

  // mean pairwise euclidean distance
  let s = 0, cnt = 0;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++) {
      const dx = coords[i][0] - coords[j][0], dy = coords[i][1] - coords[j][1];
      s += Math.hypot(dx, dy); cnt++;
    }
  const r = (cnt > 0 ? s / cnt : 1) * (params.ratio ?? 1.5);

  yield { phase: 'init', tour: [...tour], bestTour: [...tour], distance: dist, bestDistance: dist,
          iteration: 0, message: `radius=${r.toFixed(2)}, dist=${dist.toFixed(2)}` };

  let improved = true, pass = 0;
  while (improved) {
    improved = false; pass++;
    for (let i = 0; i < n - 1; i++) {
      const ci = coords[route[i]];
      // find neighbours within radius
      for (let j = i + 1; j < n; j++) {
        const cj = coords[route[j]];
        const dx = ci[0] - cj[0], dy = ci[1] - cj[1];
        if (Math.hypot(dx, dy) > r) continue;

        const newRoute = route.slice();
        const seg = newRoute.slice(i, j + 1).reverse();
        for (let k = 0; k < seg.length; k++) newRoute[i + k] = seg[k];
        const newTour = [...newRoute.map(c => c + 1), newRoute[0] + 1];
        const newDist = distanceCalc(distanceMatrix, newTour);
        if (newDist < dist) {
          for (let k = 0; k < n; k++) route[k] = newRoute[k];
          tour = newTour; dist = newDist; improved = true;
          yield { phase: 'improvement', tour: [...tour], bestTour: [...tour],
                  distance: dist, bestDistance: dist, iteration: pass,
                  highlight: { type: '2opt-segment', i, j, tour: [...tour], color: '#7dd594' },
                  message: `swap (${i},${j}) → ${dist.toFixed(2)}` };
        }
      }
    }
    yield { phase: 'pass-done', tour: [...tour], bestTour: [...tour],
            distance: dist, bestDistance: dist, iteration: pass,
            message: improved ? `pass ${pass} done` : `pass ${pass}: no improvement` };
  }

  return { tour, distance: dist, summary: `FRNN: ${dist.toFixed(2)}` };
}
