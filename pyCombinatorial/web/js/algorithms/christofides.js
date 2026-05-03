// ============================================================================
// christofides.js — Christofides Algorithm (greedy matching variant)
// Mirrors algorithm/christofides.py — MST + matching of odd-degree vertices,
// then Eulerian shortcutting. Uses GREEDY matching instead of Edmonds' blossom
// algorithm (the latter requires nontrivial code beyond reasonable port size).
// With greedy matching, we lose the formal 3/2-approximation guarantee but
// the visualization (and result) remains representative.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { minimumSpanningTree, greedyMatching } from './_shared.js';

export const meta = {
  id: 'christofides',
  label: 'Christofides (greedy)',
  category: 'Constructive',
  description: 'MST + greedy odd-degree matching → Eulerian → shortcut. Note: greedy matching, not Edmonds blossom.',
  params: [],
};

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;

  // 1. MST
  const mstEdges = minimumSpanningTree(distanceMatrix);
  const adj = Array.from({ length: n }, () => []);
  for (const [a, b] of mstEdges) { adj[a].push(b); adj[b].push(a); }
  yield { phase: 'mst', extraEdges: mstEdges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.7 })),
          iteration: 1, message: `MST: ${mstEdges.length} edges`, bestDistance: NaN };

  // 2. Odd-degree vertices
  const odd = [];
  for (let i = 0; i < n; i++) if ((adj[i].length & 1) === 1) odd.push(i);
  yield { phase: 'odd', extraEdges: mstEdges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.5 })),
          candidates: [], iteration: 2, currentCity: odd[0],
          message: `${odd.length} odd-degree vertices`, bestDistance: NaN };

  // 3. Greedy minimum-weight matching
  const matchingEdges = greedyMatching(distanceMatrix, odd);
  yield {
    phase: 'matching',
    extraEdges: [
      ...mstEdges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.5 })),
      ...matchingEdges.map(([a, b]) => ({ a, b, color: '#f5b452', alpha: 0.9, dash: [4, 3] })),
    ],
    iteration: 3, message: `${matchingEdges.length} matching edges added`, bestDistance: NaN,
  };

  // 4. Eulerian multigraph (MST + matching)
  const adjE = Array.from({ length: n }, () => []);
  for (const [a, b] of mstEdges) { adjE[a].push(b); adjE[b].push(a); }
  for (const [a, b] of matchingEdges) { adjE[a].push(b); adjE[b].push(a); }

  // 5. Eulerian circuit (Hierholzer)
  const adjCopy = adjE.map(arr => [...arr]);
  const circuit = [];
  const stack = [0];
  while (stack.length > 0) {
    const v = stack[stack.length - 1];
    if (adjCopy[v].length === 0) {
      circuit.push(stack.pop());
    } else {
      const w = adjCopy[v].pop();
      const idx = adjCopy[w].indexOf(v);
      if (idx >= 0) adjCopy[w].splice(idx, 1);
      stack.push(w);
    }
  }
  circuit.reverse();

  // 6. Shortcut
  const visited = new Set();
  const tour0 = [];
  for (const v of circuit) {
    if (!visited.has(v)) { visited.add(v); tour0.push(v); }
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
        extraEdges: [
          ...mstEdges.map(([a, b]) => ({ a, b, color: '#5dd5e6', alpha: 0.2 })),
          ...matchingEdges.map(([a, b]) => ({ a, b, color: '#f5b452', alpha: 0.3, dash: [4, 3] })),
        ],
        message: `shortcut to ${v + 1} (${tour0.length}/${n})`,
      };
    }
  }

  const tour = [...tour0.map(c => c + 1), tour0[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Christofides (greedy): ${distance.toFixed(2)}` };
}
