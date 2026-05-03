// ============================================================================
// opt_2_5.js — Local Search 2.5-opt
// Mirrors algorithm/opt_2_5.py — for each (i,j) try the 2-opt segment reversal
// AND every "remove-and-reinsert" of cities from the segment after j into
// positions inside (i, j].
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { seedFunction, makeRng } from '../core/seed.js';

export const meta = {
  id: 'opt_2_5',
  label: '2.5-opt',
  category: 'Local search',
  description: '2-opt segment reversal plus relocation of post-segment cities into the reversed segment.',
  params: [
    { key: 'recursiveSeeding', label: 'Recursive seeding', type: 'int', default: -1, min: -1, max: 50 },
    { key: 'seed', label: 'Random seed', type: 'int', default: 42, min: 0, max: 99999 },
  ],
};

export async function* run(distanceMatrix, params) {
  const rng = makeRng(params.seed ?? 42);
  const recursive = params.recursiveSeeding ?? -1;

  let cityList = params._initialTour
    ? [params._initialTour.slice(0, -1), distanceCalc(distanceMatrix, params._initialTour)]
    : (() => { const s = seedFunction(distanceMatrix, rng); return [s[0].slice(0, -1), s[1]]; })();

  const close = arr => [...arr, arr[0]];
  yield {
    phase: 'init', tour: close(cityList[0]), bestTour: close(cityList[0]),
    distance: cityList[1], bestDistance: cityList[1], iteration: 0,
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

    const n = cityList[0].length;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n + (i > 0 ? 1 : 0); j++) {
        // base 2-opt reversal
        const base = cityList[0].slice();
        const seg = base.slice(i, j + 1).reverse();
        for (let s = 0; s < seg.length; s++) base[i + s] = seg[s];
        attempts++;
        let bestCand = base, bestD = distanceCalc(distanceMatrix, close(base));

        // 2.5: take cities k from base[j+1..] and insert at each pos in (i, j]
        const insertion = base.slice(j + 1);
        const positions = [];
        for (let p = i + 1; p <= j; p++) positions.push(p);
        for (const k of insertion) {
          // remove k
          const removed = base.filter(x => x !== k);
          for (const pos of positions) {
            attempts++;
            const cand = removed.slice();
            cand.splice(pos, 0, k);
            const d = distanceCalc(distanceMatrix, close(cand));
            if (d < bestD) { bestD = d; bestCand = cand; }
          }
        }

        if (bestD < cityList[1]) {
          cityList = [bestCand, bestD];
          improvedThisPass = true;
          improvements++;
          yield {
            phase: 'improvement',
            tour: close(bestCand), bestTour: close(bestCand),
            distance: bestD, bestDistance: bestD,
            iteration: pass, attempts, improvements,
            message: `(${i},${j}) → ${bestD.toFixed(2)}`,
          };
        }
      }
    }

    if (!improvedThisPass) {
      yield { phase: 'pass-done',
              tour: close(cityList[0]), bestTour: close(cityList[0]),
              distance: cityList[1], bestDistance: cityList[1],
              iteration: pass, attempts, improvements,
              message: `pass ${pass}: no improvement` };
    }
    count++;
    if (priorBest > cityList[1] && recursive < 0) { priorBest = cityList[1]; count = -2; target = -1; }
    else if (cityList[1] >= priorBest && recursive < 0) { count = -1; target = -2; }
  }

  return { tour: close(cityList[0]), distance: cityList[1],
           summary: `2.5-opt: ${cityList[1].toFixed(2)} (${improvements}/${attempts})` };
}
