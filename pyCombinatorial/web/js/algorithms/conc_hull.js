// ============================================================================
// conc_hull.js — Concave Hull insertion
// Mirrors algorithm/conc_hull.py — uses Moreira-Santos KNN concave hull
// followed by the same min-cost-ratio insertion as convex_hull.
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'conc_hull',
  label: 'Concave Hull',
  category: 'Constructive',
  description: 'KNN concave hull cycle + cheapest-insertion of remaining cities.',
  needsCoords: true,
  params: [
    { key: 'k', label: 'KNN k', type: 'int', default: 3, min: 3, max: 30,
      hint: 'Local neighbourhood size for the hull walk; raises if walk fails.' },
  ],
};

/* --- helper geometry ------------------------------------------------------ */
function dist(a, b) { const dx = a[0] - b[0], dy = a[1] - b[1]; return Math.hypot(dx, dy); }
function cross(o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
function segIntersect(p1, p2, p3, p4) {
  const d1 = cross(p3, p4, p1);
  const d2 = cross(p3, p4, p2);
  const d3 = cross(p1, p2, p3);
  const d4 = cross(p1, p2, p4);
  return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
         ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
}
function pointInPoly(p, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i][0], yi = poly[i][1];
    const xj = poly[j][0], yj = poly[j][1];
    const intersect = ((yi > p[1]) !== (yj > p[1])) &&
                      (p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi + 1e-15) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function buildConcaveHull(coords, kInit) {
  // Moreira-Santos algorithm: walk KNN, sweep by clockwise angle.
  let k = Math.max(3, kInit);
  while (k < coords.length + 5) {
    const result = tryHull(coords, k);
    if (result) return result;
    k++;
  }
  // fallback: linear scan
  return Array.from({ length: coords.length }, (_, i) => i);
}

function tryHull(coords, k) {
  const n = coords.length;
  const used = new Set();
  // start at lowest y
  let start = 0;
  for (let i = 1; i < n; i++) if (coords[i][1] < coords[start][1]) start = i;
  const hull = [start]; used.add(start);
  let prev = [coords[start][0] + 10, coords[start][1]];
  let curr = start;
  let step = 0;

  while (true) {
    step++;
    if (step > 5 && curr === start) break;
    if (used.size === n) break;

    // find k nearest neighbours not yet used, except let start be available after step 5
    const candidates = [];
    for (let i = 0; i < n; i++) {
      if (used.has(i) && !(i === start && step >= 5)) continue;
      candidates.push([dist(coords[curr], coords[i]), i]);
    }
    if (candidates.length === 0) break;
    candidates.sort((a, b) => a[0] - b[0]);
    const knn = candidates.slice(0, Math.min(k, candidates.length)).map(c => c[1]);

    // sort by clockwise angle from prev->curr direction
    const ang = idx => {
      const a = Math.atan2(coords[idx][1] - coords[curr][1], coords[idx][0] - coords[curr][0]);
      const b = Math.atan2(prev[1] - coords[curr][1], prev[0] - coords[curr][0]);
      let d = (a - b) * 180 / Math.PI;
      d = ((d % 360) + 360) % 360;
      return d;
    };
    knn.sort((a, b) => ang(a) - ang(b));

    // pick first that doesn't self-intersect
    let chosen = -1;
    for (const cand of knn) {
      let intersects = false;
      for (let h = 0; h < hull.length - 2; h++) {
        if (segIntersect(coords[curr], coords[cand],
                         coords[hull[h]], coords[hull[h + 1]])) {
          intersects = true; break;
        }
      }
      if (!intersects) { chosen = cand; break; }
    }
    if (chosen < 0) return null;     // need larger k

    if (chosen === start) break;
    hull.push(chosen);
    used.add(chosen);
    prev = coords[curr];
    curr = chosen;
  }

  // verify all interior points are inside polygon
  const poly = hull.map(i => coords[i]);
  for (let i = 0; i < n; i++) {
    if (used.has(i)) continue;
    if (!pointInPoly(coords[i], poly)) {
      // boundary tolerance — check small offset
      let ok = false;
      for (const eps of [[0.01, 0], [-0.01, 0], [0, 0.01], [0, -0.01]]) {
        if (pointInPoly([coords[i][0] + eps[0], coords[i][1] + eps[1]], poly)) { ok = true; break; }
      }
      if (!ok) return null;
    }
  }
  return hull;
}

export async function* run(distanceMatrix, params, ctx) {
  const coords = ctx.coords;
  const n = coords.length;
  let idx_h = buildConcaveHull(coords, params.k ?? 3);
  const onHull = new Set(idx_h);
  const inside = [];
  for (let i = 0; i < n; i++) if (!onHull.has(i)) inside.push(i);

  yield {
    phase: 'init',
    tour: [...idx_h.map(c => c + 1), idx_h[0] + 1],
    bestTour: [...idx_h.map(c => c + 1), idx_h[0] + 1],
    distance: distanceCalc(distanceMatrix, [...idx_h.map(c => c + 1), idx_h[0] + 1]),
    bestDistance: NaN,
    iteration: 0,
    message: `concave hull: ${idx_h.length} on, ${inside.length} interior`,
  };

  while (inside.length > 0) {
    let chL = -1, chPos = -1, bestRatio = Infinity;
    for (const L of inside) {
      let bestC1 = Infinity, bestPos = -1, bestC2 = Infinity;
      for (let p = 0; p < idx_h.length; p++) {
        const m = idx_h[p], nn = idx_h[(p + 1) % idx_h.length];
        const c1 = distanceMatrix[m][L] + distanceMatrix[L][nn] - distanceMatrix[m][nn];
        const c2 = (distanceMatrix[m][L] + distanceMatrix[L][nn]) / (distanceMatrix[m][nn] + 1e-15);
        if (c1 < bestC1) { bestC1 = c1; bestPos = p; bestC2 = c2; }
      }
      if (bestC2 < bestRatio) { bestRatio = bestC2; chL = L; chPos = bestPos; }
    }
    inside.splice(inside.indexOf(chL), 1);
    idx_h.splice(chPos + 1, 0, chL);
    const tour = [...idx_h.map(c => c + 1), idx_h[0] + 1];
    yield { phase: 'insert', tour, bestTour: tour,
            distance: distanceCalc(distanceMatrix, tour),
            bestDistance: distanceCalc(distanceMatrix, tour),
            iteration: idx_h.length, currentCity: chL,
            message: `insert ${chL + 1}` };
  }

  const tour = [...idx_h.map(c => c + 1), idx_h[0] + 1];
  return { tour, distance: distanceCalc(distanceMatrix, tour),
           summary: `Concave Hull: ${distanceCalc(distanceMatrix, tour).toFixed(2)}` };
}
