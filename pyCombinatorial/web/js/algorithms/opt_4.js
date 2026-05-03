// ============================================================================
// opt_4.js — Local Search 4-opt
// Mirrors algorithm/opt_4.py via the shared kopt engine.
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT4_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_4',
  label: '4-opt',
  category: 'Local search',
  description: '4-opt local search: 4 split points, 47 segment permutation/reversal combinations.',
  warnIf: { citiesAbove: 40, message: '4-opt is O(n⁴ × 47); will be slow.' },
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'showAllAttempts', label: 'Show every attempt', type: 'bool', default: false },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 4, templates: OPT4_TRIALS, search: 0 },
    '4-opt');
}
