// ============================================================================
// ksp.js — Karp-Steele Patching
// Mirrors algorithm/ksp.py — solve assignment problem (Hungarian), get cycles,
// patch them pairwise into a single Hamiltonian tour.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { linearSumAssignment, assignmentCycles, patchCycles } from './_ksp_helpers.js';

export const meta = {
  id: 'ksp',
  label: 'Karp-Steele Patching',
  category: 'Constructive',
  description: 'Solve the assignment problem; patch the resulting cycles greedily into a Hamiltonian tour.',
  warnIf: { citiesAbove: 100, message: 'Hungarian assignment is O(n³); slow for n > 100.' },
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  if (n < 3) return { tour: null, distance: 0, summary: 'too few cities' };

  // build cost matrix with diagonal forbidden (sum of all entries forbids self-loops)
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
  cycles.sort((a, b) => b.length - a.length);

  yield {
    phase: 'cycles',
    iteration: 2, bestDistance: NaN,
    extraEdges: r2c.map((c, i) => ({ a: i, b: c, color: '#5dd5e6', alpha: 0.4 })),
    message: `${cycles.length} cycles to patch`,
  };

  let route = cycles[0];
  for (let i = 1; i < cycles.length; i++) {
    const [merged, mergedDist] = patchCycles(route, cycles[i], distanceMatrix);
    route = merged;
    const t = [...route.map(c => c + 1), route[0] + 1];
    yield {
      phase: 'patch',
      tour: t, bestTour: t,
      distance: distanceCalc(distanceMatrix, t),
      bestDistance: distanceCalc(distanceMatrix, t),
      iteration: i + 2,
      message: `patched cycle ${i + 1}, |route|=${route.length}`,
    };
  }

  const tour = [...route.map(c => c + 1), route[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Karp-Steele Patching: ${distance.toFixed(2)}` };
}
