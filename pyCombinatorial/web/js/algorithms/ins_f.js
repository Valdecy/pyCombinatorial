// ============================================================================
// ins_f.js — Farthest Insertion
// Mirrors algorithm/ins_f.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { cheapestInsertionPos } from './_shared.js';

export const meta = {
  id: 'ins_f',
  label: 'Farthest Insertion',
  category: 'Constructive',
  description: 'Repeatedly insert the city whose minimum distance to current tour is largest.',
  params: [
    { key: 'initialLocation', label: 'Start city', type: 'int', default: 0, min: -1, max: 999,
      hint: '-1 = try all starts.' },
  ],
};

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const initial = params.initialLocation ?? 0;
  const starts = initial === -1
    ? Array.from({ length: n }, (_, i) => i)
    : [Math.max(0, Math.min(n - 1, initial))];

  let bestTour = null, bestDist = Infinity;

  for (const i1 of starts) {
    // farthest from i1
    let idx = 0, mx = -Infinity;
    for (let j = 0; j < n; j++) if (j !== i1 && distanceMatrix[i1][j] > mx) { mx = distanceMatrix[i1][j]; idx = j; }
    const tour0 = [i1, idx];
    const inTour = new Set([i1, idx]);

    yield {
      phase: 'init',
      tour: [...tour0.map(c => c + 1), tour0[0] + 1],
      bestTour: bestTour,
      distance: distanceCalc(distanceMatrix, [...tour0.map(c => c + 1), tour0[0] + 1]),
      bestDistance: bestDist,
      iteration: 0,
      message: `start ${i1 + 1}, farthest ${idx + 1}`,
    };

    for (let it = 0; it < n - 2; it++) {
      // pick city u maximizing min(d(u, t)) for t in tour
      let bestU = -1, bestScore = -Infinity;
      for (let u = 0; u < n; u++) {
        if (inTour.has(u)) continue;
        let s = Infinity;
        for (const t of tour0) if (distanceMatrix[u][t] < s) s = distanceMatrix[u][t];
        if (s > bestScore) { bestScore = s; bestU = u; }
      }
      const r = cheapestInsertionPos(distanceMatrix, tour0, bestU);
      tour0.splice(r.pos, 0, bestU);
      inTour.add(bestU);

      const t = [...tour0.map(c => c + 1), tour0[0] + 1];
      yield {
        phase: 'insert',
        tour: t, bestTour: bestTour,
        distance: distanceCalc(distanceMatrix, t),
        bestDistance: bestDist,
        iteration: it + 1,
        currentCity: bestU,
        message: `pick ${bestU + 1} (score ${bestScore.toFixed(2)})`,
      };
    }

    const t = [...tour0.map(c => c + 1), tour0[0] + 1];
    const d = distanceCalc(distanceMatrix, t);
    if (d < bestDist) {
      bestDist = d; bestTour = t;
      yield { phase: 'improvement', tour: t, bestTour: t, distance: d, bestDistance: d,
              iteration: starts.indexOf(i1), message: `start ${i1 + 1}: best ${d.toFixed(2)}` };
    }
  }
  return { tour: bestTour, distance: bestDist, summary: `Farthest Insertion best: ${bestDist.toFixed(2)}` };
}
