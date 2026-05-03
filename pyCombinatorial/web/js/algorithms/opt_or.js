// ============================================================================
// opt_or.js — Or-opt (chain insertion)
// Mirrors algorithm/opt_or.py — remove a chain of k consecutive cities;
// re-insert it at the best position; iterate.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 'opt_or',
  label: 'Or-opt',
  category: 'Local search',
  description: 'Or-opt: relocate chains of 1..k consecutive cities to better positions.',
  params: [
    { key: 'iterations',  label: 'Iterations',   type: 'int', default: 100, min: 1, max: 10000 },
    { key: 'chainLength', label: 'Max passes',   type: 'int', default: 3,   min: 1, max: 50 },
    { key: 'k1',          label: 'Min chain k',  type: 'int', default: 1,   min: 1, max: 20 },
    { key: 'k2',          label: 'Max chain k',  type: 'int', default: 5,   min: 1, max: 30 },
    { key: 'lambda',      label: 'λ filter',     type: 'float', default: 0.1, min: 0, max: 5, step: 0.01,
      hint: 'Larger = stricter gain threshold (skip more attempts).' },
    { key: 'vfMode',      label: 'VF mode',      type: 'bool', default: true },
    { key: 'seed',        label: 'Random seed',  type: 'int', default: 42,  min: 0, max: 99999 },
  ],
};

function totalDist(dm, route0) {
  let s = 0;
  for (let i = 1; i < route0.length; i++) s += dm[route0[i - 1]][route0[i]];
  return s;
}

function avgEdge(dm, n) {
  let s = 0, c = 0;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++) { s += dm[i][j]; c++; }
  return c > 0 ? s / c : 1;
}

function orOptPass(dm, route, params) {
  const k1 = params.k1, k2 = params.k2;
  const lambda = params['lambda'];
  const vf = params.vfMode;

  let cur = route.slice();
  let curDist = totalDist(dm, cur);
  const n = cur.length - 1;
  const ag = avgEdge(dm, n);

  const kSeq = [];
  for (let v = k2; v >= k1; v--) kSeq.push(v);
  const passes = Math.max(1, params.chainLength);
  let improvedAny = false;

  for (let p = 0; p < passes; p++) {
    let improvedPass = false;
    if (vf) {
      for (let i = 1; i < cur.length - 1; i++) {
        for (const k of kSeq) {
          if (i + k >= cur.length) continue;
          const i1 = cur[i - 1], i2 = cur[i], i3 = cur[i + k - 1], i4 = cur[i + k];
          const g = dm[i1][i2] + dm[i3][i4] - dm[i1][i4];
          const dBar = curDist / Math.max(1, n);
          const lBar = 2 * ag - dBar;
          if (g <= lambda * lBar) continue;
          const segment = cur.slice(i, i + k);
          const rem = cur.slice(0, i).concat(cur.slice(i + k));
          let moved = false;
          for (let j = 1; j < rem.length; j++) {
            const tmp = rem.slice(0, j).concat(segment, rem.slice(j));
            const cost = totalDist(dm, tmp);
            if (cost + 1e-12 < curDist) {
              cur = tmp; curDist = cost;
              improvedPass = true; improvedAny = true; moved = true;
              break;
            }
          }
          if (moved) break;
        }
      }
    } else {
      for (const k of kSeq) {
        let improvedK = true;
        while (improvedK) {
          improvedK = false;
          const last = cur.length - 1;
          for (let i = 1; i < last; i++) {
            if (i + k > last) continue;
            const i1 = cur[i - 1], i2 = cur[i], i3 = cur[i + k - 1], i4 = cur[i + k];
            const g = dm[i1][i2] + dm[i3][i4] - dm[i1][i4];
            const dBar = curDist / Math.max(1, n);
            const lBar = 2 * ag - dBar;
            if (g <= lambda * lBar) continue;
            const segment = cur.slice(i, i + k);
            const rem = cur.slice(0, i).concat(cur.slice(i + k));
            for (let j = 1; j < rem.length; j++) {
              const tmp = rem.slice(0, j).concat(segment, rem.slice(j));
              const cost = totalDist(dm, tmp);
              if (cost + 1e-12 < curDist) {
                cur = tmp; curDist = cost;
                improvedK = true; improvedAny = true;
                break;
              }
            }
            if (improvedK) break;
          }
        }
      }
    }
    if (!improvedPass) break;
  }
  return [cur, curDist, improvedAny];
}

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  // initial tour: provided or random
  let init;
  if (params._initialTour) {
    init = params._initialTour.slice();
  } else {
    init = seedFunction(distanceMatrix, rng)[0];
  }
  // route in 0-indexed open form
  let route0 = init.slice(0, -1).map(c => c - 1);
  route0.push(route0[0]);                // closed 0-indexed
  let dist = totalDist(distanceMatrix, route0);

  const close1 = r => [...r.slice(0, -1).map(c => c + 1), r[0] + 1];
  yield {
    phase: 'init',
    tour: close1(route0), bestTour: close1(route0),
    distance: dist, bestDistance: dist,
    iteration: 0, message: `start ${dist.toFixed(2)}`,
  };

  const iterations = Math.max(1, params.iterations ?? 100);
  let noImprove = 0;
  for (let it = 0; it < iterations; it++) {
    const [r2, d2, ok] = orOptPass(distanceMatrix, route0, {
      chainLength: params.chainLength ?? 3,
      k1: params.k1 ?? 1, k2: params.k2 ?? 5,
      'lambda': params['lambda'] ?? 0.1, vfMode: params.vfMode ?? true,
    });
    if (d2 < dist) {
      route0 = r2; dist = d2; noImprove = 0;
      yield {
        phase: 'improvement',
        tour: close1(route0), bestTour: close1(route0),
        distance: dist, bestDistance: dist,
        iteration: it + 1, message: `iter ${it + 1}: ${dist.toFixed(2)}`,
      };
    } else {
      noImprove++;
      yield {
        phase: 'pass-done',
        tour: close1(route0), bestTour: close1(route0),
        distance: dist, bestDistance: dist,
        iteration: it + 1, message: `iter ${it + 1}: no improvement`,
      };
    }
    if (noImprove >= 2) break;
  }

  return { tour: close1(route0), distance: dist, summary: `Or-opt: ${dist.toFixed(2)}` };
}
