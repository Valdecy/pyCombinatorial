// ============================================================================
// hgs.js — Hybrid Genetic Search for the TSP
// Mirrors algorithm/hgs.py: population management with biased fitness,
// diversity control, ordered crossover, double-bridge mutation, and 2-opt.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { mulberry32 } from './_shared.js';

export const meta = {
  id: 'hgs',
  label: 'Hybrid Genetic Search',
  category: 'Metaheuristic',
  description: 'Hybrid Genetic Search: diversity-aware population management, OX crossover, double-bridge mutation, and granular 2-opt local search.',
  params: [
    { key: 'populationSize',    label: 'Population',            type: 'int',   default: 25,   min: 4,    max: 300 },
    { key: 'offspringSize',     label: 'Offspring / generation', type: 'int',   default: 40,   min: 1,    max: 500 },
    { key: 'elite',             label: 'Elite',                 type: 'int',   default: 4,    min: 1,    max: 100 },
    { key: 'closest',           label: 'Closest for diversity', type: 'int',   default: 5,    min: 1,    max: 100 },
    { key: 'mutationRate',      label: 'Mutation rate',         type: 'float', default: 0.25, min: 0,    max: 1, step: 0.01 },
    { key: 'candidates',        label: '2-opt candidates',      type: 'int',   default: 20,   min: 1,    max: 100 },
    { key: 'localSearch',       label: 'Local search',          type: 'bool',  default: true },
    { key: 'localSearchPasses', label: '2-opt passes',          type: 'int',   default: 50,   min: 1,    max: 200 },
    { key: 'generations',       label: 'Generations',           type: 'int',   default: 500,  min: 1,    max: 5000 },
    { key: 'maxNoImprovement',  label: 'No-improvement stop',   type: 'int',   default: 150,  min: 1,    max: 5000 },
    { key: 'seed',              label: 'Random seed',           type: 'int',   default: 42,   min: 0,    max: 99999 },
  ],
};

function routeCost(distanceMatrix, route) {
  let distance = 0.0;
  const n = route.length;
  for (let i = 0; i < n; i++) {
    distance += distanceMatrix[route[i]][route[(i + 1) % n]];
  }
  return distance;
}

function toCityTour(route) {
  const tour = route.map(c => c + 1);
  tour.push(tour[0]);
  return tour;
}

function isSymmetric(distanceMatrix, atol = 1e-10) {
  const n = distanceMatrix.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (Math.abs(distanceMatrix[i][j] - distanceMatrix[j][i]) > atol) return false;
    }
  }
  return true;
}

function candidateLists(distanceMatrix, candidates) {
  const n = distanceMatrix.length;
  const k = Math.max(1, Math.min(Math.floor(candidates), n - 1));
  const lists = [];
  for (let i = 0; i < n; i++) {
    const row = [];
    for (let j = 0; j < n; j++) {
      if (j !== i) row.push([j, distanceMatrix[i][j]]);
    }
    row.sort((a, b) => a[1] - b[1] || a[0] - b[0]);
    lists.push(row.slice(0, k).map(x => x[0]));
  }
  return lists;
}

function edgeSet(route, symmetric) {
  const n = route.length;
  const edges = new Set();
  for (let i = 0; i < n; i++) {
    let a = route[i];
    let b = route[(i + 1) % n];
    if (symmetric && a > b) [a, b] = [b, a];
    edges.add(`${a},${b}`);
  }
  return edges;
}

function brokenPairsDistance(edgesA, edgesB, n) {
  let common = 0;
  for (const e of edgesA) if (edgesB.has(e)) common++;
  return 1.0 - common / n;
}

function averageDistanceToClosest(individual, population, closest) {
  if (population.length <= 1) return 1.0;
  const distances = [];
  const n = individual.route.length;
  for (const other of population) {
    if (other === individual) continue;
    distances.push(brokenPairsDistance(individual.edges, other.edges, n));
  }
  distances.sort((a, b) => a - b);
  const k = Math.min(Math.floor(closest), distances.length);
  if (k <= 0) return 1.0;
  let sum = 0.0;
  for (let i = 0; i < k; i++) sum += distances[i];
  return sum / k;
}

function makeIndividual(distanceMatrix, route, symmetric) {
  const r = route.slice();
  return {
    route: r,
    cost: routeCost(distanceMatrix, r),
    edges: edgeSet(r, symmetric),
    fitness: 0.0,
  };
}

function normalizeRoute(route) {
  const r = route.slice();
  const p = r.indexOf(0);
  if (p >= 0) return r.slice(p).concat(r.slice(0, p));
  return r;
}

function randInt(rng, maxExclusive) {
  return Math.floor(rng() * maxExclusive);
}

function randomRoute(n, rng) {
  const route = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = randInt(rng, i + 1);
    [route[i], route[j]] = [route[j], route[i]];
  }
  return normalizeRoute(route);
}

function randomizedNearestNeighbor(distanceMatrix, rng, restrictedCandidateList = 3) {
  const n = distanceMatrix.length;
  const start = randInt(rng, n);
  const unvisited = new Set(Array.from({ length: n }, (_, i) => i));
  unvisited.delete(start);
  const route = [start];
  let current = start;
  const rclSize = Math.max(1, Math.floor(restrictedCandidateList));

  while (unvisited.size > 0) {
    const ranked = [...unvisited].sort((a, b) => distanceMatrix[current][a] - distanceMatrix[current][b] || a - b);
    const limit = Math.min(rclSize, ranked.length);
    const next = ranked[randInt(rng, limit)];
    route.push(next);
    unvisited.delete(next);
    current = next;
  }
  return normalizeRoute(route);
}

function orderedCrossover(parentA, parentB, rng) {
  const n = parentA.length;
  let i = randInt(rng, n);
  let j = randInt(rng, n);
  while (i === j) j = randInt(rng, n);
  if (i > j) [i, j] = [j, i];

  const child = new Array(n).fill(-1);
  for (let k = i; k <= j; k++) child[k] = parentA[k];
  const used = new Set(child.slice(i, j + 1));
  let fillPos = (j + 1) % n;
  let scanPos = (j + 1) % n;

  for (let k = 0; k < n; k++) {
    const city = parentB[scanPos];
    if (!used.has(city)) {
      child[fillPos] = city;
      fillPos = (fillPos + 1) % n;
      used.add(city);
    }
    scanPos = (scanPos + 1) % n;
  }
  return normalizeRoute(child);
}

function swapMutation(route, rng) {
  const r = route.slice();
  const n = r.length;
  let i = randInt(rng, n);
  let j = randInt(rng, n);
  while (i === j) j = randInt(rng, n);
  [r[i], r[j]] = [r[j], r[i]];
  return normalizeRoute(r);
}

function doubleBridge(route, rng) {
  const n = route.length;
  if (n < 8) return swapMutation(route, rng);
  const cuts = new Set();
  while (cuts.size < 4) cuts.add(1 + randInt(rng, n - 1));
  const [a, b, c, d] = [...cuts].sort((x, y) => x - y);
  const newRoute = route.slice(0, a)
    .concat(route.slice(c, d), route.slice(b, c), route.slice(a, b), route.slice(d, n));
  return normalizeRoute(newRoute);
}

function twoOptLocalSearch(distanceMatrix, route, candidate, maxPasses = 50) {
  const n = route.length;
  const r = route.slice();
  let bestCost = routeCost(distanceMatrix, r);
  const eps = 1e-12;
  let passes = 0;
  let improved = true;

  while (improved && passes < maxPasses) {
    improved = false;
    passes++;
    const pos = new Array(n);
    for (let idx = 0; idx < n; idx++) pos[r[idx]] = idx;

    for (let i = 0; i < n - 1; i++) {
      const a = r[i];
      const b = r[(i + 1) % n];
      for (const c of candidate[a]) {
        const j = pos[c];
        if (j <= i + 1) continue;
        if (i === 0 && j === n - 1) continue;
        const d = r[(j + 1) % n];
        const delta = distanceMatrix[a][c] + distanceMatrix[b][d] - distanceMatrix[a][b] - distanceMatrix[c][d];
        if (delta < -eps) {
          const seg = r.slice(i + 1, j + 1).reverse();
          for (let k = 0; k < seg.length; k++) r[i + 1 + k] = seg[k];
          bestCost += delta;
          improved = true;
          break;
        }
      }
      if (improved) break;
    }
  }
  return [normalizeRoute(r), bestCost];
}

function updateBiasedFitness(population, elite, closest) {
  if (population.length === 0) return;
  population.sort((a, b) => a.cost - b.cost);
  const nPop = population.length;
  if (nPop === 1) {
    population[0].fitness = 0.0;
    return;
  }

  const diversity = population.map(ind => averageDistanceToClosest(ind, population, closest));
  const costOrder = Array.from({ length: nPop }, (_, i) => i).sort((a, b) => population[a].cost - population[b].cost);
  const divOrder = Array.from({ length: nPop }, (_, i) => i).sort((a, b) => diversity[b] - diversity[a]);
  const costRank = new Array(nPop).fill(0);
  const divRank = new Array(nPop).fill(0);

  for (let r = 0; r < nPop; r++) costRank[costOrder[r]] = r;
  for (let r = 0; r < nPop; r++) divRank[divOrder[r]] = r;

  const eliteCount = Math.max(1, Math.min(Math.floor(elite), nPop));
  for (let i = 0; i < nPop; i++) {
    const fitRank = costRank[i] / (nPop - 1);
    const divContributionRank = divRank[i] / (nPop - 1);
    population[i].fitness = nPop <= eliteCount
      ? fitRank
      : fitRank + (1.0 - eliteCount / nPop) * divContributionRank;
  }
}

function uniquePopulation(population) {
  const unique = new Map();
  for (const ind of population) {
    const key = ind.route.join(',');
    if (!unique.has(key) || ind.cost < unique.get(key).cost) unique.set(key, ind);
  }
  return [...unique.values()];
}

function survivorSelection(population, populationSize, elite, closest) {
  let pop = uniquePopulation(population);
  updateBiasedFitness(pop, elite, closest);
  while (pop.length > populationSize) {
    let worstIdx = 0;
    for (let i = 1; i < pop.length; i++) {
      if (pop[i].fitness > pop[worstIdx].fitness) worstIdx = i;
    }
    pop.splice(worstIdx, 1);
    updateBiasedFitness(pop, elite, closest);
  }
  pop.sort((a, b) => a.cost - b.cost);
  return pop;
}

function binaryTournament(population, rng) {
  const n = population.length;
  let a = randInt(rng, n);
  let b = randInt(rng, n);
  while (a === b) b = randInt(rng, n);
  return population[a].fitness <= population[b].fitness ? population[a] : population[b];
}

function cloneBest(individual) {
  return {
    route: individual.route.slice(),
    cost: individual.cost,
    edges: new Set(individual.edges),
    fitness: individual.fitness,
  };
}

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const rng = mulberry32(params.seed ?? 42);
  const symmetric = isSymmetric(distanceMatrix);
  const populationSize = Math.max(4, Math.floor(params.populationSize ?? 25));
  const offspringSize = Math.max(1, Math.floor(params.offspringSize ?? 40));
  const elite = Math.max(1, Math.floor(params.elite ?? 4));
  const closest = Math.max(1, Math.floor(params.closest ?? 5));
  const mutationRate = Math.min(1, Math.max(0, Number(params.mutationRate ?? 0.25)));
  const candidates = Math.max(1, Math.floor(params.candidates ?? 20));
  const localSearch = params.localSearch !== false;
  const localSearchPasses = Math.max(1, Math.floor(params.localSearchPasses ?? 50));
  const generations = Math.max(1, Math.floor(params.generations ?? 500));
  const maxNoImprovement = Math.max(1, Math.floor(params.maxNoImprovement ?? 150));
  const candidate = candidateLists(distanceMatrix, candidates);

  let population = [];
  const initializationSize = Math.max(populationSize * 2, populationSize + offspringSize);

  for (let i = 0; i < initializationSize; i++) {
    let route = i < Math.floor(initializationSize / 2)
      ? randomizedNearestNeighbor(distanceMatrix, rng, 3)
      : randomRoute(n, rng);
    if (localSearch) [route] = twoOptLocalSearch(distanceMatrix, route, candidate, localSearchPasses);
    population.push(makeIndividual(distanceMatrix, route, symmetric));
  }

  population = survivorSelection(population, populationSize, elite, closest);
  let best = cloneBest(population[0]);
  let noImprovement = 0;
  let bestTour = toCityTour(best.route);
  let bestDistance = distanceCalc(distanceMatrix, bestTour);

  yield {
    phase: 'init',
    tour: bestTour,
    bestTour,
    distance: bestDistance,
    bestDistance,
    iteration: 0,
    message: `pop ${population.length}, start ${bestDistance.toFixed(2)}`,
  };

  for (let gen = 1; gen <= generations; gen++) {
    updateBiasedFitness(population, elite, closest);
    const offspring = [];

    for (let i = 0; i < offspringSize; i++) {
      const parentA = binaryTournament(population, rng);
      let parentB = binaryTournament(population, rng);
      let trials = 0;
      while (parentA === parentB && trials < 10) {
        parentB = binaryTournament(population, rng);
        trials++;
      }

      let childRoute = orderedCrossover(parentA.route, parentB.route, rng);
      if (rng() <= mutationRate) childRoute = doubleBridge(childRoute, rng);
      if (localSearch) [childRoute] = twoOptLocalSearch(distanceMatrix, childRoute, candidate, localSearchPasses);
      offspring.push(makeIndividual(distanceMatrix, childRoute, symmetric));
    }

    population = survivorSelection(population.concat(offspring), populationSize, elite, closest);

    const improved = population[0].cost < best.cost - 1e-12;
    if (improved) {
      best = cloneBest(population[0]);
      noImprovement = 0;
      bestTour = toCityTour(best.route);
      bestDistance = distanceCalc(distanceMatrix, bestTour);
    } else {
      noImprovement++;
    }

    const currentTour = toCityTour(population[0].route);
    const currentDistance = distanceCalc(distanceMatrix, currentTour);

    yield {
      phase: improved ? 'improvement' : 'generation',
      tour: currentTour,
      bestTour,
      distance: currentDistance,
      bestDistance,
      iteration: gen,
      message: improved ? `★ ${bestDistance.toFixed(2)}` : `gen ${gen}: ${currentDistance.toFixed(2)}  best ${bestDistance.toFixed(2)}`,
    };

    if (noImprovement >= maxNoImprovement) break;
  }

  return { tour: bestTour, distance: bestDistance, summary: `HGS: ${bestDistance.toFixed(2)}` };
}
