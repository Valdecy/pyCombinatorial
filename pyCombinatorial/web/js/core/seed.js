// ============================================================================
// seed.js — random tour seeding (mirror of seed_function in many algos)
// ============================================================================

import { distanceCalc } from './distance.js';

/**
 * Seedable PRNG (mulberry32). Used so users can reproduce runs.
 * @param {number} seed
 */
export function makeRng(seed) {
  let s = seed >>> 0;
  return function () {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Fisher-Yates shuffle in place using provided rng.
 */
export function shuffle(arr, rng = Math.random) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

/**
 * Random initial tour (1-indexed, closed loop).
 * Mirrors seed_function() from sa.py / ga.py.
 */
export function seedFunction(distanceMatrix, rng = Math.random) {
  const n = distanceMatrix.length;
  const seq = Array.from({ length: n }, (_, i) => i + 1);
  shuffle(seq, rng);
  seq.push(seq[0]);
  return [seq, distanceCalc(distanceMatrix, seq)];
}

/**
 * Pick k distinct integers from [0,n) using rng.
 */
export function pickK(n, k, rng = Math.random) {
  const pool = Array.from({ length: n }, (_, i) => i);
  shuffle(pool, rng);
  return pool.slice(0, k);
}
