// ============================================================================
// aco.js — Ant Colony Optimization (Ant System variant)
// Mirrors algorithm/aco.py — pheromone trails + visibility heuristic;
// optional 2-opt local search on the iteration's best.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'aco',
  label: 'Ant Colony Optimization',
  category: 'Metaheuristic',
  description: 'Stigmergic search: ants build tours; pheromones bias next ants toward good edges.',
  params: [
    { key: 'ants',         label: 'Ants',         type: 'int',   default: 15,  min: 1, max: 200 },
    { key: 'iterations',   label: 'Iterations',   type: 'int',   default: 30,  min: 1, max: 1000 },
    { key: 'alpha',        label: 'α (pheromone)',type: 'float', default: 1,   min: 0, max: 5, step: 0.1 },
    { key: 'beta',         label: 'β (visibility)',type: 'float',default: 2,   min: 0, max: 10, step: 0.1 },
    { key: 'decay',        label: 'Evaporation ρ',type: 'float', default: 0.05,min: 0, max: 1, step: 0.01 },
    { key: 'localSearch',  label: 'Best-tour 2-opt', type: 'bool', default: true },
    { key: 'seed',         label: 'Random seed',  type: 'int',   default: 42,  min: 0, max: 99999 },
  ],
};

function localSearch2OptInline(distanceMatrix, tour, dist) {
  let cl = [tour.slice(), dist];
  let improved = true;
  while (improved) {
    improved = false;
    for (let i = 1; i < cl[0].length - 2; i++) {
      for (let j = i + 1; j < cl[0].length - 1; j++) {
        const cand = cl[0].slice();
        const seg = cand.slice(i, j).reverse();
        for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
        cand[cand.length - 1] = cand[0];
        const d = distanceCalc(distanceMatrix, cand);
        if (d < cl[1]) { cl = [cand, d]; improved = true; }
      }
    }
  }
  return cl;
}

function pickWeighted(weights, sum, rng) {
  const r = rng() * sum;
  let acc = 0;
  for (let i = 0; i < weights.length; i++) {
    acc += weights[i];
    if (r <= acc) return i;
  }
  return weights.length - 1;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
  const ants = params.ants ?? 15;
  const iterations = params.iterations ?? 30;
  const alpha = params.alpha ?? 1;
  const beta = params.beta ?? 2;
  const decay = params.decay ?? 0.05;
  const useLs = params.localSearch ?? true;

  // visibility (eta) = 1 / dist
  const eta = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      eta[i][j] = i === j ? 0 : 1 / (distanceMatrix[i][j] + 1e-10);

  const tau = Array.from({ length: n }, () => new Float64Array(n).fill(1));

  let best = { tour: null, dist: Infinity };

  yield {
    phase: 'init',
    iteration: 0, bestDistance: best.dist,
    message: `${n} cities, ${ants} ants, ${iterations} iters`,
  };

  for (let it = 0; it < iterations; it++) {
    let iterBest = { tour: null, dist: Infinity };
    const allTours = [];

    for (let a = 0; a < ants; a++) {
      const visited = new Array(n).fill(false);
      const start = Math.floor(rng() * n);
      const tour = [start + 1];
      visited[start] = true;
      let curr = start;
      for (let s = 1; s < n; s++) {
        const candidates = [];
        const weights = [];
        for (let c = 0; c < n; c++) {
          if (visited[c]) continue;
          candidates.push(c);
          weights.push(Math.pow(tau[curr][c], alpha) * Math.pow(eta[curr][c], beta));
        }
        let sum = 0;
        for (const w of weights) sum += w;
        let next;
        if (sum <= 0 || !Number.isFinite(sum)) next = candidates[Math.floor(rng() * candidates.length)];
        else next = candidates[pickWeighted(weights, sum, rng)];
        tour.push(next + 1);
        visited[next] = true;
        curr = next;
      }
      tour.push(tour[0]);
      const d = distanceCalc(distanceMatrix, tour);
      allTours.push([tour, d]);
      if (d < iterBest.dist) iterBest = { tour, dist: d };
    }

    if (useLs && iterBest.tour) {
      const ls = localSearch2OptInline(distanceMatrix, iterBest.tour, iterBest.dist);
      iterBest = { tour: ls[0], dist: ls[1] };
    }

    // pheromone deposit (all-tour mode like Python default)
    for (const [tour, d] of allTours) {
      const inv = 1 / d;
      for (let k = 0; k < tour.length - 1; k++) {
        const a = tour[k] - 1, b = tour[k + 1] - 1;
        tau[a][b] += inv; tau[b][a] += inv;
      }
    }
    // evaporate
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++)
        tau[i][j] *= (1 - decay);

    const improved = iterBest.dist < best.dist;
    if (improved) best = iterBest;

    yield {
      phase: improved ? 'improvement' : 'iteration',
      tour: iterBest.tour, bestTour: best.tour,
      distance: iterBest.dist, bestDistance: best.dist,
      iteration: it + 1,
      message: improved ? `★ ${iterBest.dist.toFixed(2)}` : `iter ${it + 1}: ${iterBest.dist.toFixed(2)}  best ${best.dist.toFixed(2)}`,
    };
  }

  return { tour: best.tour, distance: best.dist, summary: `ACO: ${best.dist.toFixed(2)}` };
}
