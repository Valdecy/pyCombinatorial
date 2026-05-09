// ============================================================================
// lkh.js — Lin-Kernighan-Helsgaun-inspired search
// Browser-side practical variant for the visualizer:
//   nearest/randomized starts + candidate-guided 2-opt + double-bridge kicks.
// This keeps the web app responsive while exposing LKH-style behavior.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32, nearestNeighbourTour } from './_shared.js';

export const meta = {
  id: 'lkh',
  label: 'Lin-Kernighan-Helsgaun (LKH)',
  category: 'Local search',
  description: 'LKH-inspired search: candidate-guided 2-opt intensification with iterated double-bridge kicks and greedy restarts.',
  params: [
    {
      key: 'candidateSize',
      label: 'Candidate set size',
      type: 'int',
      default: 20,
      min: 3,
      max: 60,
      hint: 'Number of nearest candidate cities considered around each node.',
    },
    {
      key: 'maxPasses',
      label: '2-opt passes',
      type: 'int',
      default: 50,
      min: 1,
      max: 200,
      hint: 'Maximum local-search passes for each intensification stage.',
    },
    {
      key: 'restarts',
      label: 'Restarts',
      type: 'int',
      default: 10,
      min: 0,
      max: 100,
      hint: 'Number of kicked restarts from the incumbent route.',
    },
    {
      key: 'kicks',
      label: 'Double-bridge kicks',
      type: 'int',
      default: 1,
      min: 1,
      max: 8,
      hint: 'Number of double-bridge perturbations applied before each restart.',
    },
    {
      key: 'seed',
      label: 'Random seed',
      type: 'int',
      default: 42,
      min: 0,
      max: 99999,
      hint: 'Controls randomized greedy starts and kicks.',
    },
  ],
  warnIf: {
    citiesAbove: 1200,
    message: 'LKH in the browser may be slow on very large instances.',
  },
};

function closedToOpen(tour) {
  const out = tour.slice();
  if (out.length > 1 && out[0] === out[out.length - 1]) out.pop();
  return out.map(v => v - 1);
}

function openToClosed(route0) {
  const out = route0.map(v => v + 1);
  out.push(out[0]);
  return out;
}

function routeDistance(distanceMatrix, route0) {
  let total = 0;
  const n = route0.length;
  for (let i = 0; i < n; i++) {
    total += distanceMatrix[route0[i]][route0[(i + 1) % n]];
  }
  return total;
}

function nearestCandidates(distanceMatrix, candidateSize) {
  const n = distanceMatrix.length;
  const candidates = Array.from({ length: n }, () => []);
  for (let i = 0; i < n; i++) {
    const order = Array.from({ length: n }, (_, j) => j)
      .filter(j => j !== i)
      .sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b] || a - b);
    candidates[i] = order.slice(0, Math.min(candidateSize, n - 1));
  }
  return candidates;
}

function makeSymmetricCandidates(candidates, candidateSize, distanceMatrix) {
  const n = candidates.length;
  const merged = Array.from({ length: n }, (_, i) => new Set(candidates[i]));
  for (let i = 0; i < n; i++) {
    for (const j of merged[i]) merged[j].add(i);
  }
  return merged.map((row, i) => [...row]
    .filter(j => j !== i)
    .sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b] || a - b)
    .slice(0, candidateSize));
}

function augmentCandidatesWithRoute(candidates, route0, candidateSize, distanceMatrix) {
  const n = route0.length;
  const out = candidates.map(row => [...row]);
  for (let i = 0; i < n; i++) {
    const a = route0[i];
    const b = route0[(i + 1) % n];
    const c = route0[(i - 1 + n) % n];
    if (!out[a].includes(b)) out[a].unshift(b);
    if (!out[b].includes(a)) out[b].unshift(a);
    if (!out[a].includes(c)) out[a].unshift(c);
    if (!out[c].includes(a)) out[c].unshift(a);
  }
  return makeSymmetricCandidates(out, candidateSize, distanceMatrix);
}

function randomizedGreedy(distanceMatrix, rng, rcl = 5) {
  const n = distanceMatrix.length;
  const start = Math.floor(rng() * n);
  const unvisited = new Set(Array.from({ length: n }, (_, i) => i));
  const route = [start];
  unvisited.delete(start);
  while (unvisited.size > 0) {
    const curr = route[route.length - 1];
    const ordered = [...unvisited].sort((a, b) => distanceMatrix[curr][a] - distanceMatrix[curr][b] || a - b);
    const choice = ordered[Math.floor(rng() * Math.min(rcl, ordered.length))];
    route.push(choice);
    unvisited.delete(choice);
  }
  return route;
}

function apply2Opt(route0, i, j) {
  const cand = route0.slice();
  const mid = cand.slice(i + 1, j + 1).reverse();
  for (let k = 0; k < mid.length; k++) cand[i + 1 + k] = mid[k];
  return cand;
}

function bestCandidate2Opt(distanceMatrix, route0, candidates) {
  const n = route0.length;
  const pos = new Int32Array(n);
  for (let i = 0; i < n; i++) pos[route0[i]] = i;

  let bestDelta = 0;
  let bestI = -1;
  let bestJ = -1;

  for (let i = 0; i < n; i++) {
    const a = route0[i];
    const b = route0[(i + 1) % n];
    for (const c of candidates[b]) {
      const jRaw = pos[c];
      if (jRaw === i || jRaw === (i + 1) % n || (jRaw + 1) % n === i) continue;
      let ii = i;
      let jj = jRaw;
      if (ii > jj) [ii, jj] = [jj, ii];
      if (ii === 0 && jj === n - 1) continue;
      const a0 = route0[ii];
      const b0 = route0[(ii + 1) % n];
      const c0 = route0[jj];
      const d0 = route0[(jj + 1) % n];
      const delta = distanceMatrix[a0][c0] + distanceMatrix[b0][d0]
                  - distanceMatrix[a0][b0] - distanceMatrix[c0][d0];
      if (delta < bestDelta) {
        bestDelta = delta;
        bestI = ii;
        bestJ = jj;
      }
    }
  }

  if (bestI < 0) return null;
  const route = apply2Opt(route0, bestI, bestJ);
  return { route, delta: bestDelta, i: bestI, j: bestJ };
}

function doubleBridge(route0, rng) {
  const n = route0.length;
  if (n < 8) return route0.slice();
  const cuts = new Set();
  while (cuts.size < 4) cuts.add(1 + Math.floor(rng() * (n - 1)));
  const [a, b, c, d] = [...cuts].sort((x, y) => x - y);
  const p1 = route0.slice(0, a);
  const p2 = route0.slice(a, b);
  const p3 = route0.slice(b, c);
  const p4 = route0.slice(c, d);
  const p5 = route0.slice(d);
  return [...p1, ...p3, ...p2, ...p4, ...p5];
}

export async function* run(distanceMatrix, params = {}) {
  const n = distanceMatrix.length;
  const candidateSize = Math.max(3, Math.min(n - 1, params.candidateSize ?? 20));
  const maxPasses = Math.max(1, params.maxPasses ?? 50);
  const restarts = Math.max(0, params.restarts ?? 10);
  const kicks = Math.max(1, params.kicks ?? 1);
  const rng = mulberry32(params.seed ?? 42);

  let candidates = makeSymmetricCandidates(nearestCandidates(distanceMatrix, candidateSize), candidateSize, distanceMatrix);

  let baseTour = nearestNeighbourTour(distanceMatrix, 0)[0];
  let bestRoute0 = closedToOpen(baseTour);
  let bestDistance = routeDistance(distanceMatrix, bestRoute0);

  const greedyRoute0 = randomizedGreedy(distanceMatrix, rng, 5);
  const greedyDistance = routeDistance(distanceMatrix, greedyRoute0);
  if (greedyDistance < bestDistance) {
    bestRoute0 = greedyRoute0;
    bestDistance = greedyDistance;
  }

  yield {
    phase: 'init',
    tour: openToClosed(bestRoute0),
    bestTour: openToClosed(bestRoute0),
    distance: bestDistance,
    bestDistance,
    iteration: 0,
    message: `start ${bestDistance.toFixed(2)}`,
  };

  let currentRoute0 = bestRoute0.slice();
  let currentDistance = bestDistance;
  let moveCount = 0;

  const intensify = async function* (route0, distance, phaseLabel, restartIndex) {
    let localRoute0 = route0.slice();
    let localDistance = distance;
    let improved = false;

    for (let pass = 0; pass < maxPasses; pass++) {
      const move = bestCandidate2Opt(distanceMatrix, localRoute0, candidates);
      if (!move || move.delta >= -1e-12) break;
      localRoute0 = move.route;
      localDistance += move.delta;
      moveCount += 1;
      improved = true;

      yield {
        phase: phaseLabel,
        tour: openToClosed(localRoute0),
        bestTour: openToClosed(bestRoute0),
        distance: localDistance,
        bestDistance,
        iteration: restartIndex,
        attempts: moveCount,
        improvements: moveCount,
        highlight: {
          type: '2opt-segment',
          i: move.i,
          j: move.j,
          tour: openToClosed(localRoute0),
          color: '#7dd594',
        },
        message: `${phaseLabel} move ${moveCount}: ${localDistance.toFixed(2)}`,
      };

      if (localDistance < bestDistance - 1e-12) {
        bestRoute0 = localRoute0.slice();
        bestDistance = localDistance;
        candidates = augmentCandidatesWithRoute(candidates, bestRoute0, candidateSize, distanceMatrix);
        yield {
          phase: 'improvement',
          tour: openToClosed(localRoute0),
          bestTour: openToClosed(bestRoute0),
          distance: localDistance,
          bestDistance,
          iteration: restartIndex,
          attempts: moveCount,
          improvements: moveCount,
          message: `★ new best ${bestDistance.toFixed(2)}`,
        };
      }
    }

    return { route0: localRoute0, distance: localDistance, improved };
  };

  // Initial intensification
  let gen = intensify(currentRoute0, currentDistance, 'intensify', 0);
  while (true) {
    const step = await gen.next();
    if (step.done) {
      currentRoute0 = step.value.route0;
      currentDistance = step.value.distance;
      break;
    }
    yield step.value;
  }

  // Restarts with kicks
  for (let restart = 1; restart <= restarts; restart++) {
    let seedRoute0 = (restart % 3 === 0)
      ? randomizedGreedy(distanceMatrix, rng, 5)
      : bestRoute0.slice();

    for (let k = 0; k < kicks; k++) seedRoute0 = doubleBridge(seedRoute0, rng);
    let seedDistance = routeDistance(distanceMatrix, seedRoute0);

    yield {
      phase: 'restart',
      tour: openToClosed(seedRoute0),
      bestTour: openToClosed(bestRoute0),
      distance: seedDistance,
      bestDistance,
      iteration: restart,
      message: `restart ${restart}: kick`,
    };

    gen = intensify(seedRoute0, seedDistance, 'restart-search', restart);
    while (true) {
      const step = await gen.next();
      if (step.done) break;
      yield step.value;
    }

    yield {
      phase: 'restart-done',
      tour: openToClosed(bestRoute0),
      bestTour: openToClosed(bestRoute0),
      distance: bestDistance,
      bestDistance,
      iteration: restart,
      message: `restart ${restart}: incumbent ${bestDistance.toFixed(2)}`,
    };
  }

  return {
    tour: openToClosed(bestRoute0),
    distance: bestDistance,
    summary: `LKH complete: ${bestDistance.toFixed(2)} (${moveCount} improving moves)`,
  };
}
