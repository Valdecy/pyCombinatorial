// ============================================================================
// opt_5s.js — Stochastic 5-opt
// Mirrors algorithm/opt_5s.py
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT5_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_5s',
  label: '5-opt (stochastic)',
  category: 'Local search',
  description: 'Stochastic 5-opt: sample `search` 5-tuples per pass.',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'search', label: 'Tuples sampled', type: 'int', default: 1000, min: 1, max: 100000 },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 5, templates: OPT5_TRIALS },
    '5-opt-stoch');
}
