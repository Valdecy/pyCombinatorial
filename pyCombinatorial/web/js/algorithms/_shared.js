// ============================================================================
// _shared.js — common utilities used by many algorithm ports
// ============================================================================

import { distanceCalc } from '../core/distance.js';

/* ---------- non-yielding 2-opt (used as inner subroutine) ----------------- */
/** Run 2-opt until convergence; returns [tour, distance].
 *  This matches the Python `local_search_2_opt(...)` helper. */
export function localSearch2Opt(distanceMatrix, tour) {
  let cityList = [tour.slice(), distanceCalc(distanceMatrix, tour)];
  let priorBest = cityList[1] * 2;
  let count = -2, target = -1;
  while (count < target) {
    let improved = false;
    for (let i = 0; i < cityList[0].length - 2; i++) {
      for (let j = i + 1; j < cityList[0].length - 1; j++) {
        const cand = cityList[0].slice();
        const seg = cand.slice(i, j + 1).reverse();
        for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
        cand[cand.length - 1] = cand[0];
        const d = distanceCalc(distanceMatrix, cand);
        if (d < cityList[1]) { cityList = [cand, d]; improved = true; }
      }
    }
    count++;
    if (priorBest > cityList[1])     { priorBest = cityList[1]; count = -2; target = -1; }
    else if (cityList[1] >= priorBest) { count = -1; target = -2; }
    if (!improved && cityList[1] >= priorBest) break;
  }
  return cityList;
}

/* ---------- best insertion --------------------------------------------------*/
/** Re-runs 2-opt on the partial tour. Mirrors `best_insertion()` in many files.
 *  Input/output: 0-indexed open path. */
export function bestInsertion(distanceMatrix, partial0) {
  if (partial0.length < 3) return partial0.slice();
  const closed = partial0.map(c => c + 1);
  closed.push(closed[0]);
  const [opt, _] = localSearch2Opt(distanceMatrix, closed);
  return opt.slice(0, -1).map(c => c - 1);
}

/* ---------- cheapest insertion position ------------------------------------*/
/** Returns {pos, delta} for inserting `city` into closed `tour` (0-indexed). */
export function cheapestInsertionPos(distanceMatrix, tour0, city) {
  let best = Infinity, bestPos = 1;
  for (let p = 0; p < tour0.length; p++) {
    const a = tour0[p], b = tour0[(p + 1) % tour0.length];
    const d = distanceMatrix[a][city] + distanceMatrix[city][b] - distanceMatrix[a][b];
    if (d < best) { best = d; bestPos = p + 1; }
  }
  return { pos: bestPos, delta: best };
}

/* ---------- argmin / argmax helpers ----------------------------------------*/
export function argMin(arr, mask) {
  let best = -1, bestV = Infinity;
  for (let i = 0; i < arr.length; i++) {
    if (mask && mask[i]) continue;
    if (arr[i] < bestV) { bestV = arr[i]; best = i; }
  }
  return best;
}

export function argMax(arr, mask) {
  let best = -1, bestV = -Infinity;
  for (let i = 0; i < arr.length; i++) {
    if (mask && mask[i]) continue;
    if (arr[i] > bestV) { bestV = arr[i]; best = i; }
  }
  return best;
}

/* ---------- min spanning tree (Prim, O(n²)) --------------------------------*/
/** Returns array of [a,b] 0-indexed edges. */
export function minimumSpanningTree(distanceMatrix) {
  const n = distanceMatrix.length;
  if (n < 2) return [];
  const inTree = new Array(n).fill(false);
  const minEdge = new Float64Array(n).fill(Infinity);
  const parent = new Int32Array(n).fill(-1);
  minEdge[0] = 0;
  const edges = [];
  for (let it = 0; it < n; it++) {
    let v = -1, best = Infinity;
    for (let i = 0; i < n; i++) {
      if (!inTree[i] && minEdge[i] < best) { best = minEdge[i]; v = i; }
    }
    if (v < 0) break;
    inTree[v] = true;
    if (parent[v] >= 0) edges.push([parent[v], v]);
    for (let u = 0; u < n; u++) {
      if (!inTree[u] && distanceMatrix[v][u] < minEdge[u]) {
        minEdge[u] = distanceMatrix[v][u];
        parent[u] = v;
      }
    }
  }
  return edges;
}

/* ---------- convex hull (Andrew's monotone chain, returns CCW indices) ----*/
export function convexHullIndices(coords) {
  const n = coords.length;
  if (n < 3) return Array.from({ length: n }, (_, i) => i);
  const idx = Array.from({ length: n }, (_, i) => i)
    .sort((a, b) => coords[a][0] - coords[b][0] || coords[a][1] - coords[b][1]);
  const cross = (o, a, b) =>
    (coords[a][0] - coords[o][0]) * (coords[b][1] - coords[o][1]) -
    (coords[a][1] - coords[o][1]) * (coords[b][0] - coords[o][0]);
  const lower = [];
  for (const i of idx) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], i) <= 0) lower.pop();
    lower.push(i);
  }
  const upper = [];
  for (let k = idx.length - 1; k >= 0; k--) {
    const i = idx[k];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], i) <= 0) upper.pop();
    upper.push(i);
  }
  upper.pop();
  lower.pop();
  return lower.concat(upper);
}

/* ---------- random tour (1-indexed closed) ---------------------------------*/
export function randomTour(n, rng = Math.random) {
  const seq = Array.from({ length: n }, (_, i) => i + 1);
  for (let i = seq.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [seq[i], seq[j]] = [seq[j], seq[i]];
  }
  seq.push(seq[0]);
  return seq;
}

/* ---------- nearest neighbour from a starting city ------------------------*/
/** Returns [tour1, dist] — useful as an initial tour for many algorithms. */
export function nearestNeighbourTour(distanceMatrix, start = 0) {
  const n = distanceMatrix.length;
  const visited = new Array(n).fill(false);
  const tour = [start + 1];
  visited[start] = true;
  let curr = start;
  let total = 0;
  for (let step = 0; step < n - 1; step++) {
    let nx = -1, nd = Infinity;
    for (let i = 0; i < n; i++) {
      if (!visited[i] && distanceMatrix[curr][i] < nd) { nd = distanceMatrix[curr][i]; nx = i; }
    }
    visited[nx] = true;
    tour.push(nx + 1);
    total += nd;
    curr = nx;
  }
  total += distanceMatrix[curr][start];
  tour.push(tour[0]);
  return [tour, total];
}

/* ---------- 2-opt random swap (used by SA-style perturb) ------------------*/
export function stochastic2opt(distanceMatrix, tour, rng = Math.random) {
  const n = tour.length - 1;
  let i = Math.floor(rng() * (n - 1));
  let j = Math.floor(rng() * (n - 1));
  if (i > j) [i, j] = [j, i];
  if (j - i < 1) j = Math.min(n - 1, i + 1);
  const cand = tour.slice();
  const seg = cand.slice(i, j + 1).reverse();
  for (let k = 0; k < seg.length; k++) cand[i + k] = seg[k];
  cand[cand.length - 1] = cand[0];
  return [cand, distanceCalc(distanceMatrix, cand)];
}

/* ---------- 4-opt double-bridge ('big shuffle' perturbation) ---------------*/
export function perturb4opt(distanceMatrix, tour, rng = Math.random) {
  const seq = tour.slice(0, -1);
  const n = seq.length;
  const idx = new Set();
  while (idx.size < 4) idx.add(Math.floor(rng() * n));
  const [i, j, k, l] = [...idx].sort((a, b) => a - b);
  const A = seq.slice(0, j + 1);
  const B = seq.slice(j + 1, k + 1);
  const C = seq.slice(k + 1, l + 1);
  const D = seq.slice(l + 1);
  // classic double-bridge: A + C + B + D
  const newSeq = A.concat(C, B, D);
  newSeq.push(newSeq[0]);
  return [newSeq, distanceCalc(distanceMatrix, newSeq)];
}

/* ---------- min-weight perfect matching (greedy) ---------------------------*/
/** Greedy nearest-pair matching for vertices in `nodes` (0-indexed).
 *  Used as a fallback for Christofides where Edmonds' blossom isn't available. */
export function greedyMatching(distanceMatrix, nodes) {
  const remaining = new Set(nodes);
  const matches = [];
  while (remaining.size >= 2) {
    let bestPair = null, bestD = Infinity;
    const arr = [...remaining];
    for (let a = 0; a < arr.length; a++) {
      for (let b = a + 1; b < arr.length; b++) {
        const d = distanceMatrix[arr[a]][arr[b]];
        if (d < bestD) { bestD = d; bestPair = [arr[a], arr[b]]; }
      }
    }
    if (!bestPair) break;
    matches.push(bestPair);
    remaining.delete(bestPair[0]);
    remaining.delete(bestPair[1]);
  }
  return matches;
}

/* ---------- DFS tour from an MST (twice-around-tree shortcutting) ----------*/
/** Given undirected adjacency, return a Hamiltonian tour by skipping repeats. */
export function shortcutDFS(adj, start = 0) {
  const visited = new Set();
  const tour = [];
  const stack = [start];
  while (stack.length > 0) {
    const v = stack.pop();
    if (visited.has(v)) continue;
    visited.add(v);
    tour.push(v);
    const neighbours = adj[v] || [];
    for (let i = neighbours.length - 1; i >= 0; i--) {
      if (!visited.has(neighbours[i])) stack.push(neighbours[i]);
    }
  }
  return tour;
}

/* ---------- mulberry32 for inline use --------------------------------------*/
export function mulberry32(seed) {
  let s = seed >>> 0;
  return function () {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ---------- Box-Muller normal sample ---------------------------------------*/
export function normalRandom(rng = Math.random) {
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

/* ---------- Jacobi eigendecomposition (symmetric, dense) -------------------*/
/** Returns { values: Float64Array, vectors: Float64Array[] (col vectors) }.
 *  Ascending-sorted by eigenvalue. O(n³); fine for n ≤ ~150. */
export function jacobiEig(A, maxSweeps = 50, tol = 1e-10) {
  const n = A.length;
  // copy A
  const M = Array.from({ length: n }, (_, i) => Float64Array.from(A[i]));
  // identity
  const V = Array.from({ length: n }, (_, i) => {
    const row = new Float64Array(n);
    row[i] = 1;
    return row;
  });

  for (let sweep = 0; sweep < maxSweeps; sweep++) {
    // off-diagonal sum of squares
    let off = 0;
    for (let p = 0; p < n - 1; p++)
      for (let q = p + 1; q < n; q++)
        off += M[p][q] * M[p][q];
    if (off < tol) break;

    for (let p = 0; p < n - 1; p++) {
      for (let q = p + 1; q < n; q++) {
        const apq = M[p][q];
        if (Math.abs(apq) < 1e-14) continue;
        const app = M[p][p], aqq = M[q][q];
        const theta = (aqq - app) / (2 * apq);
        const t = theta >= 0
          ? 1 / (theta + Math.sqrt(1 + theta * theta))
          : 1 / (theta - Math.sqrt(1 + theta * theta));
        const c = 1 / Math.sqrt(1 + t * t);
        const s = t * c;
        // update M
        M[p][p] = app - t * apq;
        M[q][q] = aqq + t * apq;
        M[p][q] = 0; M[q][p] = 0;
        for (let i = 0; i < n; i++) {
          if (i !== p && i !== q) {
            const aip = M[i][p], aiq = M[i][q];
            M[i][p] = c * aip - s * aiq;
            M[p][i] = M[i][p];
            M[i][q] = s * aip + c * aiq;
            M[q][i] = M[i][q];
          }
        }
        // update V (eigenvectors stored as columns: V[i][k] = i-th component of k-th eigenvector)
        for (let i = 0; i < n; i++) {
          const vip = V[i][p], viq = V[i][q];
          V[i][p] = c * vip - s * viq;
          V[i][q] = s * vip + c * viq;
        }
      }
    }
  }

  // extract eigenvalues, sort ascending
  const values = new Float64Array(n);
  for (let i = 0; i < n; i++) values[i] = M[i][i];
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => values[a] - values[b]);
  const sortedVals = new Float64Array(n);
  // store eigenvectors as array-of-cols: vectors[k] is k-th eigenvector
  const vectors = [];
  for (let k = 0; k < n; k++) {
    sortedVals[k] = values[order[k]];
    const v = new Float64Array(n);
    for (let i = 0; i < n; i++) v[i] = V[i][order[k]];
    vectors.push(v);
  }
  return { values: sortedVals, vectors };
}

/* ---------- spectral seriation: build affinity, Laplacian, Fiedler ---------*/
export function fiedlerVector(distanceMatrix, k = 12) {
  const n = distanceMatrix.length;
  if (n < 3) return new Float64Array(n);

  // build kNN-affinity (adaptive sigma)
  const knn = [];
  for (let i = 0; i < n; i++) {
    const idx = Array.from({ length: n }, (_, j) => j)
      .filter(j => j !== i)
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
      const w = Math.exp(-(d * d) / (sig[i] * sig[j] + 1e-12));
      W[i][j] = w;
    }
  }
  // symmetrize
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++) {
      const v = (W[i][j] + W[j][i]) / 2 * 2;     // sum is what original does
      W[i][j] = v; W[j][i] = v;
    }

  // Laplacian L = D - W
  const L = Array.from({ length: n }, () => new Float64Array(n));
  for (let i = 0; i < n; i++) {
    let deg = 0;
    for (let j = 0; j < n; j++) deg += W[i][j];
    L[i][i] = deg;
    for (let j = 0; j < n; j++) if (i !== j) L[i][j] = -W[i][j];
  }

  // eigendecompose, return Fiedler (smallest nonzero)
  const { values, vectors } = jacobiEig(L);
  const eps = 1e-8;
  let j = 0;
  while (j < n && values[j] < eps) j++;
  if (j === 0 && n > 1) j = 1;
  if (j >= n) j = n - 1;
  return vectors[j];
}

/* ---------- mulberry32 for inline use --------------------------------------*/

/* ---------- opt-2 refinement applied to a 1-indexed result ----------------*/
export function maybeRefine(distanceMatrix, route1, distance, doRefine) {
  if (!doRefine) return [route1, distance];
  return localSearch2Opt(distanceMatrix, route1);
}
