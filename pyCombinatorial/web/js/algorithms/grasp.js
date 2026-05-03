// ============================================================================
// grasp.js — Greedy Randomized Adaptive Search Procedure
// Mirrors algorithm/grasp.py — α-greedy nearest neighbour with restricted
// candidate list + bounded 2-opt, repeat with new RCL each iteration.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'grasp',
  label: 'GRASP',
  category: 'Metaheuristic',
  description: 'α-greedy randomized construction + 2-opt local search.',
  params: [
    { key: 'iterations',       label: 'Iterations',  type: 'int',   default: 50,  min: 1,  max: 5000 },
    { key: 'rcl',              label: 'RCL pool',    type: 'int',   default: 25,  min: 1,  max: 200,
      hint: 'Candidate solutions per iteration; one is chosen and refined.' },
    { key: 'greedinessValue',  label: 'Greediness',  type: 'float', default: 0.5, min: 0,  max: 1, step: 0.05,
      hint: '0 = always greedy NN, 1 = always random.' },
    { key: 'seed',             label: 'Random seed', type: 'int',   default: 42,  min: 0,  max: 99999 },
  ],
};

function ranking(distanceMatrix, city) {
  const n = distanceMatrix.length;
  const arr = Array.from({ length: n }, (_, i) => [distanceMatrix[i][city], i + 1]);
  arr.sort((a, b) => a[0] - b[0]);
  return arr;
}

function rcLConstruct(distanceMatrix, greediness, rng) {
  const n = distanceMatrix.length;
  const sequence = [1 + Math.floor(rng() * n)];
  const inSeq = new Set(sequence);
  while (sequence.length < n) {
    const last = sequence[sequence.length - 1];
    if (rng() > greediness) {
      // greedy: pick nearest unvisited
      const rank = ranking(distanceMatrix, last - 1);
      let cnt = 1, next;
      while (cnt < n) {
        next = rank[cnt][1];
        if (!inSeq.has(next)) break;
        cnt++;
      }
      sequence.push(next); inSeq.add(next);
    } else {
      let next;
      do { next = 1 + Math.floor(rng() * n); } while (inSeq.has(next));
      sequence.push(next); inSeq.add(next);
    }
  }
  sequence.push(sequence[0]);
  return [sequence, distanceCalc(distanceMatrix, sequence)];
}

function ls2opt(distanceMatrix, individual, recursive) {
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

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const iterations = params.iterations ?? 50;
  const rclSize = params.rcl ?? 25;
  const greediness = params.greedinessValue ?? 0.5;

  let best = params._initialTour
    ? [params._initialTour.slice(), distanceCalc(distanceMatrix, params._initialTour)]
    : rcLConstruct(distanceMatrix, greediness, rng);

  yield {
    phase: 'init',
    tour: best[0], bestTour: best[0],
    distance: best[1], bestDistance: best[1],
    iteration: 0,
    message: `start ${best[1].toFixed(2)}`,
  };

  for (let it = 0; it < iterations; it++) {
    const rclList = [];
    for (let r = 0; r < rclSize; r++) rclList.push(rcLConstruct(distanceMatrix, greediness, rng));
    const candIdx = Math.floor(rng() * rclSize);
    let cand = ls2opt(distanceMatrix, rclList[candIdx], 2);
    while (cand[0].join(',') !== rclList[candIdx][0].join(',')) {
      rclList[candIdx] = [cand[0].slice(), cand[1]];
      cand = ls2opt(distanceMatrix, rclList[candIdx], 2);
    }
    const improved = cand[1] < best[1];
    if (improved) best = [cand[0].slice(), cand[1]];
    yield {
      phase: improved ? 'improvement' : 'iteration',
      tour: cand[0], bestTour: best[0],
      distance: cand[1], bestDistance: best[1],
      iteration: it + 1,
      message: improved ? `★ ${cand[1].toFixed(2)}` : `iter ${it + 1}: ${cand[1].toFixed(2)}  best ${best[1].toFixed(2)}`,
    };
  }

  return { tour: best[0], distance: best[1], summary: `GRASP: ${best[1].toFixed(2)}` };
}
