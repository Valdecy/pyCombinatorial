// ============================================================================
// gksp.js — Greedy Karp-Steele Patching
// Mirrors algorithm/gksp.py — at each step pick the cycle pair whose merge
// (followed by 2-opt refinement) yields the shortest tour.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { linearSumAssignment, assignmentCycles, patchCycles } from './_ksp_helpers.js';
import { localSearch2Opt } from './_shared.js';

export const meta = {
  id: 'gksp',
  label: 'Greedy Karp-Steele',
  category: 'Constructive',
  description: 'KSP variant: at each step pick the cycle-pair merge with the smallest 2-opt-refined tour.',
  warnIf: { citiesAbove: 60, message: 'O(c² × n²) per step; slow for many cycles.' },
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  if (n < 3) return { tour: null, distance: 0, summary: 'too few cities' };

  const sumAll = distanceMatrix.reduce((a, r) => a + r.reduce((b, v) => b + v, 0), 0);
  const cost = distanceMatrix.map((row, i) => row.map((v, j) => i === j ? sumAll : v));
  const r2c = linearSumAssignment(cost);

  yield {
    phase: 'assignment',
    iteration: 1, bestDistance: NaN,
    extraEdges: r2c.map((c, i) => ({ a: i, b: c, color: '#5dd5e6', alpha: 0.55 })),
    message: `solved assignment`,
  };

  let cycles = assignmentCycles(r2c);
  let route = [];
  let step = 1;

  while (cycles.length > 1 || (cycles.length === 1 && route.length < n)) {
    let bestI = 0, bestJ = 1, bestRoute = null, bestVal = Infinity;
    for (let i = 0; i < cycles.length; i++) {
      for (let j = i + 1; j < cycles.length; j++) {
        const [m, _] = patchCycles(cycles[i], cycles[j], distanceMatrix);
        const seedTour = [...m.map(c => c + 1), m[0] + 1];
        const [refined, refinedD] = localSearch2Opt(distanceMatrix, seedTour);
        if (refinedD < bestVal) {
          bestVal = refinedD; bestRoute = refined.slice(0, -1).map(c => c - 1);
          bestI = i; bestJ = j;
        }
      }
    }
    if (!bestRoute) {
      // single cycle remaining
      route = route.concat(cycles[0]); cycles.shift();
      break;
    }
    route = bestRoute;
    cycles.splice(bestJ, 1);
    cycles.splice(bestI, 1);
    cycles.unshift(route);   // treat the merged tour as a new "cycle"
    yield {
      phase: 'patch',
      tour: [...route.map(c => c + 1), route[0] + 1],
      bestTour: [...route.map(c => c + 1), route[0] + 1],
      distance: bestVal, bestDistance: bestVal,
      iteration: ++step,
      message: `merged → ${bestVal.toFixed(2)}, |route|=${route.length}`,
    };
    if (route.length === n) break;
  }

  if (route.length === 0 && cycles.length === 1) route = cycles[0];

  const closed = [...route.map(c => c + 1), route[0] + 1];
  const [final, finalD] = localSearch2Opt(distanceMatrix, closed);
  return { tour: final, distance: finalD, summary: `GKSP: ${finalD.toFixed(2)}` };
}
