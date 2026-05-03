// ============================================================================
// spfc_h.js — Space-Filling Curve (Hilbert)
// Mirrors algorithm/spfc_h.py — sorts cities by Hilbert curve index.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'spfc_h',
  label: 'SFC — Hilbert',
  category: 'Constructive',
  description: 'Sort cities by their Hilbert curve index; tour visits in that order.',
  needsCoords: true,
  params: [],
};

const HILBERT_MAP = {
  a: { '00': [0, 'd'], '01': [1, 'a'], '10': [3, 'b'], '11': [2, 'a'] },
  b: { '00': [2, 'b'], '01': [1, 'b'], '10': [3, 'a'], '11': [0, 'c'] },
  c: { '00': [2, 'c'], '01': [3, 'd'], '10': [1, 'c'], '11': [0, 'b'] },
  d: { '00': [0, 'a'], '01': [3, 'c'], '10': [1, 'd'], '11': [2, 'd'] },
};

function hilbertIdx(x, y, size) {
  let curr = 'a', res = 0;
  for (let i = size - 1; i >= 0; i--) {
    res <<= 2;
    const qx = (x & (1 << i)) ? 1 : 0;
    const qy = (y & (1 << i)) ? 1 : 0;
    const [pos, next] = HILBERT_MAP[curr][`${qx}${qy}`];
    curr = next;
    res |= pos;
  }
  return res;
}

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;

  // detect non-integer coords; scale by 100 to handle floats
  const flag = coords.some(([x, y]) => x !== Math.floor(x) || y !== Math.floor(y));
  const scaled = coords.map(([x, y]) => flag ? [Math.round(x * 100), Math.round(y * 100)] : [x | 0, y | 0]);
  // also shift to nonneg
  let mnx = Infinity, mny = Infinity;
  for (const [x, y] of scaled) { if (x < mnx) mnx = x; if (y < mny) mny = y; }
  const shifted = scaled.map(([x, y]) => [x - Math.min(0, mnx), y - Math.min(0, mny)]);
  let mx = 1;
  for (const [x, y] of shifted) { if (x > mx) mx = x; if (y > mx) mx = y; }
  let k = 1, limit = 2;
  while (limit <= mx + 1) { limit <<= 1; k++; }

  const idxs = shifted.map(([x, y]) => hilbertIdx(x, y, k));
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => idxs[a] - idxs[b]);

  // animate the build
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
  return { tour, distance, summary: `Hilbert SFC: ${distance.toFixed(2)}` };
}
