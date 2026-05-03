// ============================================================================
// brkga.js — Biased Random-Key Genetic Algorithm
// Mirrors algorithm/brkga.py — encode tour as random-key chromosome,
// elite-driven biased crossover, mutants for diversity.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'brkga',
  label: 'BRKGA',
  category: 'Metaheuristic',
  description: 'Biased Random-Key GA: each gene is a [0,1) key; sorted permutation = tour.',
  params: [
    { key: 'populationSize', label: 'Population',  type: 'int',   default: 25,  min: 4,  max: 500 },
    { key: 'elite',          label: 'Elite size',  type: 'int',   default: 5,   min: 1,  max: 100 },
    { key: 'bias',           label: 'Elite bias',  type: 'float', default: 0.7, min: 0.5, max: 1, step: 0.01 },
    { key: 'mutants',        label: 'Mutants',     type: 'int',   default: 5,   min: 0,  max: 100 },
    { key: 'generations',    label: 'Generations', type: 'int',   default: 100, min: 1,  max: 5000 },
    { key: 'seed',           label: 'Random seed', type: 'int',   default: 42,  min: 0,  max: 99999 },
  ],
};

function decode(individual, distanceMatrix) {
  const order = Array.from({ length: individual.length }, (_, i) => i)
    .sort((a, b) => individual[a] - individual[b]);
  const tour = [...order.map(c => c + 1), order[0] + 1];
  return [tour, distanceCalc(distanceMatrix, tour)];
}

function randomKey(n, rng) {
  const k = new Array(n);
  for (let i = 0; i < n; i++) k[i] = rng();
  return k;
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const n = distanceMatrix.length;
  const popSize = params.populationSize ?? 25;
  const elite = Math.min(Math.max(1, params.elite ?? 5), popSize - 1);
  const mutants = Math.max(0, params.mutants ?? 5);
  const bias = params.bias ?? 0.7;
  const generations = params.generations ?? 100;

  let population = [];
  for (let i = 0; i < popSize; i++) population.push(randomKey(n, rng));
  let cost = population.map(p => decode(p, distanceMatrix)[1]);
  let order = Array.from({ length: popSize }, (_, i) => i).sort((a, b) => cost[a] - cost[b]);
  population = order.map(i => population[i]);
  cost = order.map(i => cost[i]);
  let eliteInd = [population[0].slice(), cost[0]];
  let [bestTour, bestDist] = decode(eliteInd[0], distanceMatrix);

  yield {
    phase: 'init',
    tour: bestTour, bestTour,
    distance: bestDist, bestDistance: bestDist,
    iteration: 0,
    message: `pop ${popSize}, start ${bestDist.toFixed(2)}`,
  };

  for (let gen = 0; gen < generations; gen++) {
    const offspring = population.map(p => p.slice());
    for (let i = elite; i < popSize; i++) {
      const p1Idx = Math.floor(rng() * elite);
      let p2Idx = elite + Math.floor(rng() * (popSize - elite));
      if (p2Idx >= popSize) p2Idx = popSize - 1;
      for (let j = 0; j < n; j++) {
        offspring[i][j] = rng() <= bias ? population[p1Idx][j] : population[p2Idx][j];
      }
    }
    // mutate the worst `mutants`
    for (let i = popSize - mutants; i < popSize; i++) {
      offspring[i] = randomKey(n, rng);
    }

    cost = offspring.map(p => decode(p, distanceMatrix)[1]);
    order = Array.from({ length: popSize }, (_, i) => i).sort((a, b) => cost[a] - cost[b]);
    population = order.map(i => offspring[i]);
    cost = order.map(i => cost[i]);

    const improved = cost[0] < eliteInd[1];
    if (improved) {
      eliteInd = [population[0].slice(), cost[0]];
      [bestTour, bestDist] = decode(eliteInd[0], distanceMatrix);
    }
    const [bestGenTour, bestGenDist] = decode(population[0], distanceMatrix);

    yield {
      phase: improved ? 'improvement' : 'generation',
      tour: bestGenTour, bestTour,
      distance: bestGenDist, bestDistance: bestDist,
      iteration: gen + 1,
      message: improved ? `★ ${bestDist.toFixed(2)}` : `gen ${gen + 1}: ${bestGenDist.toFixed(2)}  best ${bestDist.toFixed(2)}`,
    };
  }

  return { tour: bestTour, distance: bestDist, summary: `BRKGA: ${bestDist.toFixed(2)}` };
}
