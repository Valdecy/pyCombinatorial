// ============================================================================
// ins_n.js — Nearest Insertion
// Mirrors algorithm/ins_n.py — uses 2-opt re-balance after each insertion.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { bestInsertion } from './_shared.js';

export const meta = {
  id: 'ins_n',
  label: 'Nearest Insertion',
  category: 'Constructive',
  description: 'Pick the city nearest to any current tour city; insert via best 2-opt position.',
  params: [
    { key: 'initialLocation', label: 'Start city', type: 'int', default: 0, min: -1, max: 999,
      hint: '0-indexed; -1 = try every start, keep the best.' },
  ],
};

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const initial = params.initialLocation ?? -1;
  const starts = initial === -1
    ? Array.from({ length: n }, (_, i) => i)
    : [Math.max(0, Math.min(n - 1, initial))];

  let bestTour = null, bestDist = Infinity;

  for (const i1 of starts) {
    const dist = distanceMatrix.map(r => Float64Array.from(r));
    for (let i = 0; i < n; i++) dist[i][i] = Infinity;

    let temp = [];
    let nextCity = -1, nd = Infinity;
    for (let j = 0; j < n; j++) if (dist[i1][j] < nd) { nd = dist[i1][j]; nextCity = j; }
    for (let j = 0; j < n; j++) { dist[i1][j] = Infinity; dist[j][i1] = Infinity; }
    temp.push(i1, nextCity);

    yield {
      phase: 'init',
      tour: [...temp.map(c => c + 1), temp[0] + 1],
      bestTour: bestTour,
      distance: distanceCalc(distanceMatrix, [...temp.map(c => c + 1), temp[0] + 1]),
      bestDistance: bestDist,
      iteration: 0,
      message: `start ${i1 + 1} → ${nextCity + 1}`,
    };

    for (let it = 0; it < n - 2; it++) {
      const i2 = nextCity;
      let nx = -1, nxd = Infinity;
      for (let j = 0; j < n; j++) if (dist[i2][j] < nxd) { nxd = dist[i2][j]; nx = j; }
      for (let j = 0; j < n; j++) { dist[i2][j] = Infinity; dist[j][i2] = Infinity; }
      temp.push(nx);
      temp = bestInsertion(distanceMatrix, temp);
      nextCity = nx;

      const t = [...temp.map(c => c + 1), temp[0] + 1];
      yield {
        phase: 'insert',
        tour: t,
        bestTour: bestTour,
        distance: distanceCalc(distanceMatrix, t),
        bestDistance: bestDist,
        iteration: it + 1,
        currentCity: nx,
        message: `add ${nx + 1}, re-balance`,
      };
    }

    const t = [...temp.map(c => c + 1), temp[0] + 1];
    const d = distanceCalc(distanceMatrix, t);
    if (d < bestDist) {
      bestDist = d;
      bestTour = t;
      yield { phase: 'improvement', tour: t, bestTour: t, distance: d, bestDistance: d,
              iteration: starts.indexOf(i1), message: `start ${i1 + 1}: new best ${d.toFixed(2)}` };
    }
  }

  return { tour: bestTour, distance: bestDist, summary: `Nearest Insertion best: ${bestDist.toFixed(2)}` };
}
