// ============================================================================
// ga.js — Genetic Algorithm with BCR / ER crossover + swap mutation + 2-opt
// Mirrors algorithm/ga.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';
import { seedFunction } from '../core/seed.js';

export const meta = {
  id: 'ga',
  label: 'Genetic Algorithm',
  category: 'Metaheuristic',
  description: 'Population-based: roulette selection, BCR + ER crossover, swap mutation with 2-opt.',
  params: [
    { key: 'populationSize',  label: 'Population',     type: 'int',   default: 15,  min: 4,  max: 500 },
    { key: 'elite',           label: 'Elite',          type: 'int',   default: 1,   min: 0,  max: 50 },
    { key: 'mutationRate',    label: 'Mutation rate',  type: 'float', default: 0.1, min: 0,  max: 1, step: 0.01 },
    { key: 'mutationSearch',  label: '2-opt passes',   type: 'int',   default: 1,   min: -1, max: 50 },
    { key: 'generations',     label: 'Generations',    type: 'int',   default: 50,  min: 1,  max: 5000 },
    { key: 'seed',            label: 'Random seed',    type: 'int',   default: 42,  min: 0,  max: 99999 },
  ],
};

function ls2opt(distanceMatrix, individual, recursive) {
  // recursive < 0: until convergence; otherwise that many passes
  let cl = [individual[0].slice(), individual[1]];
  let priorBest = cl[1] * 2;
  let count, target;
  if (recursive < 0) { count = -2; target = -1; }
  else { count = 0; target = recursive; }

  while (count < target) {
    for (let i = 0; i < cl[0].length - 2; i++) {
      for (let j = i + 1; j < cl[0].length - 1; j++) {
        const cand = cl[0].slice();
        const seg = cand.slice(i, j + 1).reverse();
        for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
        cand[cand.length - 1] = cand[0];
        const d = distanceCalc(distanceMatrix, cand);
        if (d < cl[1]) cl = [cand, d];
      }
    }
    count++;
    if (priorBest > cl[1] && recursive < 0) { priorBest = cl[1]; count = -2; target = -1; }
    else if (cl[1] >= priorBest && recursive < 0) { count = -1; target = -2; }
  }
  return cl;
}

function fitnessFn(cost) {
  const n = cost.length;
  const fit = new Float64Array(n);
  const cum = new Float64Array(n);
  let mn = Infinity;
  for (const c of cost) if (c < mn) mn = c;
  let sum = 0;
  for (let i = 0; i < n; i++) { fit[i] = 1 / (1 + cost[i] + Math.abs(mn)); sum += fit[i]; }
  cum[0] = fit[0];
  for (let i = 1; i < n; i++) cum[i] = cum[i - 1] + fit[i];
  for (let i = 0; i < n; i++) cum[i] /= sum;
  return cum;
}

function rouletteWheel(cum, rng) {
  const r = rng();
  for (let i = 0; i < cum.length; i++) if (r <= cum[i]) return i;
  return cum.length - 1;
}

// Best Cost Route Crossover (BCR)
function crossoverBCR(distanceMatrix, p1, p2, rng) {
  const child = [p2[0].slice(), p2[1]];
  const halfLen = Math.max(1, Math.floor(p1[0].length / 2));
  const idxs = [];
  while (idxs.length < halfLen) {
    const k = Math.floor(rng() * p1[0].length);
    if (!idxs.includes(k)) idxs.push(k);
  }
  let cut = idxs.map(i => p1[0][i]).filter(c => c !== p2[0][0]);

  let d1 = Infinity;
  for (const A of cut) {
    let best = null;
    const idx = child[0].indexOf(A);
    if (idx >= 0) child[0].splice(idx, 1);
    let mn = Infinity, mnPos = -1;
    for (let pos = 1; pos < child[0].length; pos++) {
      const trial = [...child[0].slice(0, pos), A, ...child[0].slice(pos)];
      const d = distanceCalc(distanceMatrix, trial);
      if (d < mn) { mn = d; mnPos = pos; best = trial; }
    }
    if (mn <= d1 && best) {
      d1 = mn;
      if (best[0] === best[best.length - 1]) {
        child[0] = best;
        child[1] = mn;
      }
    }
  }
  return child;
}

// Edge Recombination crossover (simplified)
function crossoverER(distanceMatrix, p1, p2, rng) {
  const ilist = [...new Set(p2[0])].sort((a, b) => a - b);
  const edgeMap = new Map();
  for (const id of ilist) edgeMap.set(id, new Set());

  const addEdges = (parent) => {
    for (let i = 0; i < parent[0].length; i++) {
      const c = parent[0][i];
      const idxL = Math.max(0, i - 1), idxR = Math.min(parent[0].length - 1, i + 1);
      edgeMap.get(c).add(parent[0][idxL]);
      edgeMap.get(c).add(parent[0][idxR]);
    }
  };
  addEdges(p1); addEdges(p2);

  let target = p1[0][0];
  const child = [target];
  edgeMap.delete(target);

  while (child.length < ilist.length - 1) {
    let candidates = [];
    let limit = Infinity;
    // find cities whose edge list contains target with minimum |edges|
    for (const [city, edges] of edgeMap) {
      if (edges.has(target)) {
        if (edges.size < limit) { candidates = [city]; limit = edges.size; }
        else if (edges.size === limit) candidates.push(city);
        edges.delete(target);
      }
    }
    let chosen;
    if (candidates.length > 0) {
      chosen = candidates[Math.floor(rng() * candidates.length)];
    } else if (edgeMap.size > 0) {
      chosen = [...edgeMap.keys()][0];
    } else {
      const last = ilist.filter(c => !child.includes(c));
      child.push(...last);
      break;
    }
    child.push(chosen);
    edgeMap.delete(chosen);
    target = chosen;
  }

  if (child.length < ilist.length) {
    for (const c of ilist) if (!child.includes(c)) child.push(c);
  }
  child.push(child[0]);
  return [child, distanceCalc(distanceMatrix, child)];
}

function mutateSwap(distanceMatrix, individual, mutationSearch, rng) {
  const len = individual[0].length;
  let k1 = 1 + Math.floor(rng() * (len - 2));
  let k2 = 1 + Math.floor(rng() * (len - 2));
  while (k2 === k1) k2 = 1 + Math.floor(rng() * (len - 2));
  const cand = [individual[0].slice(), 0];
  [cand[0][k1], cand[0][k2]] = [cand[0][k2], cand[0][k1]];
  cand[1] = distanceCalc(distanceMatrix, cand[0]);
  return ls2opt(distanceMatrix, cand, mutationSearch);
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const popSize = params.populationSize ?? 15;
  const elite = params.elite ?? 1;
  const generations = params.generations ?? 50;

  let population = [];
  for (let i = 0; i < popSize; i++) population.push(seedFunction(distanceMatrix, rng));
  population.sort((a, b) => a[1] - b[1]);
  let eliteInd = [population[0][0].slice(), population[0][1]];

  yield {
    phase: 'init',
    tour: eliteInd[0], bestTour: eliteInd[0],
    distance: eliteInd[1], bestDistance: eliteInd[1],
    iteration: 0,
    message: `pop ${popSize}, start ${eliteInd[1].toFixed(2)}`,
  };

  for (let gen = 0; gen < generations; gen++) {
    const cost = population.map(p => p[1]);
    const cum = fitnessFn(cost);
    const offspring = population.map(p => [p[0].slice(), p[1]]);

    for (let i = elite; i < popSize; i++) {
      let pi = rouletteWheel(cum, rng), pj = rouletteWheel(cum, rng);
      if (pi === pj) pj = (pj + 1) % popSize;
      const p1 = [population[pi][0].slice(), population[pi][1]];
      const p2 = [population[pj][0].slice(), population[pj][1]];
      const r1 = rng();
      let child;
      if (r1 > 0.5) {
        const r2 = rng();
        child = r2 > 0.5 ? crossoverBCR(distanceMatrix, p1, p2, rng) : crossoverBCR(distanceMatrix, p2, p1, rng);
      } else {
        child = crossoverER(distanceMatrix, p1, p2, rng);
      }
      offspring[i] = child;
    }

    for (let i = elite; i < popSize; i++) {
      if (rng() <= (params.mutationRate ?? 0.1)) {
        offspring[i] = mutateSwap(distanceMatrix, offspring[i], params.mutationSearch ?? 1, rng);
      }
    }

    offspring.sort((a, b) => a[1] - b[1]);
    population = offspring;

    const improved = population[0][1] < eliteInd[1];
    if (improved) eliteInd = [population[0][0].slice(), population[0][1]];

    yield {
      phase: improved ? 'improvement' : 'generation',
      tour: population[0][0], bestTour: eliteInd[0],
      distance: population[0][1], bestDistance: eliteInd[1],
      iteration: gen + 1,
      message: improved ? `★ ${eliteInd[1].toFixed(2)}` : `gen ${gen + 1}: ${population[0][1].toFixed(2)}  best ${eliteInd[1].toFixed(2)}`,
    };
  }

  return { tour: eliteInd[0], distance: eliteInd[1], summary: `GA: ${eliteInd[1].toFixed(2)}` };
}
