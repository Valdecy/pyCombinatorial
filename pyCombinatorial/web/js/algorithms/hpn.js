// ============================================================================
// hpn.js — Hopfield Network TSP
// Mirrors algorithm/hpn.py — Hopfield-Tank energy: A,B,C,D constraint + tour terms.
// Per-iteration neuron updates use the full matrix energy gradient.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'hpn',
  label: 'Hopfield Network',
  category: 'Neural',
  description: 'Hopfield-Tank network: continuous neurons u[city,position] settle into a tour.',
  warnIf: { citiesAbove: 30, message: 'Hopfield is O(n²) per neuron update; slow for n > 30.' },
  params: [
    { key: 'iterations',  label: 'Iterations',  type: 'int',   default: 200, min: 10,  max: 5000 },
    { key: 'alpha',       label: 'α (tanh)',    type: 'float', default: 50,  min: 1,   max: 500 },
    { key: 'sigma',       label: 'σ (slack)',   type: 'float', default: 1,   min: 0,   max: 10, step: 0.1 },
    { key: 'A',           label: 'A (row)',     type: 'float', default: 100, min: 1,   max: 1000 },
    { key: 'B',           label: 'B (col)',     type: 'float', default: 100, min: 1,   max: 1000 },
    { key: 'C',           label: 'C (sum)',     type: 'float', default: 90,  min: 1,   max: 1000 },
    { key: 'D',           label: 'D (tour)',    type: 'float', default: 100, min: 1,   max: 1000 },
    { key: 'trials',      label: 'Restart after',type: 'int',  default: 25,  min: 1,   max: 200 },
    { key: 'seed',        label: 'Random seed', type: 'int',   default: 42,  min: 0,   max: 99999 },
  ],
};

function decodeU(u, distanceMatrix) {
  const n = u.length;
  // for each position i, take argmax over rows
  const route = [];
  const used = new Set();
  for (let i = 0; i < n; i++) {
    let bx = -1, bv = -Infinity;
    for (let r = 0; r < n; r++) {
      if (used.has(r)) continue;
      if (u[r][i] > bv) { bv = u[r][i]; bx = r; }
    }
    if (bx < 0) {
      for (let r = 0; r < n; r++) { if (!used.has(r)) { bx = r; break; } }
    }
    route.push(bx);
    used.add(bx);
  }
  for (let r = 0; r < n; r++) if (!used.has(r)) { route.push(r); used.add(r); }
  const tour = [...route.map(c => c + 1), route[0] + 1];
  return [tour, distanceCalc(distanceMatrix, tour)];
}

function updateNeurons(u, A, B, C, D, alpha, sigma, dm, n, rng) {
  for (let it = 0; it < n * n; it++) {
    const x = Math.floor(rng() * n);
    const i = Math.floor(rng() * n);
    let A_ = 0, B_ = 0, C_ = 0, D_ = 0;
    for (let k = 0; k < n; k++) if (k !== i) A_ += u[x][k];
    A_ *= -A;
    for (let k = 0; k < n; k++) if (k !== x) B_ += u[k][i];
    B_ *= -B;
    let total = 0;
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) total += u[r][c];
    C_ = -C * (total - (n + sigma));
    for (let y = 0; y < n; y++) {
      let l, r;
      if (i > 0 && i < n - 1) { l = u[y][i - 1]; r = u[y][i + 1]; }
      else if (i === 0)        { l = u[y][n - 1]; r = u[y][i + 1]; }
      else                     { l = u[y][i - 1]; r = u[y][0]; }
      D_ += dm[x][y] * (l + r);
    }
    D_ *= -D;
    u[x][i] = 0.5 * (1 + Math.tanh(alpha * (A_ + B_ + C_ + D_)));
  }
  return u;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;

  // normalize distance matrix to [0,1] (excluding diag)
  let mn = Infinity, mx = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    if (i === j) continue;
    if (distanceMatrix[i][j] > mx) mx = distanceMatrix[i][j];
    if (distanceMatrix[i][j] < mn) mn = distanceMatrix[i][j];
  }
  const dm = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      dm[i][j] = i === j ? 0 : (distanceMatrix[i][j] - mn) / (mx - mn + 1e-15);

  let u = Array.from({ length: n }, () => {
    const row = new Float64Array(n);
    for (let i = 0; i < n; i++) row[i] = rng() * 0.03;
    return row;
  });

  const iterations = params.iterations ?? 200;
  const trials = params.trials ?? 25;
  let bestDist = Infinity, bestTour = null;
  let rep = 0;

  yield {
    phase: 'init',
    iteration: 0, bestDistance: bestDist,
    message: `${n}×${n} neurons, α=${params.alpha}, σ=${params.sigma}`,
  };

  for (let it = 0; it < iterations; it++) {
    u = updateNeurons(u, params.A ?? 100, params.B ?? 100, params.C ?? 90, params.D ?? 100,
                      params.alpha ?? 50, params.sigma ?? 1, dm, n, rng);
    const [tour, d] = decodeU(u, distanceMatrix);
    const improved = d < bestDist;
    if (improved) { bestDist = d; bestTour = tour; rep = 0; }
    else rep++;

    if (rep > trials) {
      rep = 0;
      // restart neurons
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) u[i][j] = rng() * 0.03;
    }

    if (it % Math.max(1, Math.floor(iterations / 30)) === 0 || it === iterations - 1) {
      yield {
        phase: improved ? 'improvement' : 'iteration',
        tour, bestTour,
        distance: d, bestDistance: bestDist,
        iteration: it + 1,
        message: improved ? `★ ${d.toFixed(2)}` : `iter ${it + 1}: ${d.toFixed(2)}  best ${bestDist.toFixed(2)}`,
      };
    }
  }
  return { tour: bestTour, distance: bestDist, summary: `Hopfield: ${bestDist.toFixed(2)}` };
}
