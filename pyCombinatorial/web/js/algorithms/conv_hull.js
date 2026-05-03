// ============================================================================
// conv_hull.js — Convex Hull insertion
// Mirrors algorithm/conv_hull.py — hull cycle + cheapest-insertion of interior cities.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { convexHullIndices } from './_shared.js';

export const meta = {
  id: 'conv_hull',
  label: 'Convex Hull',
  category: 'Constructive',
  description: 'Hull cycle as initial tour; insert each interior city at minimum-ratio position.',
  needsCoords: true,
  params: [],
};

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const idx_h = convexHullIndices(coords);     // 0-indexed CCW
  const inside = [];
  const onHull = new Set(idx_h);
  for (let i = 0; i < n; i++) if (!onHull.has(i)) inside.push(i);

  yield {
    phase: 'init',
    tour: [...idx_h.map(c => c + 1), idx_h[0] + 1],
    bestTour: [...idx_h.map(c => c + 1), idx_h[0] + 1],
    distance: distanceCalc(distanceMatrix, [...idx_h.map(c => c + 1), idx_h[0] + 1]),
    bestDistance: NaN,
    iteration: 0,
    message: `hull: ${idx_h.length} cities, ${inside.length} inside`,
  };

  while (inside.length > 0) {
    // for each interior city L, find best (m,n) pair in hull with min cost ratio
    let chosenL = -1, chosenM = -1, chosenN = -1, chosenIns = -1, bestRatio = Infinity;
    for (const L of inside) {
      let bestVec1 = Infinity, bestPos = -1, bestVec2 = Infinity, bestM = -1, bestN = -1;
      for (let p = 0; p < idx_h.length; p++) {
        const m = idx_h[p], nn = idx_h[(p + 1) % idx_h.length];
        const c1 = distanceMatrix[m][L] + distanceMatrix[L][nn] - distanceMatrix[m][nn];
        const c2 = (distanceMatrix[m][L] + distanceMatrix[L][nn]) / (distanceMatrix[m][nn] + 1e-15);
        if (c1 < bestVec1) { bestVec1 = c1; bestPos = p; bestVec2 = c2; bestM = m; bestN = nn; }
      }
      if (bestVec2 < bestRatio) {
        bestRatio = bestVec2; chosenL = L; chosenM = bestM; chosenN = bestN; chosenIns = bestPos;
      }
    }
    inside.splice(inside.indexOf(chosenL), 1);
    idx_h.splice(chosenIns + 1, 0, chosenL);
    const tour = [...idx_h.map(c => c + 1), idx_h[0] + 1];
    yield { phase: 'insert', tour, bestTour: tour, distance: distanceCalc(distanceMatrix, tour),
            bestDistance: distanceCalc(distanceMatrix, tour), iteration: idx_h.length,
            currentCity: chosenL,
            message: `insert ${chosenL + 1} between ${chosenM + 1}-${chosenN + 1}` };
  }

  const tour = [...idx_h.map(c => c + 1), idx_h[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Convex Hull: ${distance.toFixed(2)}` };
}
