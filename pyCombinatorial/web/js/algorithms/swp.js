// ============================================================================
// swp.js — Sweep
// Mirrors algorithm/swp.py — sort cities by polar angle around a pivot city.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'swp',
  label: 'Sweep',
  category: 'Constructive',
  description: 'Sort cities by polar angle around a pivot city; tour visits them in order.',
  needsCoords: true,
  params: [
    { key: 'initialLocation', label: 'Pivot city', type: 'int', default: 0, min: -1, max: 999,
      hint: '-1 = try all pivots, keep the best.' },
  ],
};

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const initial = params.initialLocation ?? 0;
  const pivots = initial === -1
    ? Array.from({ length: n }, (_, i) => i)
    : [Math.max(0, Math.min(n - 1, initial))];

  let bestTour = null, bestDist = Infinity;

  for (const piv of pivots) {
    const px = coords[piv][0], py = coords[piv][1];
    // (rho, phi) per city using: rho = d(pivot, j),  phi = atan((y-py)/(x-px))
    const items = [];
    for (let j = 0; j < n; j++) {
      const dx = coords[j][0] - px, dy = coords[j][1] - py;
      let phi = Math.atan(dy / (dx === 0 ? 1e-15 : dx));
      if (!Number.isFinite(phi)) phi = 0;
      items.push({ id: j, phi });
    }
    items.sort((a, b) => a.phi - b.phi);
    const tour = [...items.map(c => c.id + 1)];
    tour.push(tour[0]);
    const d = distanceCalc(distanceMatrix, tour);

    yield { phase: 'build', tour: [...tour], bestTour: bestTour,
            distance: d, bestDistance: bestDist,
            iteration: pivots.indexOf(piv), currentCity: piv,
            message: `pivot ${piv + 1}: ${d.toFixed(2)}` };

    if (d < bestDist) {
      bestDist = d; bestTour = [...tour];
      yield { phase: 'improvement', tour: [...tour], bestTour: [...tour],
              distance: d, bestDistance: d,
              iteration: pivots.indexOf(piv),
              message: `pivot ${piv + 1}: new best ${d.toFixed(2)}` };
    }
  }

  return { tour: bestTour, distance: bestDist, summary: `Sweep best: ${bestDist.toFixed(2)}` };
}
