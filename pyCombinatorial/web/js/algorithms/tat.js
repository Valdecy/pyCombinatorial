// ============================================================================
// tat.js — Twice-Around-the-Tree
// Mirrors algorithm/tat.py — MST → DFS → shortcut.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { minimumSpanningTree } from './_shared.js';

export const meta = {
  id: 'tat',
  label: 'Twice-Around the Tree',
  category: 'Constructive',
  description: 'Build MST, walk it via DFS, shortcut repeats — produces a 2-approximation.',
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  const edges = minimumSpanningTree(distanceMatrix);
  const adj = Array.from({ length: n }, () => []);
  for (const [a, b] of edges) { adj[a].push(b); adj[b].push(a); }

  // sort children by distance ascending so DFS prefers nearest neighbour first
  for (let i = 0; i < n; i++) adj[i].sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b]);

  yield {
    phase: 'mst',
    extraEdges: edges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.6 })),
    bestDistance: NaN,
    iteration: 0,
    message: `MST: ${edges.length} edges`,
  };

  // DFS shortcut
  const visited = new Set();
  const tour0 = [];
  const stack = [0];
  while (stack.length > 0) {
    const v = stack.pop();
    if (visited.has(v)) continue;
    visited.add(v);
    tour0.push(v);
    const ns = adj[v];
    for (let i = ns.length - 1; i >= 0; i--) if (!visited.has(ns[i])) stack.push(ns[i]);

    if (tour0.length % Math.max(1, Math.floor(n / 30)) === 0 || tour0.length === n) {
      const t = [...tour0.map(c => c + 1)];
      if (t.length > 1) t.push(t[0]);
      yield {
        phase: 'shortcut',
        tour: t.length > 2 ? t : null,
        bestTour: t.length > 2 ? t : null,
        distance: t.length > 2 ? distanceCalc(distanceMatrix, t) : 0,
        bestDistance: NaN,
        iteration: tour0.length,
        currentCity: v,
        extraEdges: edges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.25 })),
        message: `visit ${v + 1} (${tour0.length}/${n})`,
      };
    }
  }

  const tour = [...tour0.map(c => c + 1), tour0[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Twice-Around-Tree: ${distance.toFixed(2)}` };
}
