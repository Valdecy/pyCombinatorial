// ============================================================================
// rss.js — Randomized Spectral Seriation
// Mirrors algorithm/rss.py — like ssi but uses an embedding (multiple
// eigenvectors) and projects randomly each iteration; richer search space.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { jacobiEig, mulberry32, normalRandom, localSearch2Opt } from './_shared.js';

export const meta = {
  id: 'rss',
  label: 'Randomized Spectral Seriation',
  category: 'Constructive',
  description: 'Random projection of multi-vector spectral embedding + perturb + 2-opt.',
  warnIf: { citiesAbove: 150, message: 'spectral decomposition is O(n³); may be slow.' },
  params: [
    { key: 'k',           label: 'kNN k',       type: 'int',   default: 12,    min: 2,  max: 50 },
    { key: 'iterations',  label: 'Iterations',  type: 'int',   default: 100,   min: 1,  max: 5000 },
    { key: 'sigmaNoise',  label: 'Noise σ',     type: 'float', default: 0.006, min: 0,  max: 1, step: 0.001 },
    { key: 'twoOptPasses',label: '2-opt passes',type: 'int',   default: 5,     min: 0,  max: 100 },
    { key: 'numVecs',     label: 'Embed dim',   type: 'int',   default: 3,     min: 1,  max: 10,
      hint: 'How many eigenvectors form the embedding.' },
    { key: 'seed',        label: 'Random seed', type: 'int',   default: 7,     min: 0,  max: 99999 },
  ],
};

function buildLaplacian(distanceMatrix, k) {
  const n = distanceMatrix.length;
  const knn = [];
  for (let i = 0; i < n; i++) {
    const idx = Array.from({ length: n }, (_, j) => j).filter(j => j !== i)
      .sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b])
      .slice(0, Math.min(k, n - 1));
    knn.push(idx);
  }
  const sig = new Float64Array(n);
  for (let i = 0; i < n; i++) sig[i] = distanceMatrix[i][knn[i][knn[i].length - 1]] + 1e-12;

  const W = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++) {
    for (const j of knn[i]) {
      const d = distanceMatrix[i][j];
      W[i][j] = Math.exp(-(d * d) / (sig[i] * sig[j] + 1e-12));
    }
  }
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++) { const v = W[i][j] + W[j][i]; W[i][j] = v; W[j][i] = v; }

  const L = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++) {
    let deg = 0;
    for (let j = 0; j < n; j++) deg += W[i][j];
    L[i][i] = deg;
    for (let j = 0; j < n; j++) if (i !== j) L[i][j] = -W[i][j];
  }
  return L;
}

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  if (n < 3) return { tour: null, distance: 0, summary: 'too few cities' };

  const rng = mulberry32(params.seed ?? 7);
  const numVecs = Math.max(1, params.numVecs ?? 3);

  const L = buildLaplacian(distanceMatrix, params.k ?? 12);
  const { values, vectors } = jacobiEig(L);
  const eps = 1e-8;
  let j0 = 0;
  while (j0 < n && values[j0] < eps) j0++;
  if (j0 === 0 && n > 1) j0 = 1;
  const end = Math.min(j0 + numVecs, vectors.length);
  const embedding = vectors.slice(j0, end);   // m vectors of length n

  yield {
    phase: 'spectral',
    iteration: 0, bestDistance: NaN,
    message: `embedding: ${embedding.length} vectors`,
  };

  let bestL = Infinity, bestTour = null;
  const iters = Math.max(1, params.iterations ?? 100);
  const sigma = params.sigmaNoise ?? 0.006;

  for (let it = 0; it < iters; it++) {
    // random unit-vector linear combination of embedding
    const m = embedding.length;
    const coeffs = new Float64Array(m);
    let cnorm = 0;
    for (let k = 0; k < m; k++) {
      const c = normalRandom(rng);
      coeffs[k] = c;
      cnorm += c * c;
    }
    if (m > 0) coeffs[0] *= 3;
    cnorm = Math.sqrt(cnorm) + 1e-12;
    for (let k = 0; k < m; k++) coeffs[k] /= cnorm;

    // x_proj = embedding * coeffs
    const xp = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      let s = 0;
      for (let k = 0; k < m; k++) s += embedding[k][i] * coeffs[k];
      xp[i] = s + sigma * normalRandom(rng);
    }
    let order = Array.from({ length: n }, (_, i) => i).sort((a, b) => xp[a] - xp[b]);
    if (rng() < 0.5) order.reverse();
    const shift = Math.floor(rng() * n);
    order = [...order.slice(shift), ...order.slice(0, shift)];

    let tour = [...order.map(c => c + 1), order[0] + 1];
    let dist = distanceCalc(distanceMatrix, tour);
    if ((params.twoOptPasses ?? 5) > 0) {
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
  return { tour: bestTour, distance: bestL, summary: `Randomized Spectral: ${bestL.toFixed(2)}` };
}
