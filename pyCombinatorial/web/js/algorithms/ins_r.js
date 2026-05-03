// ============================================================================
// ins_r.js — Random Insertion
// Mirrors algorithm/ins_r.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { bestInsertion, mulberry32 } from './_shared.js';

export const meta = {
  id: 'ins_r',
  label: 'Random Insertion',
  category: 'Constructive',
  description: 'Insert remaining cities in random order, each at its 2-opt best position.',
  params: [
    { key: 'initialLocation', label: 'Start city', type: 'int', default: 0, min: -1, max: 999,
      hint: '-1 = try all starts.' },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const initial = params.initialLocation ?? 0;
  const rng = mulberry32(params.seed ?? 42);
  const starts = initial === -1
    ? Array.from({ length: n }, (_, i) => i)
    : [Math.max(0, Math.min(n - 1, initial))];

  let bestTour = null, bestDist = Infinity;

  for (const i1 of starts) {
    let nodes = Array.from({ length: n }, (_, i) => i);
    for (let i = nodes.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [nodes[i], nodes[j]] = [nodes[j], nodes[i]];
    }
    const dist = distanceMatrix.map(r => Float64Array.from(r));
    for (let i = 0; i < n; i++) dist[i][i] = Infinity;
    let nearest = -1, nd = Infinity;
    for (let j = 0; j < n; j++) if (dist[i1][j] < nd) { nd = dist[i1][j]; nearest = j; }
    let temp = [i1, nearest];
    for (let j = 0; j < n; j++) { dist[i1][j] = Infinity; dist[j][i1] = Infinity; dist[nearest][j] = Infinity; dist[j][nearest] = Infinity; }
    nodes = nodes.filter(x => x !== i1 && x !== nearest);

    yield { phase: 'init',
            tour: [...temp.map(c => c + 1), temp[0] + 1],
            bestTour, bestDistance: bestDist, iteration: 0,
            message: `seed ${i1 + 1}-${nearest + 1}` };

    let it = 0;
    for (const j of nodes) {
      temp.push(j);
      temp = bestInsertion(distanceMatrix, temp);
      it++;
      const t = [...temp.map(c => c + 1), temp[0] + 1];
      yield { phase: 'insert', tour: t, bestTour, distance: distanceCalc(distanceMatrix, t),
              bestDistance: bestDist, iteration: it, currentCity: j,
              message: `add ${j + 1}` };
    }
    const t = [...temp.map(c => c + 1), temp[0] + 1];
    const d = distanceCalc(distanceMatrix, t);
    if (d < bestDist) {
      bestDist = d; bestTour = t;
      yield { phase: 'improvement', tour: t, bestTour: t, distance: d, bestDistance: d,
              iteration: starts.indexOf(i1), message: `start ${i1 + 1}: best ${d.toFixed(2)}` };
    }
  }
  return { tour: bestTour, distance: bestDist, summary: `Random Insertion best: ${bestDist.toFixed(2)}` };
}
