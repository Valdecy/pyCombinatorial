// ============================================================================
// ssi.js — Spectral Seriation Initializer
// Mirrors algorithm/ssi.py — sort cities by Fiedler vector + small-noise
// perturbation, repeat with 2-opt refinement; keep the best.
// Uses Jacobi eigendecomposition (dense; suitable for n ≤ ~150).
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { fiedlerVector, mulberry32, normalRandom, localSearch2Opt } from './_shared.js';

export const meta = {
  id: 'ssi',
  label: 'Spectral Seriation',
  category: 'Constructive',
  description: 'Sort cities by Fiedler vector of a kNN-affinity Laplacian; perturb + 2-opt, take best.',
  warnIf: { citiesAbove: 150, message: 'spectral decomposition is O(n³); may be slow.' },
  params: [
    { key: 'k',           label: 'kNN k',       type: 'int',   default: 12,    min: 2,  max: 50 },
    { key: 'iterations',  label: 'Iterations',  type: 'int',   default: 100,   min: 1,  max: 5000 },
    { key: 'sigmaNoise',  label: 'Noise σ',     type: 'float', default: 0.003, min: 0,  max: 1, step: 0.001 },
    { key: 'twoOptPasses',label: '2-opt passes',type: 'int',   default: 5,     min: 0,  max: 100 },
    { key: 'seed',        label: 'Random seed', type: 'int',   default: 7,     min: 0,  max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  if (n < 3) return { tour: null, distance: 0, summary: 'too few cities' };

  const rng = mulberry32(params.seed ?? 7);
  const x = fiedlerVector(distanceMatrix, params.k ?? 12);

  yield {
    phase: 'spectral',
    iteration: 0, bestDistance: NaN,
    message: `Fiedler vector computed (n=${n}); seriation begins`,
  };

  let bestL = Infinity, bestTour = null;
  const iters = Math.max(1, params.iterations ?? 100);
  const sigma = params.sigmaNoise ?? 0.003;
  const passes = Math.max(0, params.twoOptPasses ?? 5);

  for (let it = 0; it < iters; it++) {
    const noisy = new Float64Array(n);
    for (let i = 0; i < n; i++) noisy[i] = x[i] + sigma * normalRandom(rng);
    let order = Array.from({ length: n }, (_, i) => i).sort((a, b) => noisy[a] - noisy[b]);
    if (rng() < 0.5) order.reverse();
    const shift = Math.floor(rng() * n);
    order = [...order.slice(shift), ...order.slice(0, shift)];

    let tour = [...order.map(c => c + 1), order[0] + 1];
    let dist = distanceCalc(distanceMatrix, tour);
    // limited 2-opt
    if (passes > 0) {
      const [t2, d2] = localSearch2Opt(distanceMatrix, tour);
      if (d2 < dist) { tour = t2; dist = d2; }
    }
    const improved = dist < bestL;
    if (improved) { bestL = dist; bestTour = tour; }

    yield {
      phase: improved ? 'improvement' : 'sample',
      tour, bestTour: bestTour,
      distance: dist, bestDistance: bestL,
      iteration: it + 1,
      message: improved ? `★ ${dist.toFixed(2)}` : `${dist.toFixed(2)}  best ${bestL.toFixed(2)}`,
    };
  }
  return { tour: bestTour, distance: bestL, summary: `Spectral Seriation: ${bestL.toFixed(2)} over ${iters} samples` };
}
