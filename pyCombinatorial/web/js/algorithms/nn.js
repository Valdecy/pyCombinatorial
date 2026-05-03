// ============================================================================
// nn.js — Nearest Neighbour
// Mirrors algorithm/nn.py (without internal 2-opt; use the post-step refiner)
// ============================================================================

import { distanceCalc } from '../core/distance.js';

export const meta = {
  id: 'nn',
  label: 'Nearest Neighbour',
  category: 'Constructive',
  description: 'Greedy: at each step, jump to the closest unvisited city.',
  params: [
    {
      key: 'initialLocation',
      label: 'Start city',
      type: 'int',
      default: 0,
      min: -1,
      max: 999,
      hint: '0-indexed; use -1 to try every start and keep the best.',
    },
  ],
};

/**
 * @param {number[][]} distanceMatrix
 * @param {{initialLocation:number}} params
 */
export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const initialLocation = params.initialLocation ?? -1;

  const starts = initialLocation === -1
    ? Array.from({ length: n }, (_, i) => i)
    : [Math.max(0, Math.min(n - 1, initialLocation))];

  let bestTour = null;
  let bestDist = Infinity;

  for (const start of starts) {
    const visited = new Array(n).fill(false);
    visited[start] = true;
    const tour = [start + 1];                 // 1-indexed throughout (mirrors Python)
    let curr = start;
    let runningDist = 0;

    yield {
      phase: 'building',
      tour: [...tour, tour[0]],
      bestTour: bestTour,
      distance: runningDist,
      bestDistance: bestDist,
      currentCity: start,
      visited: [...visited],
      iteration: 1,
      message: `start: city ${start + 1}`,
    };

    for (let step = 0; step < n - 1; step++) {
      let nearest = -1, nearestDist = Infinity;
      for (let i = 0; i < n; i++) {
        if (!visited[i] && distanceMatrix[curr][i] < nearestDist) {
          nearest = i;
          nearestDist = distanceMatrix[curr][i];
        }
      }
      visited[nearest] = true;
      tour.push(nearest + 1);
      runningDist += nearestDist;
      curr = nearest;

      yield {
        phase: 'building',
        tour: [...tour, tour[0]],
        bestTour: bestTour,
        distance: runningDist,
        bestDistance: bestDist,
        currentCity: nearest,
        visited: [...visited],
        iteration: step + 2,
        highlight: {
          type: 'edge',
          from: tour[tour.length - 2] - 1,
          to: nearest,
        },
        message: `→ ${nearest + 1}  (Δ ${nearestDist.toFixed(2)})`,
      };
    }

    // close tour
    tour.push(tour[0]);
    const closingDist = distanceMatrix[curr][start];
    runningDist += closingDist;

    if (runningDist < bestDist) {
      bestDist = runningDist;
      bestTour = [...tour];
      yield {
        phase: 'improvement',
        tour: [...tour],
        bestTour: bestTour,
        distance: runningDist,
        bestDistance: bestDist,
        iteration: tour.length,
        message: starts.length > 1
          ? `start ${start + 1}: new best ${bestDist.toFixed(2)}`
          : `complete: ${bestDist.toFixed(2)}`,
      };
    } else {
      yield {
        phase: 'restart',
        tour: [...tour],
        bestTour: bestTour,
        distance: runningDist,
        bestDistance: bestDist,
        iteration: tour.length,
        message: `start ${start + 1}: ${runningDist.toFixed(2)} (no improvement)`,
      };
    }
  }

  return {
    tour: bestTour,
    distance: bestDist,
    summary: `NN best: ${bestDist.toFixed(2)} over ${starts.length} starts`,
  };
}
