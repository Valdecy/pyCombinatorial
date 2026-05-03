// ============================================================================
// opt_2.js — 2-opt local search
// Mirrors algorithm/opt_2.py
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 'opt_2',
  label: '2-opt',
  category: 'Local search',
  description: 'Reverse tour segments while improvement is found. First-improvement scan.',
  params: [
    {
      key: 'recursiveSeeding',
      label: 'Recursive seeding',
      type: 'int',
      default: -1,
      min: -1,
      max: 50,
      hint: '-1 = run until no improvement; otherwise number of fixed passes.',
    },
    {
      key: 'showAllAttempts',
      label: 'Show every attempt',
      type: 'bool',
      default: false,
      hint: 'If on, yields on every (i,j) try (slower but more granular).',
    },
    {
      key: 'seed',
      label: 'Random seed',
      type: 'int',
      default: 42,
      min: 0,
      max: 99999,
      hint: 'Used only when no initial tour is provided.',
    },
  ],
};

/**
 * 2-opt local search.
 * Accepts an optional initial tour via params._initialTour (1-indexed, closed).
 * Otherwise, starts from a random tour seeded with params.seed.
 */
export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const showAll = !!params.showAllAttempts;
  const recursiveSeeding = params.recursiveSeeding ?? -1;

  let cityList;
  if (params._initialTour) {
    const t = [...params._initialTour];
    cityList = [t, distanceCalc(distanceMatrix, t)];
  } else {
    const rng = makeRng(params.seed ?? 42);
    cityList = seedFunction(distanceMatrix, rng);
  }

  yield {
    phase: 'init',
    tour: [...cityList[0]],
    bestTour: [...cityList[0]],
    distance: cityList[1],
    bestDistance: cityList[1],
    iteration: 0,
    message: `start ${cityList[1].toFixed(2)}`,
  };

  let count, target;
  if (recursiveSeeding < 0) { count = -2; target = -1; }
  else { count = 0; target = recursiveSeeding; }

  let priorBest = cityList[1] * 2;
  let iteration = 0;
  let attempts = 0;
  let improvements = 0;

  while (count < target) {
    let improvedThisPass = false;

    for (let i = 0; i < cityList[0].length - 2; i++) {
      for (let j = i + 1; j < cityList[0].length - 1; j++) {
        attempts++;

        // build candidate by reversing segment [i..j]
        const candidate = [...cityList[0]];
        const seg = candidate.slice(i, j + 1).reverse();
        for (let k = 0; k < seg.length; k++) candidate[i + k] = seg[k];
        candidate[candidate.length - 1] = candidate[0];
        const candDist = distanceCalc(distanceMatrix, candidate);

        if (showAll) {
          yield {
            phase: 'attempt',
            tour: [...cityList[0]],
            bestTour: [...cityList[0]],
            distance: cityList[1],
            bestDistance: cityList[1],
            highlight: {
              type: '2opt-segment',
              i, j,
              tour: candidate,
              color: candDist < cityList[1] ? '#7dd594' : '#e07a6b',
            },
            iteration,
            attempts,
            improvements,
            message: `try (${i},${j}) ⇒ ${candDist.toFixed(2)}`,
          };
        }

        if (candDist < cityList[1]) {
          cityList = [candidate, candDist];
          improvedThisPass = true;
          improvements++;
          yield {
            phase: 'improvement',
            tour: [...candidate],
            bestTour: [...candidate],
            distance: candDist,
            bestDistance: candDist,
            highlight: {
              type: '2opt-segment',
              i, j,
              tour: candidate,
              color: '#7dd594',
            },
            iteration,
            attempts,
            improvements,
            message: `swap (${i},${j}): ${candDist.toFixed(2)}`,
          };
        }
      }
    }

    iteration++;

    if (!improvedThisPass) {
      yield {
        phase: 'pass-done',
        tour: [...cityList[0]],
        bestTour: [...cityList[0]],
        distance: cityList[1],
        bestDistance: cityList[1],
        iteration,
        attempts,
        improvements,
        message: `pass ${iteration}: no improvement`,
      };
    }

    count++;
    if (priorBest > cityList[1] && recursiveSeeding < 0) {
      priorBest = cityList[1];
      count = -2;
      target = -1;
    } else if (cityList[1] >= priorBest && recursiveSeeding < 0) {
      count = -1;
      target = -2;
    }
  }

  return {
    tour: cityList[0],
    distance: cityList[1],
    summary: `2-opt complete: ${cityList[1].toFixed(2)} (${improvements} improvements / ${attempts} tries)`,
  };
}
