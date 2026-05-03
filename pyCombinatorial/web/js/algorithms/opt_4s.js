// ============================================================================
// opt_4s.js — Stochastic 4-opt
// Mirrors algorithm/opt_4s.py
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT4_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_4s',
  label: '4-opt (stochastic)',
  category: 'Local search',
  description: 'Stochastic 4-opt: sample `search` 4-tuples per pass instead of all C(n,4).',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'search', label: 'Tuples sampled', type: 'int', default: 1000, min: 1, max: 100000 },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 4, templates: OPT4_TRIALS },
    '4-opt-stoch');
}
