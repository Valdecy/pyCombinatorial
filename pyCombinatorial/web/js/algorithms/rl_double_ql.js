// ============================================================================
// rl_double_ql.js — Double Q-Learning for TSP
// Mirrors algorithm/rl_double_ql.py — two Q-tables, one updated per step.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'rl_double_ql',
  label: 'Double Q-Learning',
  category: 'Neural',
  description: 'Two independent Q-tables; eliminates max-bias of vanilla Q-learning.',
  params: [
    { key: 'episodes',       label: 'Episodes',         type: 'int',   default: 1000, min: 10,    max: 100000 },
    { key: 'learningRate',   label: 'α (learning)',     type: 'float', default: 0.1,  min: 0.001, max: 1, step: 0.01 },
    { key: 'discountFactor', label: 'γ (discount)',     type: 'float', default: 0.95, min: 0,     max: 1, step: 0.01 },
    { key: 'epsilon',        label: 'ε (exploration)',  type: 'float', default: 0.15, min: 0,     max: 1, step: 0.01 },
    { key: 'yieldEvery',     label: 'Yield every',      type: 'int',   default: 50,   min: 1,     max: 10000 },
    { key: 'seed',           label: 'Random seed',      type: 'int',   default: 42,   min: 0,     max: 99999 },
  ],
};

function makeQNoisy(n, rng) {
  const Q = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) Q[i][j] = (rng() * 0.02) - 0.01;
  return Q;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
  let mx = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (distanceMatrix[i][j] > mx) mx = distanceMatrix[i][j];
  const dmN = Array.from({ length: n }, (_, i) => distanceMatrix[i].map(v => v / mx));

  const QA = makeQNoisy(n, rng);
  const QB = makeQNoisy(n, rng);
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
    while (true) {
      const unv = [];
      for (let i = 0; i < n; i++) if (!visited[i]) unv.push(i);
      if (unv.length === 0) break;
      let next;
      if (rng() < eps) next = unv[Math.floor(rng() * unv.length)];
      else {
        let bv = -Infinity;
        for (const i of unv) {
          const v = (QA[curr][i] + QB[curr][i]) / 2;
          if (v > bv) { bv = v; next = i; }
        }
      }
      const reward = -dmN[curr][next];
      // update one of the two
      if (rng() < 0.5) {
        let mxB = 0;
        if (unv.length > 1) {
          mxB = -Infinity;
          for (const i of unv) if (i !== next && QB[next][i] > mxB) mxB = QB[next][i];
          if (mxB === -Infinity) mxB = 0;
        }
        QA[curr][next] = QA[curr][next] + lr * (reward + gamma * mxB - QA[curr][next]);
      } else {
        let mxA = 0;
        if (unv.length > 1) {
          mxA = -Infinity;
          for (const i of unv) if (i !== next && QA[next][i] > mxA) mxA = QA[next][i];
          if (mxA === -Infinity) mxA = 0;
        }
        QB[curr][next] = QB[curr][next] + lr * (reward + gamma * mxA - QB[curr][next]);
      }
      curr = next;
      visited[curr] = true;
    }

    if (ep % yieldEvery === 0 || ep === episodes - 1) {
      // reconstruction with averaged Q
      let c = 0;
      const v = new Array(n).fill(false);
      v[0] = true;
      const route = [0];
      let dist = 0;
      while (route.length < n) {
        let bv = -Infinity, bx = -1;
        for (let i = 0; i < n; i++) {
          if (v[i]) continue;
          const av = (QA[c][i] + QB[c][i]) / 2;
          if (av > bv) { bv = av; bx = i; }
        }
        if (bx < 0) break;
        v[bx] = true;
        route.push(bx);
        dist += distanceMatrix[c][bx];
        c = bx;
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
  return { tour: bestTour, distance: bestDist, summary: `Double Q: ${bestDist.toFixed(2)}` };
}
