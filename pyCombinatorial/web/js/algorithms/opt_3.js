// ============================================================================
// opt_3.js — Local Search 3-opt
// Mirrors algorithm/opt_3.py via the shared kopt engine.
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT3_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_3',
  label: '3-opt',
  category: 'Local search',
  description: '3-opt local search: choose three split points, try each of 7 segment-reversal combinations.',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50,
      hint: '-1 = run until no improvement.' },
    { key: 'showAllAttempts', label: 'Show every attempt', type: 'bool', default: false },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 3, templates: OPT3_TRIALS, search: 0 },
    '3-opt');
}
