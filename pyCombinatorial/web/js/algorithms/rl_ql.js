// ============================================================================
// rl_ql.js — Q-Learning for TSP
// Mirrors algorithm/rl_ql.py — episodic ε-greedy Q-learning over normalized
// distances; final greedy rollout from city 0.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'rl_ql',
  label: 'Q-Learning',
  category: 'Neural',
  description: 'ε-greedy tabular Q-learning; reward = -distance per edge.',
  params: [
    { key: 'episodes',       label: 'Episodes',         type: 'int',   default: 1000, min: 10,    max: 100000 },
    { key: 'learningRate',   label: 'α (learning)',     type: 'float', default: 0.1,  min: 0.001, max: 1, step: 0.01 },
    { key: 'discountFactor', label: 'γ (discount)',     type: 'float', default: 0.95, min: 0,     max: 1, step: 0.01 },
    { key: 'epsilon',        label: 'ε (exploration)',  type: 'float', default: 0.15, min: 0,     max: 1, step: 0.01 },
    { key: 'yieldEvery',     label: 'Yield every',      type: 'int',   default: 50,   min: 1,     max: 10000,
      hint: 'Episodes per visualization frame; higher = faster.' },
    { key: 'seed',           label: 'Random seed',      type: 'int',   default: 42,   min: 0,     max: 99999 },
  ],
};

function argMaxIn(qRow, mask) {
  let best = -1, bv = -Infinity;
  for (let i = 0; i < qRow.length; i++) {
    if (mask[i]) continue;
    if (qRow[i] > bv) { bv = qRow[i]; best = i; }
  }
  return best;
}

function maxIn(qRow, unvisitedSet) {
  let bv = -Infinity;
  for (const i of unvisitedSet) if (qRow[i] > bv) bv = qRow[i];
  return bv === -Infinity ? 0 : bv;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
  // normalize
  let mx = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (distanceMatrix[i][j] > mx) mx = distanceMatrix[i][j];
  const dmN = Array.from({ length: n }, (_, i) => distanceMatrix[i].map(v => v / mx));

  const Q = Array.from({ length: n }, () => new Float64Array(n));
  const episodes = params.episodes ?? 1000;
  const lr = params.learningRate ?? 0.1;
  const gamma = params.discountFactor ?? 0.95;
  const eps = params.epsilon ?? 0.15;
  const yieldEvery = Math.max(1, params.yieldEvery ?? 50);

  yield {
    phase: 'init',
    iteration: 0, bestDistance: NaN,
    message: `${episodes} episodes, ε=${eps}, α=${lr}, γ=${gamma}`,
  };

  let bestRolloutDist = Infinity, bestRolloutTour = null;

  for (let ep = 0; ep < episodes; ep++) {
    let curr = Math.floor(rng() * n);
    const visited = new Set([curr]);
    const unvisited = new Set();
    for (let i = 0; i < n; i++) if (i !== curr) unvisited.add(i);

    while (visited.size < n) {
      let next;
      if (rng() < eps) {
        const arr = [...unvisited];
        next = arr[Math.floor(rng() * arr.length)];
      } else {
        let bv = -Infinity;
        for (const c of unvisited) if (Q[curr][c] > bv) { bv = Q[curr][c]; next = c; }
      }
      const reward = -dmN[curr][next];
      visited.add(next);
      unvisited.delete(next);
      const futureMax = unvisited.size > 0 ? maxIn(Q[next], unvisited) : 0;
      Q[curr][next] = Q[curr][next] + lr * (reward + gamma * futureMax - Q[curr][next]);
      curr = next;
    }

    if (ep % yieldEvery === 0 || ep === episodes - 1) {
      // greedy rollout from city 0
      let c = 0;
      const v = new Array(n).fill(false);
      v[0] = true;
      const route = [0];
      let dist = 0;
      while (route.length < n) {
        const next = argMaxIn(Q[c], v);
        if (next < 0) break;
        v[next] = true;
        route.push(next);
        dist += distanceMatrix[c][next];
        c = next;
      }
      route.push(0);
      dist += distanceMatrix[c][0];
      const tour = route.map(x => x + 1);
      const improved = dist < bestRolloutDist;
      if (improved) { bestRolloutDist = dist; bestRolloutTour = tour; }
      yield {
        phase: improved ? 'improvement' : 'episode',
        tour, bestTour: bestRolloutTour,
        distance: dist, bestDistance: bestRolloutDist,
        iteration: ep + 1,
        message: improved ? `★ ${dist.toFixed(2)}` : `ep ${ep + 1}: ${dist.toFixed(2)}  best ${bestRolloutDist.toFixed(2)}`,
      };
    }
  }
  return { tour: bestRolloutTour, distance: bestRolloutDist, summary: `Q-learning: ${bestRolloutDist.toFixed(2)}` };
}
