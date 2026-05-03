// ============================================================================
// twoopt_refiner.js — post-hoc 2-opt that operates on a finished tour
// Wraps opt_2 with `_initialTour` so the user can refine ANY algorithm's
// output and watch the swaps happen.
// ============================================================================

import * as opt2 from '../algorithms/opt_2.js';

/**
 * Build a 2-opt refiner generator from a finished tour.
 * @param {number[][]} distanceMatrix
 * @param {number[]} tour 1-indexed closed tour
 * @param {object} options
 */
export function makeRefiner(distanceMatrix, tour, options = {}) {
  return opt2.run(distanceMatrix, {
    _initialTour: tour,
    recursiveSeeding: options.recursiveSeeding ?? -1,
    showAllAttempts: options.showAllAttempts ?? false,
  });
}
