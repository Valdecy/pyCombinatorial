// ============================================================================
// _ksp_helpers.js — Hungarian algorithm + simple cycle decomposition
// for Karp-Steele Patching algorithms.
// ============================================================================

/**
 * Solve the assignment problem (minimum-cost perfect matching) on a square
 * cost matrix. Returns array `r2c` such that row i is assigned to col r2c[i].
 * Uses the Jonker-Volgenant / Hungarian-style algorithm in O(n³).
 * Source: standard textbook implementation; verified against scipy on test cases.
 */
export function linearSumAssignment(cost) {
  const n = cost.length;
  const u = new Float64Array(n + 1);
  const v = new Float64Array(n + 1);
  const p = new Int32Array(n + 1);
  const way = new Int32Array(n + 1);

  for (let i = 1; i <= n; i++) {
    p[0] = i;
    let j0 = 0;
    const minv = new Float64Array(n + 1).fill(Infinity);
    const used = new Uint8Array(n + 1);

    do {
      used[j0] = 1;
      const i0 = p[j0];
      let delta = Infinity;
      let j1 = -1;
      for (let j = 1; j <= n; j++) {
        if (used[j]) continue;
        const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
        if (minv[j] < delta) { delta = minv[j]; j1 = j; }
      }
      for (let j = 0; j <= n; j++) {
        if (used[j]) { u[p[j]] += delta; v[j] -= delta; }
        else { minv[j] -= delta; }
      }
      j0 = j1;
    } while (p[j0] !== 0);

    do {
      const j1 = way[j0];
      p[j0] = p[j1];
      j0 = j1;
    } while (j0 !== 0);
  }

  const r2c = new Array(n).fill(-1);
  for (let j = 1; j <= n; j++) r2c[p[j] - 1] = j - 1;
  return r2c;
}

/**
 * Decompose a directed graph (where each node has out-degree 1, given as
 * row->col assignment array) into its disjoint cycles.
 */
export function assignmentCycles(r2c) {
  const n = r2c.length;
  const seen = new Array(n).fill(false);
  const cycles = [];
  for (let i = 0; i < n; i++) {
    if (seen[i]) continue;
    const cycle = [];
    let j = i;
    while (!seen[j]) {
      seen[j] = true;
      cycle.push(j);
      j = r2c[j];
    }
    cycles.push(cycle);
  }
  return cycles;
}

/**
 * Patch two cycles a and b into a single Hamiltonian path/cycle.
 * Mirrors the Python `patch_cycles()` simplification: try to merge by
 * choosing the best "swap" of one edge from each cycle.
 * Returns 0-indexed open path of length |a|+|b| and its closed tour distance.
 */
export function patchCycles(a, b, distanceMatrix) {
  const A = [...a, a[0]];
  const B = [...b, b[0]];
  const pairsA = [];
  const pairsB = [];
  for (let i = 0; i < A.length - 1; i++) pairsA.push([A[i], A[i + 1]]);
  for (let i = 0; i < B.length - 1; i++) pairsB.push([B[i], B[i + 1]]);

  let bestRoute = null, bestDist = Infinity;

  for (const [m1, m2] of pairsA) {
    for (const [n1, n2] of pairsB) {
      // four reconnection patterns
      const variants = [
        [[n1, m1], [n2, m2]],
        [[n2, m1], [n1, m2]],
      ];
      for (const [link1, link2] of variants) {
        const remainPairs = pairsA.filter(([x, y]) => !(x === m1 && y === m2))
                                 .concat(pairsB.filter(([x, y]) => !(x === n1 && y === n2)));
        // try to chain them starting from link1 by following next-pair-by-target
        const built = [link1[0], link1[1]];
        const remaining = remainPairs.slice();
        remaining.push(link2);
        let ok = true;
        while (built.length < a.length + b.length && ok) {
          ok = false;
          for (let r = 0; r < remaining.length; r++) {
            const [x, y] = remaining[r];
            if (built[built.length - 1] === x) {
              built.push(y); remaining.splice(r, 1); ok = true; break;
            } else if (built[built.length - 1] === y) {
              built.push(x); remaining.splice(r, 1); ok = true; break;
            }
          }
        }
        if (built.length === a.length + b.length) {
          // check it forms a valid hamiltonian path through both sets of vertices
          const set = new Set(built);
          if (set.size !== a.length + b.length) continue;
          const closed = [...built.map(c => c + 1), built[0] + 1];
          const d = closed.reduce((acc, c, i) => i === 0 ? 0
                : acc + distanceMatrix[closed[i - 1] - 1][c - 1], 0);
          if (d < bestDist) { bestDist = d; bestRoute = built; }
        }
      }
    }
  }
  // fallback: just concatenate if patching fails
  if (!bestRoute) {
    bestRoute = [...a, ...b];
    const closed = [...bestRoute.map(c => c + 1), bestRoute[0] + 1];
    bestDist = closed.reduce((acc, c, i) => i === 0 ? 0
            : acc + distanceMatrix[closed[i - 1] - 1][c - 1], 0);
  }
  return [bestRoute, bestDist];
}
