// ============================================================================
// mf.js — Multi-Fragment Heuristic
// Mirrors algorithm/mf.py — greedy edge selection; merge edges into fragments
// without creating sub-tours, then close into Hamiltonian cycle.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'mf',
  label: 'Multi-Fragment',
  category: 'Constructive',
  description: 'Pick the shortest edges greedily; build a single Hamiltonian path by merging fragments.',
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  // sort all unique pairs by distance ascending
  const pairs = [];
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++)
      pairs.push({ i, j, d: distanceMatrix[i][j] });
  pairs.sort((a, b) => a.d - b.d);

  let route = [];        // 0-indexed working path
  let count = 0;

  for (const { i, j } of pairs) {
    if (route.length === n) break;
    const inI = route.includes(i), inJ = route.includes(j);
    if (!inI && !inJ) {
      route.push(i, j);
    } else if (inI && !inJ) {
      const pos = route.indexOf(i);
      const A = route.slice(0, pos), B = route.slice(pos);
      const r1 = [...A, j, ...B], r2 = [j, ...A, ...B];
      const closed = arr => [...arr.map(c => c + 1), arr[0] + 1];
      const d1 = distanceCalc(distanceMatrix, closed(r1));
      const d2 = distanceCalc(distanceMatrix, closed(r2));
      route = d1 <= d2 ? r1 : r2;
    } else if (!inI && inJ) {
      const pos = route.indexOf(j);
      const A = route.slice(0, pos), B = route.slice(pos);
      const r1 = [...A, i, ...B], r2 = [i, ...A, ...B];
      const closed = arr => [...arr.map(c => c + 1), arr[0] + 1];
      const d1 = distanceCalc(distanceMatrix, closed(r1));
      const d2 = distanceCalc(distanceMatrix, closed(r2));
      route = d1 <= d2 ? r1 : r2;
    } else continue;

    count++;
    if (count % Math.max(1, Math.floor(n / 20)) === 0 || route.length === n) {
      const t = [...route.map(c => c + 1), route[0] + 1];
      yield { phase: 'edge', tour: t, bestTour: t,
              distance: distanceCalc(distanceMatrix, t),
              bestDistance: distanceCalc(distanceMatrix, t),
              iteration: count,
              highlight: { type: 'edge', from: i, to: j, color: '#7dd594' },
              message: `take edge (${i + 1},${j + 1}) d=${distanceMatrix[i][j].toFixed(2)}` };
    }
  }

  const tour = [...route.map(c => c + 1), route[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Multi-Fragment: ${distance.toFixed(2)}` };
}
