// ============================================================================
// opt_5.js — Local Search 5-opt
// Mirrors algorithm/opt_5.py via the shared kopt engine.
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT5_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_5',
  label: '5-opt',
  category: 'Local search',
  description: '5-opt local search: 5 split points, 373 segment permutation/reversal combinations.',
  warnIf: { citiesAbove: 25, message: '5-opt is O(n⁵ × 373); use a stochastic variant for larger instances.' },
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'showAllAttempts', label: 'Show every attempt', type: 'bool', default: false },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 5, templates: OPT5_TRIALS, search: 0 },
    '5-opt');
}
