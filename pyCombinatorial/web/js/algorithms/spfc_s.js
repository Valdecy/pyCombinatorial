// ============================================================================
// spfc_s.js — Space-Filling Curve (Sierpinski)
// Mirrors algorithm/spfc_s.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'spfc_s',
  label: 'SFC — Sierpinski',
  category: 'Constructive',
  description: 'Sort cities by Sierpinski curve index.',
  needsCoords: true,
  params: [],
};

function sierpinskiIdx(x, y, size) {
  let result = 0, idx = size;
  if (x > y) { result += 1; x = size - x; y = size - y; }
  while (idx > 0) {
    result += result;
    if (x + y > size) {
      result += 1;
      const xs = x;
      x = size - y; y = xs;
    }
    x = 2 * x; y = 2 * y;
    result = 2 * result;
    if (y > size) {
      result += 1;
      const xs = x;
      x = y - size; y = size - xs;
    }
    idx = (idx / 2) | 0;
  }
  return result;
}

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  const flag = coords.some(([x, y]) => x !== Math.floor(x) || y !== Math.floor(y));
  const scaled = coords.map(([x, y]) => flag ? [Math.round(x * 100), Math.round(y * 100)] : [x | 0, y | 0]);
  let mnx = Infinity, mny = Infinity;
  for (const [x, y] of scaled) { if (x < mnx) mnx = x; if (y < mny) mny = y; }
  const shifted = scaled.map(([x, y]) => [x - Math.min(0, mnx), y - Math.min(0, mny)]);
  let mx = 1;
  for (const [x, y] of shifted) { if (x > mx) mx = x; if (y > mx) mx = y; }
  const idxs = shifted.map(([x, y]) => sierpinskiIdx(x, y, mx + 1));
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => idxs[a] - idxs[b]);

  const tourSoFar = [];
  for (let i = 0; i < order.length; i++) {
    tourSoFar.push(order[i] + 1);
    if (i % Math.max(1, Math.floor(n / 30)) === 0 || i === order.length - 1) {
      const t = [...tourSoFar];
      if (t.length > 1) t.push(t[0]);
      yield { phase: 'build', tour: t, bestTour: t,
              distance: t.length > 2 ? distanceCalc(distanceMatrix, t) : 0,
              bestDistance: NaN, iteration: i, currentCity: order[i],
              message: `${i + 1}/${n}` };
    }
  }
  const tour = [...order.map(c => c + 1), order[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Sierpinski SFC: ${distance.toFixed(2)}` };
}
