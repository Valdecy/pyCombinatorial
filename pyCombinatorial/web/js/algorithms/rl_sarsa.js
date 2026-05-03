// ============================================================================
// rl_sarsa.js — SARSA for TSP
// Mirrors algorithm/rl_sarsa.py — on-policy: Q(s,a) ← Q(s,a) + α(r + γQ(s',a') - Q(s,a))
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'rl_sarsa',
  label: 'SARSA',
  category: 'Neural',
  description: 'On-policy TD learning: bootstrap from the action actually taken next.',
  params: [
    { key: 'episodes',       label: 'Episodes',        type: 'int',   default: 1000, min: 10,    max: 100000 },
    { key: 'learningRate',   label: 'α (learning)',    type: 'float', default: 0.1,  min: 0.001, max: 1, step: 0.01 },
    { key: 'discountFactor', label: 'γ (discount)',    type: 'float', default: 0.95, min: 0,     max: 1, step: 0.01 },
    { key: 'epsilon',        label: 'ε (exploration)', type: 'float', default: 0.15, min: 0,     max: 1, step: 0.01 },
    { key: 'yieldEvery',     label: 'Yield every',     type: 'int',   default: 50,   min: 1,     max: 10000 },
    { key: 'seed',           label: 'Random seed',     type: 'int',   default: 42,   min: 0,     max: 99999 },
  ],
};

function argMaxIn(qRow, visited) {
  let best = -1, bv = -Infinity;
  for (let i = 0; i < qRow.length; i++) {
    if (visited[i]) continue;
    if (qRow[i] > bv) { bv = qRow[i]; best = i; }
  }
  return best;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
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

  let bestDist = Infinity, bestTour = null;

  for (let ep = 0; ep < episodes; ep++) {
    let curr = Math.floor(rng() * n);
    const visited = new Array(n).fill(false);
    visited[curr] = true;
    let next;
    const pickNext = () => {
      const unv = [];
      for (let i = 0; i < n; i++) if (!visited[i]) unv.push(i);
      if (unv.length === 0) return null;
      if (rng() < eps) return unv[Math.floor(rng() * unv.length)];
      let bv = -Infinity, b = unv[0];
      for (const i of unv) if (Q[curr][i] > bv) { bv = Q[curr][i]; b = i; }
      return b;
    };
    next = pickNext();

    while (next != null) {
      const reward = -dmN[curr][next];
      visited[next] = true;
      // pick a' from next state (still ε-greedy)
      let nextNext = null;
      const unv2 = [];
      for (let i = 0; i < n; i++) if (!visited[i]) unv2.push(i);
      if (unv2.length === 0) { nextNext = null; }
      else if (rng() < eps) nextNext = unv2[Math.floor(rng() * unv2.length)];
      else {
        let bv = -Infinity;
        for (const i of unv2) if (Q[next][i] > bv) { bv = Q[next][i]; nextNext = i; }
      }
      if (nextNext != null) {
        Q[curr][next] = Q[curr][next] + lr * (reward + gamma * Q[next][nextNext] - Q[curr][next]);
      } else {
        Q[curr][next] = Q[curr][next] + lr * (reward - Q[curr][next]);
      }
      curr = next;
      next = nextNext;
    }

    if (ep % yieldEvery === 0 || ep === episodes - 1) {
      // greedy rollout from city 0
      let c = 0;
      const v = new Array(n).fill(false);
      v[0] = true;
      const route = [0];
      let dist = 0;
      while (route.length < n) {
        const nx = argMaxIn(Q[c], v);
        if (nx < 0) break;
        v[nx] = true;
        route.push(nx);
        dist += distanceMatrix[c][nx];
        c = nx;
      }
      route.push(0);
      dist += distanceMatrix[c][0];
      const tour = route.map(x => x + 1);
      const improved = dist < bestDist;
      if (improved) { bestDist = dist; bestTour = tour; }
      yield {
        phase: improved ? 'improvement' : 'episode',
        tour, bestTour,
        distance: dist, bestDistance: bestDist,
        iteration: ep + 1,
        message: improved ? `★ ${dist.toFixed(2)}` : `ep ${ep + 1}: ${dist.toFixed(2)}  best ${bestDist.toFixed(2)}`,
      };
    }
  }
  return { tour: bestTour, distance: bestDist, summary: `SARSA: ${bestDist.toFixed(2)}` };
}
