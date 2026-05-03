// ============================================================================
// opt_3s.js — Stochastic 3-opt
// Mirrors algorithm/opt_3s.py
// ============================================================================

import { runKopt } from './_kopt.js';
import { OPT3_TRIALS } from './_kopt_trials.js';

export const meta = {
  id: 'opt_3s',
  label: '3-opt (stochastic)',
  category: 'Local search',
  description: 'Stochastic 3-opt: sample only `search` segment triples per pass.',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'search', label: 'Tuples sampled', type: 'int', default: 1000, min: 1, max: 100000,
      hint: 'Number of (i,j,k) tuples to try per pass.' },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  return yield* runKopt(distanceMatrix,
    { ...params, kopt_k: 3, templates: OPT3_TRIALS },
    '3-opt-stoch');
}
