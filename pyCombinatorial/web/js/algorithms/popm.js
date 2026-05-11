// ============================================================================
// popm.js — POPMUSIC (Partial OPtimization Metaheuristic Under Special
// Intensification Conditions) for the TSP
// Mirrors algorithm/popm.py
// ============================================================================

import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'popm',
  label: 'POPMUSIC',
  category: 'Metaheuristic',
  description: 'Recursive path decomposition + POPMUSIC local optimization with 3-opt intensification.',
  params: [
    {
      key: 'sampleSize',
      label: 'Sample size',
      type: 'int',
      default: 10,
      min: 2,
      max: 500,
      hint: 'Recursive cluster/sample size used in the constructive phase.',
    },
    {
      key: 'maxNeighbors',
      label: 'Max neighbours',
      type: 'int',
      default: 5,
      min: 1,
      max: 200,
      hint: 'Nearest-neighbour candidate list size used in the 3-opt search.',
    },
    {
      key: 'solutions',
      label: 'Solutions',
      type: 'int',
      default: 1,
      min: 1,
      max: 500,
      hint: 'Independent random starts; the best solution is kept.',
    },
    {
      key: 'trials',
      label: 'Trials',
      type: 'int',
      default: 1,
      min: 0,
      max: 200,
      hint: 'Number of 3-opt passes per subproblem before a double-bridge kick.',
    },
    {
      key: 'seed',
      label: 'Random seed',
      type: 'int',
      default: 42,
      min: 0,
      max: 99999,
    },
  ],
};

function randint(rng, a, b) {
  return a + Math.floor(rng() * (b - a + 1));
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function copyMatrix(distanceMatrix) {
  return Array.from({ length: distanceMatrix.length }, (_, i) =>
    Array.from(distanceMatrix[i], x => Number(x))
  );
}

function tourCost(distanceMatrix, tour0) {
  let cost = 0;
  for (let k = 0; k < tour0.length - 1; k++) cost += distanceMatrix[tour0[k]][tour0[k + 1]];
  return cost;
}

function isSymmetric(distanceMatrix, atol = 1e-12) {
  const n = distanceMatrix.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (Math.abs(distanceMatrix[i][j] - distanceMatrix[j][i]) > atol) return false;
    }
  }
  return true;
}

function symmetrize(distanceMatrix) {
  const n = distanceMatrix.length;
  const out = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    out[i][i] = 0;
    for (let j = i + 1; j < n; j++) {
      const v = 0.5 * (distanceMatrix[i][j] + distanceMatrix[j][i]);
      out[i][j] = v;
      out[j][i] = v;
    }
  }
  return out;
}

function subMatrix(distanceMatrix, indices) {
  const n = indices.length;
  const out = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) out[i][j] = distanceMatrix[indices[i]][indices[j]];
    out[i][i] = 0;
  }
  return out;
}

function prevInTour(state, v) {
  const p = state.pos[v];
  return p > 0 ? state.tour[p - 1] : state.tour[state.N - 1];
}

function nextInTour(state, v) {
  const p = state.pos[v];
  return p < state.N - 1 ? state.tour[p + 1] : state.tour[0];
}

function PREV(state, v) {
  return state.reversed ? nextInTour(state, v) : prevInTour(state, v);
}

function NEXT(state, v) {
  return state.reversed ? prevInTour(state, v) : nextInTour(state, v);
}

function between(state, v1, v2, v3) {
  const a = state.pos[v1];
  const b = state.pos[v2];
  const c = state.pos[v3];
  if (a <= c) return b >= a && b <= c;
  return b <= c || b >= a;
}

function BETWEEN(state, v1, v2, v3) {
  return state.reversed ? between(state, v3, v2, v1) : between(state, v1, v2, v3);
}

function fixedEdge(state, a, b) {
  const fp = state.fixedPair;
  if (!fp) return false;
  return (a === fp[0] && b === fp[1]) || (a === fp[1] && b === fp[0]);
}

function flip(state, src, dst) {
  if (src === dst) return;
  if (state.reversed) [src, dst] = [dst, src];

  const { tour, pos, N } = state;
  let i = pos[src];
  let j = pos[dst];
  let size = j - i;
  if (size < 0) size += N;
  if (size >= Math.floor(N / 2)) {
    const tmp = i;
    i = (j + 1 < N) ? (j + 1) : 0;
    j = (tmp - 1 >= 0) ? (tmp - 1) : (N - 1);
  }

  while (i !== j) {
    const a = tour[i];
    const b = tour[j];
    tour[i] = b;
    tour[j] = a;
    pos[a] = j;
    pos[b] = i;
    i = (i + 1 < N) ? (i + 1) : 0;
    if (i !== j) j = (j - 1 >= 0) ? (j - 1) : (N - 1);
  }
}

function threeOptPass(state) {
  const N = state.N;
  const dist = state.dist;
  const neighbor = state.neighbor;
  const dontLook = state.dontLook;

  let improved = true;
  while (improved) {
    improved = false;
    for (let b = 0; b < N; b++) {
      if (dontLook[b]) continue;
      dontLook[b] = true;

      for (let xa = 1; xa <= 2; xa++) {
        const a = PREV(state, b);
        if (fixedEdge(state, a, b)) {
          state.reversed = !state.reversed;
          continue;
        }

        const g0 = dist[a][b];
        for (const c of neighbor[b]) {
          if (c === prevInTour(state, b) || c === nextInTour(state, b)) continue;
          const g1 = g0 - dist[b][c];
          if (g1 <= 0) break;

          let moveDone = false;
          for (let xc = 1; xc <= 2 && !moveDone; xc++) {
            const d = (xc === 1) ? PREV(state, c) : NEXT(state, c);
            if (d === a || fixedEdge(state, c, d)) continue;

            const g2 = g1 + dist[c][d];
            if (xc === 1) {
              const gain = g2 - dist[d][a];
              if (gain > 0) {
                flip(state, b, d);
                state.tourLength -= gain;
                dontLook[a] = false;
                dontLook[b] = false;
                dontLook[c] = false;
                dontLook[d] = false;
                improved = true;
                moveDone = true;
                break;
              }
            }

            for (const e of neighbor[d]) {
              if (e === prevInTour(state, d) || e === nextInTour(state, d)) continue;
              if (xc === 2 && !BETWEEN(state, b, e, c)) continue;

              const g3 = g2 - dist[d][e];
              if (g3 <= 0) break;

              for (let xe = 1; xe <= xc; xe++) {
                let f;
                if (xc === 1) {
                  f = BETWEEN(state, b, e, c) ? NEXT(state, e) : PREV(state, e);
                } else {
                  f = (xe === 1) ? PREV(state, e) : NEXT(state, e);
                }
                if (f === a || fixedEdge(state, e, f)) continue;

                const gain = g3 + dist[e][f] - dist[f][a];
                if (gain <= 0) continue;

                if (xc === 1) {
                  flip(state, b, d);
                  if (f === PREV(state, e)) flip(state, e, a);
                  else flip(state, a, e);
                } else if (xe === 1) {
                  flip(state, e, c);
                  if (b === NEXT(state, a)) flip(state, b, f);
                  else flip(state, f, b);
                } else {
                  flip(state, d, a);
                  if (f === NEXT(state, e)) flip(state, f, c);
                  else flip(state, c, f);
                  if (b === NEXT(state, d)) flip(state, b, e);
                  else flip(state, e, b);
                }

                state.tourLength -= gain;
                dontLook[a] = false;
                dontLook[b] = false;
                dontLook[c] = false;
                dontLook[d] = false;
                dontLook[e] = false;
                dontLook[f] = false;
                improved = true;
                moveDone = true;
                break;
              }
              if (moveDone) break;
            }
          }
          if (moveDone) break;
        }

        state.reversed = !state.reversed;
      }
    }
  }
}

function legalT(state, r, i, t) {
  for (let j = 0; j < i; j++) if (r === t[j]) return false;
  return !fixedEdge(state, r, nextInTour(state, r));
}

function selectT(state, i, t, rng) {
  const N = state.N;
  let r = randint(rng, 0, N - 1);
  const r0 = r;
  while (!legalT(state, r, i, t)) {
    r = (r + 1 < N) ? (r + 1) : 0;
    if (r === r0) return -1;
  }
  return r;
}

function doubleBridgeKick(state, rng) {
  state.reversed = false;
  const { pos, dist } = state;
  const t = new Array(4).fill(-1);

  for (let i = 0; i < 4; i++) {
    t[i] = selectT(state, i, t, rng);
    if (t[i] < 0) return;
  }

  if (pos[t[0]] > pos[t[1]]) [t[0], t[1]] = [t[1], t[0]];
  if (pos[t[2]] > pos[t[3]]) [t[2], t[3]] = [t[3], t[2]];
  if (pos[t[0]] > pos[t[2]]) [t[0], t[2]] = [t[2], t[0]];
  if (pos[t[1]] > pos[t[3]]) [t[1], t[3]] = [t[3], t[1]];
  if (pos[t[1]] > pos[t[2]]) [t[1], t[2]] = [t[2], t[1]];

  const a = t[0], b = nextInTour(state, a);
  const c = t[2], d = nextInTour(state, c);
  const e = t[1], f = nextInTour(state, e);
  const g = t[3], h = nextInTour(state, g);

  flip(state, b, c);
  if (f === nextInTour(state, e)) flip(state, f, h);
  else flip(state, h, f);
  if (b === nextInTour(state, d)) flip(state, c, d);
  else flip(state, d, c);

  state.tourLength -= (
    (dist[a][b] - dist[b][c]) +
    (dist[c][d] - dist[d][a]) +
    (dist[e][f] - dist[f][g]) +
    (dist[g][h] - dist[h][e])
  );

  for (const v of [a, b, c, d, e, f, g, h]) state.dontLook[v] = false;
}

function pathThreeOpt(dist, nPath, maxNeighbors, trialsParam, rng, fixedPair) {
  const N = nPath + 1;
  const tour = Array.from({ length: N }, (_, i) => i);
  const pos = Array.from({ length: N }, (_, i) => i);
  let bestTour = tour.slice();

  let tourLength = 0;
  for (let i = 0; i < N - 1; i++) tourLength += dist[tour[i]][tour[i + 1]];
  tourLength += dist[tour[N - 1]][tour[0]];
  let bestTourLength = tourLength;

  const kNeighbors = Math.min(maxNeighbors, N - 1);
  const neighbor = new Array(N);
  for (let i = 0; i < N; i++) {
    const order = Array.from({ length: N }, (_, j) => j)
      .filter(j => j !== i)
      .sort((a, b) => dist[i][a] - dist[i][b] || a - b);
    neighbor[i] = order.slice(0, kNeighbors);
  }

  const state = {
    N,
    tour,
    pos,
    dist,
    neighbor,
    dontLook: new Array(N).fill(false),
    reversed: false,
    tourLength,
    fixedPair,
  };

  const trials = trialsParam > 0 ? trialsParam : N;
  for (let trial = 1; trial <= trials; trial++) {
    threeOptPass(state);
    if (state.tourLength < bestTourLength) {
      bestTour = state.tour.slice();
      bestTourLength = state.tourLength;
    } else {
      state.tour = bestTour.slice();
      state.pos = new Array(N).fill(0);
      for (let i = 0; i < N; i++) state.pos[state.tour[i]] = i;
      state.tourLength = bestTourLength;
    }

    if (N <= 5 || trial === trials) break;
    state.dontLook = new Array(N).fill(false);
    doubleBridgeKick(state, rng);
  }

  state.tour = bestTour.slice();
  state.pos = new Array(N).fill(0);
  for (let i = 0; i < N; i++) state.pos[state.tour[i]] = i;
  state.reversed = fixedPair ? (nextInTour(state, 0) === N - 1) : false;

  const order = [];
  let v = 0;
  for (let i = 0; i < N; i++) {
    order.push(v);
    v = NEXT(state, v);
  }
  return order;
}

function optimizePath(distanceMatrix, path, maxNeighbors, trialsParam, rng) {
  const nPath = path.length - 1;
  if (nPath < 2) return;

  if (path[0] === path[path.length - 1]) {
    const unique = path.slice(0, -1);
    const N = nPath;
    if (N < 3) return;

    const dist = subMatrix(distanceMatrix, unique);
    const order = pathThreeOpt(dist, N - 1, maxNeighbors, trialsParam, rng, null);

    if (order[0] !== 0) {
      const k = order.indexOf(0);
      const rotated = order.slice(k).concat(order.slice(0, k));
      order.length = 0;
      order.push(...rotated);
    }

    const newPath = [];
    for (let i = 0; i < N; i++) newPath.push(unique[order[i]]);
    newPath.push(newPath[0]);
    for (let i = 0; i <= nPath; i++) path[i] = newPath[i];
    return;
  }

  const dist = subMatrix(distanceMatrix, path);
  dist[0][nPath] = 0;
  dist[nPath][0] = 0;
  const order = pathThreeOpt(dist, nPath, maxNeighbors, trialsParam, rng, [0, nPath]);
  const newPath = new Array(nPath + 1);
  for (let i = 0; i <= nPath; i++) newPath[i] = path[order[i]];
  for (let i = 0; i <= nPath; i++) path[i] = newPath[i];
}

function buildPath(distanceMatrix, path, nbClust, maxNeighbors, trialsParam, rng) {
  const n = path.length - 1;
  if (n <= 2) return;
  if (n <= nbClust * nbClust) {
    optimizePath(distanceMatrix, path, maxNeighbors, trialsParam, rng);
    return;
  }

  const tmpPath = path.slice();

  const p0 = path[0];
  let dmin = distanceMatrix[tmpPath[1]][p0];
  let closest = 1;
  for (let i = 2; i < n; i++) {
    const d = distanceMatrix[tmpPath[i]][p0];
    if (d < dmin) {
      dmin = d;
      closest = i;
    }
  }
  [tmpPath[1], tmpPath[closest]] = [tmpPath[closest], tmpPath[1]];

  const pn = path[n];
  dmin = distanceMatrix[tmpPath[2]][pn];
  closest = 2;
  for (let i = 3; i < n; i++) {
    const d = distanceMatrix[tmpPath[i]][pn];
    if (d < dmin) {
      dmin = d;
      closest = i;
    }
  }
  [tmpPath[2], tmpPath[closest]] = [tmpPath[closest], tmpPath[2]];

  for (let i = 3; i <= nbClust; i++) {
    const j = randint(rng, i, n - 1);
    [tmpPath[i], tmpPath[j]] = [tmpPath[j], tmpPath[i]];
  }
  [tmpPath[2], tmpPath[nbClust]] = [tmpPath[nbClust], tmpPath[2]];

  const sample = [];
  for (let i = 0; i <= nbClust; i++) sample.push(tmpPath[i]);
  sample.push(path[n]);
  optimizePath(distanceMatrix, sample, maxNeighbors, trialsParam, rng);

  const assignment = new Array(n + 1).fill(0);
  for (let i = 1; i < n; i++) {
    const pi = path[i];
    let closestAnchor = 1;
    let bestD = Infinity;
    let matched = false;
    for (let j = 1; j <= nbClust; j++) {
      if (pi === sample[j]) {
        closestAnchor = j;
        matched = true;
        break;
      }
      const d = distanceMatrix[pi][sample[j]];
      if (d < bestD) {
        bestD = d;
        closestAnchor = j;
      }
    }
    assignment[i] = matched ? closestAnchor : closestAnchor;
  }

  const startClust = new Array(nbClust + 1).fill(0);
  for (let i = 1; i < n; i++) startClust[assignment[i]] += 1;
  for (let i = 1; i <= nbClust; i++) startClust[i] += startClust[i - 1];

  const assigned = new Array(nbClust + 1).fill(0);
  for (let i = 1; i < n; i++) {
    const k = assignment[i];
    tmpPath[startClust[k - 1] + assigned[k]] = path[i];
    assigned[k] += 1;
  }

  for (let i = 1; i < n; i++) path[i] = tmpPath[i - 1];

  for (let i = 0; i < nbClust; i++) {
    const start = startClust[i];
    const end = startClust[i + 1] + 1;
    if (end - start > 2) {
      const subPath = path.slice(start, end);
      buildPath(distanceMatrix, subPath, nbClust, maxNeighbors, trialsParam, rng);
      for (let j = start; j < end; j++) path[j] = subPath[j - start];
    }
  }
}

function fastPopmusic(distanceMatrix, tour, R, maxNeighbors, trialsParam, rng) {
  const n = tour.length - 1;
  if (R > n) R = n;
  if (R < 3) return;

  for (let scan = 1; scan <= 2; scan++) {
    if (scan === 2) {
      const shift = Math.floor(R / 2);
      const interior = tour.slice(0, -1);
      const rotated = interior.slice(-shift).concat(interior.slice(0, -shift));
      for (let i = 0; i < rotated.length; i++) tour[i] = rotated[i];
      tour[tour.length - 1] = tour[0];
    }

    let i = 0;
    while (i < Math.floor(n / R)) {
      const start = R * i;
      const sub = tour.slice(start, start + R + 1);
      optimizePath(distanceMatrix, sub, maxNeighbors, trialsParam, rng);
      for (let j = 0; j < sub.length; j++) tour[start + j] = sub[j];
      i += 1;
    }

    if (n % R !== 0) {
      const start = n - R;
      const sub = tour.slice(start, n + 1);
      optimizePath(distanceMatrix, sub, maxNeighbors, trialsParam, rng);
      for (let j = 0; j < sub.length; j++) tour[start + j] = sub[j];
    }
  }
}

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  if (n < 2) {
    return { tour: [1, 1], distance: 0, summary: 'POPMUSIC: 0.00' };
  }

  for (let i = 0; i < n; i++) {
    if (!distanceMatrix[i] || distanceMatrix[i].length !== n) {
      throw new Error('distanceMatrix must be square');
    }
    for (let j = 0; j < n; j++) {
      if (distanceMatrix[i][j] < 0) throw new Error('distanceMatrix cannot contain negative distances');
    }
  }

  const rng = mulberry32(params.seed ?? 42);
  const originalMatrix = copyMatrix(distanceMatrix);
  const workMatrix = isSymmetric(distanceMatrix) ? copyMatrix(distanceMatrix) : symmetrize(distanceMatrix);

  const sampleSize = clamp(params.sampleSize ?? 10, 2, n);
  const maxNeighbors = clamp(params.maxNeighbors ?? 5, 1, Math.max(1, n - 1));
  const solutions = Math.max(1, params.solutions ?? 1);
  const trials = Math.max(0, params.trials ?? 1);

  let bestTour = null;
  let bestDistance = Infinity;

  for (let s = 0; s < solutions; s++) {
    const tour = Array.from({ length: n }, (_, i) => i);
    for (let i = n - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [tour[i], tour[j]] = [tour[j], tour[i]];
    }
    tour.push(tour[0]);

    yield {
      phase: s === 0 ? 'init' : 'restart',
      tour: tour.map(v => v + 1),
      bestTour: bestTour ? bestTour.map(v => v + 1) : null,
      distance: tourCost(originalMatrix, tour),
      bestDistance,
      iteration: s + 1,
      message: `seeded solution ${s + 1}/${solutions}`,
    };

    buildPath(workMatrix, tour, sampleSize, maxNeighbors, trials, rng);
    tour[tour.length - 1] = tour[0];
    fastPopmusic(workMatrix, tour, sampleSize * sampleSize, maxNeighbors, trials, rng);
    tour[tour.length - 1] = tour[0];

    const d = tourCost(originalMatrix, tour);
    const improved = d < bestDistance;
    if (improved) {
      bestDistance = d;
      bestTour = tour.slice();
    }

    yield {
      phase: improved ? 'improvement' : 'iteration',
      tour: tour.map(v => v + 1),
      bestTour: bestTour ? bestTour.map(v => v + 1) : null,
      distance: d,
      bestDistance,
      iteration: s + 1,
      message: improved
        ? `★ solution ${s + 1}: ${d.toFixed(2)}`
        : `solution ${s + 1}: ${d.toFixed(2)}  best ${bestDistance.toFixed(2)}`,
    };
  }

  const outTour = (bestTour || [0, 0]).map(v => v + 1);
  return {
    tour: outTour,
    distance: bestDistance,
    summary: `POPMUSIC: ${bestDistance.toFixed(2)}`,
  };
}
