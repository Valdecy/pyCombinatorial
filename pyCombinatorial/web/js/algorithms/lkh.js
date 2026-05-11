// ============================================================================
// lkh.js — Faithful Lin-Kernighan-Helsgaun (browser variant)
// ============================================================================
// Improvements vs the previous "LKH-inspired" build (2-opt + kicks only):
//   1) O(n²) α-nearness candidates with subgradient π-ascent on the 1-tree.
//   2) Faithful sequential k-opt search (k up to 5) with the proper LK gain
//      criterion: closing edge tested first at every depth, partial-sum gain,
//      edge-uniqueness enforced, feasibility checked via single-cycle rebuild.
//   3) Don't-look bits at the k-opt level (cleared for every node touched by
//      an applied chain plus its new neighbours).
// The async-generator interface is unchanged — the visualizer keeps animating.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32, nearestNeighbourTour } from './_shared.js';

export const meta = {
  id: 'lkh',
  label: 'Lin-Kernighan-Helsgaun (LKH)',
  category: 'Local search',
  description: 'Faithful LKH: α-nearness candidates, sequential k-opt with the LK gain criterion, don\'t-look bits, and double-bridge restarts.',
  params: [
    {
      key: 'candidateSize',
      label: 'Candidate set size',
      type: 'int',
      default: 10,
      min: 3,
      max: 60,
      hint: 'Number of α-nearest candidate cities considered around each node.',
    },
    {
      key: 'maxDepth',
      label: 'k-opt max depth',
      type: 'int',
      default: 5,
      min: 2,
      max: 6,
      hint: 'Maximum k for sequential k-opt moves (Helsgaun uses 5).',
    },
    {
      key: 'breadth',
      label: 'k-opt branching',
      type: 'int',
      default: 5,
      min: 1,
      max: 10,
      hint: 'Number of y-candidates expanded at each depth of the LK chain.',
    },
    {
      key: 'ascentIterations',
      label: 'π-ascent iterations',
      type: 'int',
      default: 30,
      min: 0,
      max: 200,
      hint: 'Subgradient iterations for Held-Karp π potentials.',
    },
    {
      key: 'maxPasses',
      label: '2-opt passes',
      type: 'int',
      default: 50,
      min: 1,
      max: 200,
      hint: 'Maximum 2-opt local-search passes per intensification stage.',
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

// ---------------------------------------------------------------------------
//  ROUTE / DISTANCE UTILITIES
// ---------------------------------------------------------------------------

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

function successorPredecessor(route0) {
  const n = route0.length;
  const succ = new Int32Array(n);
  const pred = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    const a = route0[i];
    const b = route0[(i + 1) % n];
    succ[a] = b;
    pred[b] = a;
  }
  return { succ, pred };
}

// ---------------------------------------------------------------------------
//  CANDIDATE-SET PLUMBING
// ---------------------------------------------------------------------------

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

function mergeCandidates(alphaCands, nearestCands, candidateSize, distanceMatrix) {
  const n = alphaCands.length;
  const merged = [];
  for (let i = 0; i < n; i++) {
    const seen = new Set();
    const row = [];
    for (const j of [...alphaCands[i], ...nearestCands[i]]) {
      if (j === i || seen.has(j)) continue;
      row.push(j);
      seen.add(j);
    }
    row.sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b] || a - b);
    merged.push(row.slice(0, candidateSize));
  }
  return makeSymmetricCandidates(merged, candidateSize, distanceMatrix);
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

// ---------------------------------------------------------------------------
//  IMPROVEMENT 1 :  O(n²) α-NEARNESS
//  -------------------------------------------------------------------------
//  Held-Karp π-ascent on the 1-tree, then per-source DFS to build β[i, j]
//  (max edge on the i→j path in the MST that spans the n-1 non-root nodes).
//  α(i, j) = c̄(i, j) − β(i, j),  with the second-shortest-root-edge rule
//  for edges incident to the special node.
// ---------------------------------------------------------------------------

function mstPrimDense(weight, nodes) {
  const m = nodes.length;
  if (m <= 1) return { edges: [], cost: 0 };
  const minW    = new Float64Array(m).fill(Infinity);
  const minPrev = new Int32Array(m).fill(-1);
  const inTree  = new Uint8Array(m);

  minW[0] = 0;
  let cost = 0;
  const edges = [];

  for (let iter = 0; iter < m; iter++) {
    let u = -1, best = Infinity;
    for (let i = 0; i < m; i++) {
      if (!inTree[i] && minW[i] < best) { best = minW[i]; u = i; }
    }
    if (u < 0) break;
    inTree[u] = 1;
    cost += best;
    if (minPrev[u] >= 0) edges.push([nodes[minPrev[u]], nodes[u]]);
    const wu = weight[nodes[u]];
    for (let v = 0; v < m; v++) {
      if (!inTree[v]) {
        const w = wu[nodes[v]];
        if (w < minW[v]) { minW[v] = w; minPrev[v] = u; }
      }
    }
  }
  return { edges, cost };
}

function minimumOneTree(distanceMatrix, pi, root) {
  const n = distanceMatrix.length;
  const weighted = new Array(n);
  for (let i = 0; i < n; i++) {
    const row = new Float64Array(n);
    const di = distanceMatrix[i];
    const pii = pi[i];
    for (let j = 0; j < n; j++) row[j] = di[j] + pii + pi[j];
    weighted[i] = row;
  }
  const nodes = [];
  for (let i = 0; i < n; i++) if (i !== root) nodes.push(i);
  const { edges: mstEdges, cost: mstCost } = mstPrimDense(weighted, nodes);

  const rootCands = [];
  for (const j of nodes) rootCands.push([weighted[root][j], j]);
  rootCands.sort((a, b) => a[0] - b[0]);
  const e1 = [root, rootCands[0][1]];
  const e2 = [root, rootCands[1][1]];
  const allEdges = mstEdges.concat([e1, e2]);

  const degree = new Int32Array(n);
  for (const [a, b] of allEdges) { degree[a]++; degree[b]++; }

  let piSum = 0;
  for (let i = 0; i < n; i++) piSum += pi[i];
  const lowerBound = mstCost + rootCands[0][0] + rootCands[1][0] - 2 * piSum;
  return { edges: allEdges, degree, weighted, lowerBound };
}

function subgradientPotentials(distanceMatrix, root, ascentIterations) {
  const n = distanceMatrix.length;
  let pi = new Float64Array(n);
  let bestPi = new Float64Array(n);
  let result = minimumOneTree(distanceMatrix, pi, root);
  let bestEdges = result.edges;
  let bestDegree = result.degree;
  let bestLb = result.lowerBound;

  if (ascentIterations === 0) {
    return { pi: bestPi, edges: bestEdges, degree: bestDegree, lb: bestLb };
  }

  let total = 0, count = 0;
  for (let i = 0; i < n; i++) {
    const di = distanceMatrix[i];
    for (let j = 0; j < n; j++) if (di[j] > 0) { total += di[j]; count++; }
  }
  const scale = count > 0 ? total / count : 1;

  let period = Math.max(4, Math.floor(ascentIterations / 4));
  let stepScale = scale;
  let prevG = new Float64Array(n);
  let t = 0;

  while (t < ascentIterations) {
    for (let p = 0; p < period && t < ascentIterations; p++) {
      result = minimumOneTree(distanceMatrix, pi, root);
      if (result.lowerBound > bestLb + 1e-12) {
        bestLb = result.lowerBound;
        bestPi = pi.slice();
        bestEdges = result.edges;
        bestDegree = result.degree;
      }

      const g = new Float64Array(n);
      let normSq = 0;
      for (let i = 0; i < n; i++) { g[i] = result.degree[i] - 2; normSq += g[i] * g[i]; }
      if (normSq < 1e-12) {
        return { pi: pi.slice(), edges: result.edges, degree: result.degree, lb: result.lowerBound };
      }

      const beta = t > 0 ? 0.3 : 0;
      const direction = new Float64Array(n);
      let dirNormSq = 0;
      for (let i = 0; i < n; i++) {
        direction[i] = g[i] + beta * (g[i] - prevG[i]);
        dirNormSq += direction[i] * direction[i];
      }
      if (dirNormSq < 1e-12) {
        for (let i = 0; i < n; i++) direction[i] = g[i];
        dirNormSq = normSq;
      }

      const step = stepScale / Math.sqrt(dirNormSq);
      let mean = 0;
      for (let i = 0; i < n; i++) { pi[i] += step * direction[i]; mean += pi[i]; }
      mean /= n;
      for (let i = 0; i < n; i++) pi[i] -= mean;
      prevG = g;
      t++;
    }
    stepScale *= 0.5;
    period = Math.max(2, Math.floor(period / 2));
  }

  return { pi: bestPi, edges: bestEdges, degree: bestDegree, lb: bestLb };
}

function buildMstAdjacencyNoRoot(n, oneTreeEdges, weighted, root) {
  const adj = Array.from({ length: n }, () => []);
  for (const [i, j] of oneTreeEdges) {
    if (i === root || j === root) continue;
    const w = weighted[i][j];
    adj[i].push(j); adj[i].push(w);
    adj[j].push(i); adj[j].push(w);
  }
  return adj;  // flat [neighbor, weight, neighbor, weight, ...]
}

function computeBetaMatrix(n, mstAdj, root) {
  // beta is a flat n*n Float64Array; beta[i*n + j] = max edge on i→j MST path
  const beta = new Float64Array(n * n);
  const stackNode   = new Int32Array(n);
  const stackParent = new Int32Array(n);
  const stackMaxE   = new Float64Array(n);
  const visited     = new Uint8Array(n);

  for (let source = 0; source < n; source++) {
    if (source === root) continue;
    visited.fill(0);
    visited[source] = 1;
    let top = 0;
    stackNode[top] = source; stackParent[top] = -1; stackMaxE[top] = 0;
    top++;
    const baseRow = source * n;
    while (top > 0) {
      top--;
      const v = stackNode[top];
      const parent = stackParent[top];
      const maxE = stackMaxE[top];
      const adj = mstAdj[v];
      for (let k = 0; k < adj.length; k += 2) {
        const u = adj[k];
        if (visited[u]) continue;
        const w = adj[k + 1];
        visited[u] = 1;
        const newMax = maxE > w ? maxE : w;
        beta[baseRow + u] = newMax;
        stackNode[top] = u; stackParent[top] = v; stackMaxE[top] = newMax;
        top++;
      }
    }
  }
  return beta;
}

function exactAlphaValuesFast(distanceMatrix, pi, oneTreeEdges, root) {
  const n = distanceMatrix.length;
  const weighted = new Array(n);
  for (let i = 0; i < n; i++) {
    const row = new Float64Array(n);
    const di = distanceMatrix[i];
    const pii = pi[i];
    for (let j = 0; j < n; j++) row[j] = di[j] + pii + pi[j];
    weighted[i] = row;
  }

  const treeMark = new Uint8Array(n * n);
  for (const [a, b] of oneTreeEdges) { treeMark[a * n + b] = 1; treeMark[b * n + a] = 1; }

  const mstAdj = buildMstAdjacencyNoRoot(n, oneTreeEdges, weighted, root);
  const beta = computeBetaMatrix(n, mstAdj, root);

  const rootCands = [];
  for (let j = 0; j < n; j++) if (j !== root) rootCands.push([weighted[root][j], j]);
  rootCands.sort((a, b) => a[0] - b[0]);
  const sel0 = rootCands[0][1], sel1 = rootCands[1][1];
  const secondRootW = rootCands[1][0];

  const alpha = new Array(n);
  for (let i = 0; i < n; i++) alpha[i] = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      let val;
      if (treeMark[i * n + j] === 1) {
        val = 0;
      } else if (i === root || j === root) {
        const other = i === root ? j : i;
        if (other === sel0 || other === sel1) val = 0;
        else val = weighted[root][other] - secondRootW;
      } else {
        val = weighted[i][j] - beta[i * n + j];
      }
      if (val < 0) val = 0;
      alpha[i][j] = val;
      alpha[j][i] = val;
    }
  }
  return alpha;
}

function alphaNearnessCandidates(distanceMatrix, candidateSize, ascentIterations) {
  const n = distanceMatrix.length;
  candidateSize = Math.max(1, Math.min(candidateSize, n - 1));
  const { pi, edges } = subgradientPotentials(distanceMatrix, 0, ascentIterations);
  const alpha = exactAlphaValuesFast(distanceMatrix, pi, edges, 0);

  const candidates = new Array(n);
  for (let i = 0; i < n; i++) {
    const scored = [];
    const ai = alpha[i];
    const di = distanceMatrix[i];
    for (let j = 0; j < n; j++) if (j !== i) scored.push([ai[j], di[j], j]);
    scored.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const row = new Array(candidateSize);
    for (let k = 0; k < candidateSize; k++) row[k] = scored[k][2];
    candidates[i] = row;
  }
  return { candidates, alpha };
}

// ---------------------------------------------------------------------------
//  INITIAL TOURS
// ---------------------------------------------------------------------------

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

function alphaGreedy(distanceMatrix, candidates, alpha, start = 0) {
  const n = distanceMatrix.length;
  const visited = new Uint8Array(n);
  visited[start] = 1;
  const route = [start];
  for (let step = 1; step < n; step++) {
    const i = route[route.length - 1];
    let pick = -1;
    let bestAlpha = Infinity, bestDist = Infinity;
    for (const j of candidates[i]) {
      if (visited[j]) continue;
      const a = alpha[i][j], d = distanceMatrix[i][j];
      if (a < bestAlpha || (a === bestAlpha && d < bestDist)) {
        bestAlpha = a; bestDist = d; pick = j;
      }
    }
    if (pick < 0) {
      bestDist = Infinity;
      for (let j = 0; j < n; j++) {
        if (visited[j]) continue;
        const d = distanceMatrix[i][j];
        if (d < bestDist) { bestDist = d; pick = j; }
      }
    }
    route.push(pick);
    visited[pick] = 1;
  }
  return route;
}

// ---------------------------------------------------------------------------
//  CANDIDATE-GUIDED 2-OPT  (greedy descent, used as a first-pass intensifier)
// ---------------------------------------------------------------------------

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

  let bestDelta = 0, bestI = -1, bestJ = -1;

  for (let i = 0; i < n; i++) {
    const a = route0[i];
    const b = route0[(i + 1) % n];
    const cand = candidates[b];
    for (let k = 0; k < cand.length; k++) {
      const c = cand[k];
      const jRaw = pos[c];
      if (jRaw === i || jRaw === (i + 1) % n || (jRaw + 1) % n === i) continue;
      let ii = i, jj = jRaw;
      if (ii > jj) { const tmp = ii; ii = jj; jj = tmp; }
      if (ii === 0 && jj === n - 1) continue;
      const a0 = route0[ii];
      const b0 = route0[(ii + 1) % n];
      const c0 = route0[jj];
      const d0 = route0[(jj + 1) % n];
      const delta = distanceMatrix[a0][c0] + distanceMatrix[b0][d0]
                  - distanceMatrix[a0][b0] - distanceMatrix[c0][d0];
      if (delta < bestDelta) { bestDelta = delta; bestI = ii; bestJ = jj; }
    }
  }

  if (bestI < 0) return null;
  return { route: apply2Opt(route0, bestI, bestJ), delta: bestDelta, i: bestI, j: bestJ };
}

function doubleBridge(route0, rng) {
  const n = route0.length;
  if (n < 8) return route0.slice();
  const cuts = new Set();
  while (cuts.size < 4) cuts.add(1 + Math.floor(rng() * (n - 1)));
  const [a, b, c, d] = [...cuts].sort((x, y) => x - y);
  return route0.slice(0, a)
    .concat(route0.slice(b, c))
    .concat(route0.slice(a, b))
    .concat(route0.slice(c, d))
    .concat(route0.slice(d));
}

// ---------------------------------------------------------------------------
//  IMPROVEMENT 2 :  FAITHFUL SEQUENTIAL k-OPT
//  -------------------------------------------------------------------------
//  Recursive descent that builds a chain (t₁, t₂, ..., t_{2k}) where
//      x_i = (t_{2i-1}, t_{2i})  are removed tour edges
//      y_i = (t_{2i},   t_{2i+1}) are added candidate edges
//  At every depth ≥ 2 the closing move (replacing y_k with (t_{2k}, t₁)) is
//  tested first. The LK partial-sum gain criterion
//      Σ c(x_j) − Σ c(y_j) > 0
//  must hold at every level for the search to descend. Feasibility (single
//  Hamiltonian cycle) is verified by reconstructing the tour from the
//  symmetric edge difference whenever a closing attempt looks profitable.
// ---------------------------------------------------------------------------

function buildEdgeSetFromRoute(route0, n) {
  const edges = new Set();
  for (let i = 0; i < n; i++) {
    const a = route0[i], b = route0[(i + 1) % n];
    edges.add(a < b ? a * n + b : b * n + a);
  }
  return edges;
}

function rebuildTourFromEdges(n, edgeSet, start) {
  if (edgeSet.size !== n) return null;
  const adj = Array.from({ length: n }, () => []);
  for (const key of edgeSet) {
    const a = Math.floor(key / n);
    const b = key - a * n;
    adj[a].push(b);
    adj[b].push(a);
  }
  for (let i = 0; i < n; i++) if (adj[i].length !== 2) return null;
  const route = new Array(n);
  route[0] = start;
  let prev = -1, cur = start;
  for (let step = 0; step < n - 1; step++) {
    const nxts = adj[cur];
    const nxt = nxts[0] !== prev ? nxts[0] : nxts[1];
    if (nxt === start) return null;
    route[step + 1] = nxt;
    prev = cur; cur = nxt;
  }
  if (adj[cur][0] !== start && adj[cur][1] !== start) return null;
  return route;
}

function applySequentialChain(route0, chain) {
  const n = route0.length;
  const k = chain.length >>> 1;
  if ((k << 1) !== chain.length || k < 2) return null;
  const edges = buildEdgeSetFromRoute(route0, n);

  // Remove x_i = (chain[2i], chain[2i+1])
  for (let i = 0; i < k; i++) {
    const a = chain[2 * i], b = chain[2 * i + 1];
    const key = a < b ? a * n + b : b * n + a;
    if (!edges.has(key)) return null;
    edges.delete(key);
  }
  // Add y_i = (chain[2i+1], chain[2i+2]) for i = 0 .. k-2
  for (let i = 0; i < k - 1; i++) {
    const a = chain[2 * i + 1], b = chain[2 * i + 2];
    const key = a < b ? a * n + b : b * n + a;
    if (edges.has(key)) return null;
    edges.add(key);
  }
  // Closing y_k = (t_{2k}, t_1)
  {
    const a = chain[chain.length - 1], b = chain[0];
    const key = a < b ? a * n + b : b * n + a;
    if (edges.has(key)) return null;
    edges.add(key);
  }
  return rebuildTourFromEdges(n, edges, route0[0]);
}

function lkSequentialSearchFrom(distanceMatrix, route0, succ, pred, candidates, t1, maxDepth, breadth) {
  const baseDistance = routeDistance(distanceMatrix, route0);
  const state = { bestGain: 0, bestRoute: route0, bestChain: null };

  function search(chain, chainSet, CX, CY, level) {
    const tLast = chain[chain.length - 1];

    // ---- closing test (FIRST at every depth ≥ 2) ----
    if (level >= 2) {
      const closeCost = distanceMatrix[tLast][t1];
      const gainClose = CX - CY - closeCost;
      if (gainClose > state.bestGain + 1e-12) {
        const cand = applySequentialChain(route0, chain);
        if (cand !== null) {
          const candDist = routeDistance(distanceMatrix, cand);
          const realGain = baseDistance - candDist;
          if (realGain > state.bestGain + 1e-12) {
            state.bestGain  = realGain;
            state.bestRoute = cand;
            state.bestChain = chain.slice();
          }
        }
      }
    }

    if (level >= maxDepth) return;

    // ---- y candidates (LK gain criterion) ----
    const pool = [];
    const cands = candidates[tLast];
    const sLast = succ[tLast], pLast = pred[tLast];
    for (let k = 0; k < cands.length; k++) {
      const tNew = cands[k];
      if (tNew === t1 || chainSet.has(tNew)) continue;
      if (tNew === sLast || tNew === pLast) continue;     // y must not be a tour edge
      const cy = distanceMatrix[tLast][tNew];
      const G = CX - CY - cy;                             // partial-sum gain after y
      if (G <= 1e-12) continue;                           // LK criterion
      pool.push([G, tNew, cy]);
    }
    pool.sort((a, b) => b[0] - a[0]);
    const levelBreadth = level <= 2 ? breadth : Math.max(1, breadth - level + 1);
    if (pool.length > levelBreadth) pool.length = levelBreadth;

    for (let i = 0; i < pool.length; i++) {
      const tNew = pool[i][1];
      const cy   = pool[i][2];
      const sNew = succ[tNew], pNew = pred[tNew];
      for (let p = 0; p < 2; p++) {
        const tPartner = p === 0 ? sNew : pNew;
        if (tPartner === t1 || chainSet.has(tPartner)) continue;
        const cx = distanceMatrix[tNew][tPartner];

        chain.push(tNew); chain.push(tPartner);
        chainSet.add(tNew); chainSet.add(tPartner);
        search(chain, chainSet, CX + cx, CY + cy, level + 1);
        chainSet.delete(tPartner); chainSet.delete(tNew);
        chain.pop(); chain.pop();
      }
    }
  }

  for (let dir = 0; dir < 2; dir++) {
    const t2 = dir === 0 ? succ[t1] : pred[t1];
    const cx1 = distanceMatrix[t1][t2];
    const chain = [t1, t2];
    const chainSet = new Set([t1, t2]);
    search(chain, chainSet, cx1, 0, 1);
  }
  return state;
}

// ---------------------------------------------------------------------------
//  RUN
// ---------------------------------------------------------------------------

export async function* run(distanceMatrix, params = {}) {
  const n = distanceMatrix.length;
  const candidateSize     = Math.max(3, Math.min(n - 1, params.candidateSize     ?? 10));
  const maxDepth          = Math.max(2, Math.min(6,     params.maxDepth          ?? 5));
  const breadth           = Math.max(1, Math.min(10,    params.breadth           ?? 5));
  const ascentIterations  = Math.max(0,                 params.ascentIterations  ?? 30);
  const maxPasses         = Math.max(1,                 params.maxPasses         ?? 50);
  const restarts          = Math.max(0,                 params.restarts          ?? 10);
  const kicks             = Math.max(1,                 params.kicks             ?? 1);
  const rng = mulberry32(params.seed ?? 42);

  // ---- α-nearness candidates (with nearest fallback merged in) ----
  const alphaResult = alphaNearnessCandidates(distanceMatrix, candidateSize, ascentIterations);
  const nearest = nearestCandidates(distanceMatrix, candidateSize);
  let candidates = mergeCandidates(alphaResult.candidates, nearest, candidateSize, distanceMatrix);
  const alpha = alphaResult.alpha;

  // ---- initial tour: α-greedy, falling back to nearest neighbour or a randomized greedy if better ----
  const aRoute0 = alphaGreedy(distanceMatrix, candidates, alpha, 0);
  let bestRoute0 = aRoute0;
  let bestDistance = routeDistance(distanceMatrix, bestRoute0);

  const nnTour = nearestNeighbourTour(distanceMatrix, 0)[0];
  const nnRoute0 = closedToOpen(nnTour);
  const nnDistance = routeDistance(distanceMatrix, nnRoute0);
  if (nnDistance < bestDistance) { bestRoute0 = nnRoute0; bestDistance = nnDistance; }

  const rgRoute0 = randomizedGreedy(distanceMatrix, rng, 5);
  const rgDistance = routeDistance(distanceMatrix, rgRoute0);
  if (rgDistance < bestDistance) { bestRoute0 = rgRoute0; bestDistance = rgDistance; }

  yield {
    phase: 'init',
    tour: openToClosed(bestRoute0),
    bestTour: openToClosed(bestRoute0),
    distance: bestDistance,
    bestDistance,
    iteration: 0,
    message: `start ${bestDistance.toFixed(2)}  (α-candidates ready, depth=${maxDepth})`,
  };

  let currentRoute0 = bestRoute0.slice();
  let currentDistance = bestDistance;
  let moveCount = 0;

  // -----------------------------------------------------------------------
  //  Inner: candidate-guided 2-opt intensification
  // -----------------------------------------------------------------------
  const intensify2Opt = async function* (route0, distance, phaseLabel, restartIndex) {
    let localRoute0 = route0.slice();
    let localDistance = distance;

    for (let pass = 0; pass < maxPasses; pass++) {
      const move = bestCandidate2Opt(distanceMatrix, localRoute0, candidates);
      if (!move || move.delta >= -1e-12) break;
      localRoute0 = move.route;
      localDistance += move.delta;
      moveCount += 1;

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
        message: `${phaseLabel} 2-opt move ${moveCount}: ${localDistance.toFixed(2)}`,
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

    return { route0: localRoute0, distance: localDistance };
  };

  // -----------------------------------------------------------------------
  //  Inner: faithful sequential k-opt intensification with DLB
  // -----------------------------------------------------------------------
  const intensifyLK = async function* (route0, distance, restartIndex) {
    let curRoute = route0.slice();
    let { succ, pred } = successorPredecessor(curRoute);
    let curDistance = distance;
    const dlb = new Uint8Array(curRoute.length);

    let safety = 200;
    while (safety-- > 0) {
      let improvedInPass = false;

      for (let t1 = 0; t1 < curRoute.length; t1++) {
        if (dlb[t1]) continue;

        const result = lkSequentialSearchFrom(
          distanceMatrix, curRoute, succ, pred, candidates,
          t1, maxDepth, breadth
        );

        if (result.bestGain > 1e-12 && result.bestChain !== null) {
          const newSP = successorPredecessor(result.bestRoute);
          const affected = new Set(result.bestChain);
          for (const node of [...affected]) {
            affected.add(newSP.succ[node]);
            affected.add(newSP.pred[node]);
          }
          for (const node of affected) dlb[node] = 0;

          curRoute = result.bestRoute;
          succ = newSP.succ;
          pred = newSP.pred;
          curDistance -= result.bestGain;
          moveCount += 1;
          improvedInPass = true;

          yield {
            phase: 'lk-kopt',
            tour: openToClosed(curRoute),
            bestTour: openToClosed(bestRoute0),
            distance: curDistance,
            bestDistance,
            iteration: restartIndex,
            attempts: moveCount,
            improvements: moveCount,
            highlight: {
              type: 'kopt-chain',
              chain: result.bestChain.slice(),
              k: result.bestChain.length / 2,
              tour: openToClosed(curRoute),
              color: '#f7b955',
            },
            message: `k-opt (k=${result.bestChain.length / 2}) move ${moveCount}: ${curDistance.toFixed(2)}`,
          };

          if (curDistance < bestDistance - 1e-12) {
            bestRoute0 = curRoute.slice();
            bestDistance = curDistance;
            candidates = augmentCandidatesWithRoute(candidates, bestRoute0, candidateSize, distanceMatrix);
            yield {
              phase: 'improvement',
              tour: openToClosed(curRoute),
              bestTour: openToClosed(bestRoute0),
              distance: curDistance,
              bestDistance,
              iteration: restartIndex,
              attempts: moveCount,
              improvements: moveCount,
              message: `★ new best ${bestDistance.toFixed(2)}`,
            };
          }
        } else {
          dlb[t1] = 1;
        }
      }

      if (!improvedInPass) break;
    }

    return { route0: curRoute, distance: curDistance };
  };

  const drain = async function* (gen) {
    while (true) {
      const step = await gen.next();
      if (step.done) return step.value;
      yield step.value;
    }
  };

  // -----------------------------------------------------------------------
  //  Initial intensification (2-opt → faithful k-opt)
  // -----------------------------------------------------------------------
  let r1 = yield* drain(intensify2Opt(currentRoute0, currentDistance, 'intensify', 0));
  currentRoute0 = r1.route0; currentDistance = r1.distance;

  let r2 = yield* drain(intensifyLK(currentRoute0, currentDistance, 0));
  currentRoute0 = r2.route0; currentDistance = r2.distance;

  // -----------------------------------------------------------------------
  //  Restarts with double-bridge kicks
  // -----------------------------------------------------------------------
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

    let s1 = yield* drain(intensify2Opt(seedRoute0,    seedDistance, 'restart-search', restart));
    let s2 = yield* drain(intensifyLK   (s1.route0,   s1.distance,                     restart));

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
    summary: `LKH complete: ${bestDistance.toFixed(2)} (${moveCount} improving moves, k-opt depth ${maxDepth})`,
  };
}
