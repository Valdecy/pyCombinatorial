// ============================================================================
// zs.js — Zero Suffix Method
// Mirrors algorithm/zs.py — assignment-style: reduce matrix, pick zero with
// max suffix value, lock row/column, prevent sub-tours via union-find.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'zs',
  label: 'Zero Suffix Method',
  category: 'Constructive',
  description: 'Reduced-cost assignment: at each step pick the zero with greatest "suffix" (next-best in row+col).',
  params: [],
};

class UnionFind {
  constructor(n) {
    this.parent = Array.from({ length: n }, (_, i) => i);
    this.rank = new Array(n).fill(0);
  }
  find(x) { while (this.parent[x] !== x) { this.parent[x] = this.parent[this.parent[x]]; x = this.parent[x]; } return x; }
  union(a, b) {
    const ra = this.find(a), rb = this.find(b);
    if (ra === rb) return;
    if (this.rank[ra] > this.rank[rb]) this.parent[rb] = ra;
    else if (this.rank[ra] < this.rank[rb]) this.parent[ra] = rb;
    else { this.parent[rb] = ra; this.rank[ra]++; }
  }
  connected(a, b) { return this.find(a) === this.find(b); }
}

function reduceMatrix(M, n) {
  for (let i = 0; i < n; i++) {
    let mn = Infinity;
    for (let j = 0; j < n; j++) if (M[i][j] !== Infinity && M[i][j] < mn) mn = M[i][j];
    if (mn !== Infinity && mn !== 0)
      for (let j = 0; j < n; j++) if (M[i][j] !== Infinity) M[i][j] -= mn;
  }
  for (let j = 0; j < n; j++) {
    let mn = Infinity;
    for (let i = 0; i < n; i++) if (M[i][j] !== Infinity && M[i][j] < mn) mn = M[i][j];
    if (mn !== Infinity && mn !== 0)
      for (let i = 0; i < n; i++) if (M[i][j] !== Infinity) M[i][j] -= mn;
  }
}

function suffixValues(M, n) {
  const sv = Array.from({ length: n }, () => new Float64Array(n).fill(Infinity));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (M[i][j] !== 0) continue;
      let rmin = Infinity, cmin = Infinity;
      for (let k = 0; k < n; k++) {
        if (k !== j && M[i][k] !== Infinity && M[i][k] < rmin) rmin = M[i][k];
        if (k !== i && M[k][j] !== Infinity && M[k][j] < cmin) cmin = M[k][j];
      }
      sv[i][j] = (rmin === Infinity ? 0 : rmin) + (cmin === Infinity ? 0 : cmin);
    }
  }
  return sv;
}

export async function* run(distanceMatrix) {
  const n = distanceMatrix.length;
  const M = distanceMatrix.map(r => Array.from(r));
  for (let i = 0; i < n; i++) M[i][i] = Infinity;

  const pathPairs = [];
  const visitedRows = new Set();
  const visitedCols = new Set();
  const uf = new UnionFind(n);
  let it = 0;

  while (pathPairs.length < n) {
    reduceMatrix(M, n);
    const sv = suffixValues(M, n);
    let bestV = -Infinity, bi = -1, bj = -1;
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++)
        if (sv[i][j] !== Infinity && sv[i][j] > bestV) { bestV = sv[i][j]; bi = i; bj = j; }
    if (bestV === -Infinity) break;
    if (visitedRows.has(bi) || visitedCols.has(bj)) {
      M[bi][bj] = Infinity; continue;
    }
    if (uf.connected(bi, bj) && pathPairs.length < n - 1) {
      M[bi][bj] = Infinity; continue;
    }
    pathPairs.push([bi, bj]);
    visitedRows.add(bi); visitedCols.add(bj);
    uf.union(bi, bj);
    for (let k = 0; k < n; k++) M[bi][k] = Infinity;
    for (let k = 0; k < n; k++) M[k][bj] = Infinity;
    it++;

    if (it % Math.max(1, Math.floor(n / 25)) === 0 || pathPairs.length === n) {
      yield { phase: 'pick', iteration: it,
              bestDistance: NaN,
              highlight: { type: 'edge', from: bi, to: bj, color: '#7dd594' },
              message: `pick ${bi + 1}→${bj + 1}` };
    }
  }

  // construct path from pairs
  const route = [pathPairs[0][0]];
  const visited = new Set([route[0]]);
  while (route.length < n) {
    let advanced = false;
    for (const [a, b] of pathPairs) {
      if (a === route[route.length - 1] && !visited.has(b)) {
        route.push(b); visited.add(b); advanced = true; break;
      }
    }
    if (!advanced) {
      for (const [a, b] of pathPairs) {
        if (!visited.has(a)) { route.push(a); visited.add(a); advanced = true; break; }
      }
    }
    if (!advanced) break;
  }
  const tour = [...route.map(c => c + 1), route[0] + 1];
  const distance = distanceCalc(distanceMatrix, tour);
  return { tour, distance, summary: `Zero-Suffix: ${distance.toFixed(2)}` };
}
