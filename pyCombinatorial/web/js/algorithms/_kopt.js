// ============================================================================
// _kopt.js — generic k-opt engine driven by trial templates.
//
// Shared back-end for opt_3, opt_4, opt_5 and their stochastic variants.
// Templates encode each trial as an array of k codes; each code is:
//   low 3 bits = segment index (0=A, 1=B, 2=C, 3=D, 4=E)
//   bit 3      = reversed flag
// (See _kopt_trials.js — auto-extracted from the Python sources.)
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

/* enumerate all (i_1 < i_2 < ... < i_k) with i_k allowed to extend by 1 if i_1>0
   matches the Python `segments_k_opt(n)` exactly. */
export function enumerateSegments(n, k) {
  const out = [];
  const choose = (start, depth, prefix) => {
    if (depth === k) { out.push(prefix.slice()); return; }
    const isFirst = depth === 0;
    const last = depth === k - 1;
    const upper = last ? (n + (prefix[0] > 0 ? 1 : 0)) : n;
    for (let i = (isFirst ? 0 : start); i < upper; i++) {
      prefix.push(i);
      choose(i + 1, depth + 1, prefix);
      prefix.pop();
    }
  };
  choose(0, 0, []);
  return out;
}

/* Build each segment from the open tour and indices.
   For k segments with picks [i_1, ..., i_k]:
     S_0 = tour[0..i_1+1] + tour[i_1+1..i_2+1]   (the "A"/"a" segment includes prefix + first piece)
     S_1 = tour[i_2+1..i_3+1]                    (the "B" segment)
     S_2 = tour[i_3+1..i_4+1]                    (the "C" segment)  ...
   For k=3: A includes [0..j+1], B = [j+1..k+1], C = [k+1..]
   Reversal of S_0 ("a") only reverses the [i_1+1..i_2+1] part, prefix stays.
*/
function buildSegments(tour, picks) {
  const k = picks.length;
  const segs = new Array(k);
  // S_0 = prefix + first inner piece, but reversal only flips inner piece
  const prefix = tour.slice(0, picks[0] + 1);
  const firstInner = tour.slice(picks[0] + 1, picks[1] + 1);
  segs[0] = { prefix, body: firstInner };
  for (let s = 1; s < k; s++) {
    const start = picks[s] + 1;
    const end = (s + 1 < k) ? picks[s + 1] + 1 : tour.length;
    segs[s] = { prefix: null, body: tour.slice(start, end) };
  }
  return segs;
}

function applyTrial(segs, template) {
  const out = [];
  for (const code of template) {
    const idx = code & 7;
    const rev = (code & 8) !== 0;
    const seg = segs[idx];
    if (idx === 0) {
      out.push(...seg.prefix);
      if (rev) {
        for (let i = seg.body.length - 1; i >= 0; i--) out.push(seg.body[i]);
      } else {
        out.push(...seg.body);
      }
    } else {
      if (rev) {
        for (let i = seg.body.length - 1; i >= 0; i--) out.push(seg.body[i]);
      } else {
        out.push(...seg.body);
      }
    }
  }
  return out;
}

/**
 * Run a k-opt local search.
 * @param {Array<Array<number>>} distanceMatrix
 * @param {Object} params
 *   - kopt_k:        which k (3, 4, 5)
 *   - templates:     array of trial templates
 *   - recursiveSeeding: -1 = run until no improvement; otherwise fixed passes
 *   - search:        if > 0, sample only `search` segment tuples per pass (stochastic)
 *   - seed:          PRNG seed
 *   - _initialTour:  optional starting tour (1-indexed closed)
 *   - showAllAttempts: emit on every trial (very slow)
 * @yields  visualization frames
 */
export async function* runKopt(distanceMatrix, params, label = 'k-opt') {
  const k = params.kopt_k;
  const templates = params.templates;
  const recursive = params.recursiveSeeding ?? -1;
  const sample = params.search ?? 0;          // 0 = exhaustive
  const showAll = !!params.showAllAttempts;
  const rng = makeRng(params.seed ?? 42);

  let cityList;
  if (params._initialTour) {
    const t = [...params._initialTour];
    cityList = [t.slice(0, -1), distanceCalc(distanceMatrix, t)];
  } else {
    const seeded = seedFunction(distanceMatrix, rng);
    cityList = [seeded[0].slice(0, -1), seeded[1]];
  }

  const closeTour = arr => [...arr, arr[0]];
  yield {
    phase: 'init',
    tour: closeTour(cityList[0]),
    bestTour: closeTour(cityList[0]),
    distance: cityList[1],
    bestDistance: cityList[1],
    iteration: 0,
    message: `start ${cityList[1].toFixed(2)}`,
  };

  let priorBest = cityList[1] * 2;
  let count, target;
  if (recursive < 0) { count = -2; target = -1; }
  else { count = 0; target = recursive; }

  let pass = 0, attempts = 0, improvements = 0;

  while (count < target) {
    pass++;
    let improvedThisPass = false;

    let tuples = enumerateSegments(cityList[0].length, k);
    if (sample > 0 && sample < tuples.length) {
      // Fisher-Yates to take random `sample` tuples
      for (let i = tuples.length - 1; i > 0; i--) {
        const j = Math.floor(rng() * (i + 1));
        [tuples[i], tuples[j]] = [tuples[j], tuples[i]];
      }
      tuples = tuples.slice(0, sample);
    }

    for (const picks of tuples) {
      const segs = buildSegments(cityList[0], picks);
      for (const tmpl of templates) {
        attempts++;
        const cand = applyTrial(segs, tmpl);
        const closed = closeTour(cand);
        const d = distanceCalc(distanceMatrix, closed);
        if (showAll) {
          yield {
            phase: 'attempt',
            tour: closeTour(cityList[0]),
            bestTour: closeTour(cityList[0]),
            distance: cityList[1], bestDistance: cityList[1],
            iteration: pass, attempts, improvements,
            message: `try ${picks.join(',')} ⇒ ${d.toFixed(2)}`,
          };
        }
        if (d < cityList[1]) {
          cityList = [cand, d];
          improvedThisPass = true;
          improvements++;
          yield {
            phase: 'improvement',
            tour: closeTour(cand),
            bestTour: closeTour(cand),
            distance: d, bestDistance: d,
            iteration: pass, attempts, improvements,
            message: `${label} ${picks.join(',')}: ${d.toFixed(2)}`,
          };
        }
      }
    }

    if (!improvedThisPass) {
      yield {
        phase: 'pass-done',
        tour: closeTour(cityList[0]),
        bestTour: closeTour(cityList[0]),
        distance: cityList[1], bestDistance: cityList[1],
        iteration: pass, attempts, improvements,
        message: `pass ${pass}: no improvement`,
      };
    }

    count++;
    if (priorBest > cityList[1] && recursive < 0) {
      priorBest = cityList[1]; count = -2; target = -1;
    } else if (cityList[1] >= priorBest && recursive < 0) {
      count = -1; target = -2;
    }
  }

  return {
    tour: closeTour(cityList[0]),
    distance: cityList[1],
    summary: `${label} complete: ${cityList[1].toFixed(2)} (${improvements}/${attempts})`,
  };
}
