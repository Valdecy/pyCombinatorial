// ============================================================================
// distance.js — distance helpers
// Mirror of utils/util.py: build_distance_matrix + tour distance
// ============================================================================

/**
 * Euclidean distance matrix.
 * @param {Array<[number,number]>} coords
 * @returns {Float64Array[]}
 */
export function buildDistanceMatrix(coords) {
  const n = coords.length;
  const m = new Array(n);
  for (let i = 0; i < n; i++) m[i] = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = coords[i][0] - coords[j][0];
      const dy = coords[i][1] - coords[j][1];
      const d = Math.hypot(dx, dy);
      m[i][j] = d;
      m[j][i] = d;
    }
  }
  return m;
}

/**
 * Compute the total length of a tour.
 * tour is an array of 1-indexed city ids ending with the start city,
 * matching the convention in the original Python algorithms.
 */
export function distanceCalc(distanceMatrix, tour) {
  let d = 0;
  for (let k = 0; k < tour.length - 1; k++) {
    d += distanceMatrix[tour[k] - 1][tour[k + 1] - 1];
  }
  return d;
}

/**
 * Compute total length given 0-indexed tour (more natural in JS).
 */
export function tourLength0(distanceMatrix, tour0) {
  let d = 0;
  for (let k = 0; k < tour0.length - 1; k++) {
    d += distanceMatrix[tour0[k]][tour0[k + 1]];
  }
  return d;
}
