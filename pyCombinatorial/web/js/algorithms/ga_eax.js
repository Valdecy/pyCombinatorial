// ============================================================================
// ga_eax.js — Genetic Algorithm with Edge Assembly Crossover (GA-EAX)
// Mirrors the structure of algorithm/ga_eax.py using AB-cycle extraction,
// subtour reconnection, optional 2-opt polishing, and a simple two-stage mode.
// ============================================================================

import { distanceCalc } from '../core/distance.js';
import { localSearch2Opt, mulberry32 } from './_shared.js';

export const meta = {
  id: 'ga_eax',
  label: 'GA-EAX',
  category: 'Metaheuristic',
  description: 'Genetic Algorithm with Edge Assembly Crossover: AB-cycles recombine parent edges, then subtours are reconnected.',
  params: [
    { key: 'populationSize', label: 'Population',     type: 'int',  default: 30,  min: 4,   max: 300 },
    { key: 'offspringSize',  label: 'Offspring set',  type: 'int',  default: 30,  min: 1,   max: 300 },
    { key: 'generations',    label: 'Generations',    type: 'int',  default: 500, min: 1,   max: 5000 },
    { key: 'localSearch',    label: 'Apply 2-opt',    type: 'bool', default: true },
    { key: 'stageSwitch',    label: '2-stage mode',   type: 'bool', default: true },
    { key: 'seed',           label: 'Random seed',    type: 'int',  default: 42,  min: 0,   max: 99999 },
  ],
};

function route0To1(route0) {
  return [...route0.map(v => v + 1), route0[0] + 1];
}

function route1To0(route1) {
  const route = route1.slice();
  if (route.length > 1 && route[0] === route[route.length - 1]) route.pop();
  return route.map(v => v - 1);
}

function routeDistance0(distanceMatrix, route0) {
  let d = 0;
  for (let i = 0; i < route0.length; i++) d += distanceMatrix[route0[i]][route0[(i + 1) % route0.length]];
  return d;
}

function edgeKey(i, j) {
  return i <= j ? `${i}|${j}` : `${j}|${i}`;
}

function parseEdge(key) {
  const [a, b] = key.split('|').map(Number);
  return [a, b];
}

function edgeSetFromRoute(route0) {
  const s = new Set();
  for (let i = 0; i < route0.length; i++) s.add(edgeKey(route0[i], route0[(i + 1) % route0.length]));
  return s;
}

function adjacencyFromRoute(route0) {
  const n = route0.length;
  const adj = Array.from({ length: n }, () => new Set());
  for (let i = 0; i < n; i++) {
    const a = route0[i];
    const b = route0[(i + 1) % n];
    adj[a].add(b);
    adj[b].add(a);
  }
  return adj;
}

function validDegrees(adj) {
  return adj.every(nbrs => nbrs.size === 2);
}

function routeFromAdjacency(adj, start = 0) {
  const route = [start];
  let prev = -1;
  let curr = start;
  while (true) {
    const nbrs = [...adj[curr]];
    if (nbrs.length !== 2) throw new Error('Adjacency structure is not a Hamiltonian cycle');
    const nxt = nbrs[0] !== prev ? nbrs[0] : nbrs[1];
    if (nxt === start) break;
    route.push(nxt);
    prev = curr;
    curr = nxt;
    if (route.length > adj.length) throw new Error('Cycle reconstruction overflow');
  }
  if (route.length !== adj.length) throw new Error('Reconstructed route does not include all nodes');
  return route;
}

function connectedComponents(adj) {
  const visited = new Array(adj.length).fill(false);
  const comps = [];
  for (let s = 0; s < adj.length; s++) {
    if (visited[s]) continue;
    const stack = [s];
    visited[s] = true;
    const comp = [];
    while (stack.length) {
      const u = stack.pop();
      comp.push(u);
      for (const v of adj[u]) {
        if (!visited[v]) {
          visited[v] = true;
          stack.push(v);
        }
      }
    }
    comps.push(comp);
  }
  return comps;
}

function cycleRouteFromComponent(adj, component) {
  const start = component[0];
  const route = [start];
  let prev = -1;
  let curr = start;
  while (true) {
    const nbrs = [...adj[curr]];
    const nxt = nbrs[0] === prev ? nbrs[1] : nbrs[0];
    if (nxt === start) break;
    route.push(nxt);
    prev = curr;
    curr = nxt;
  }
  return route;
}

function cycleEdgesFromComponent(adj, component) {
  const route = cycleRouteFromComponent(adj, component);
  const edges = [];
  for (let i = 0; i < route.length; i++) {
    edges.push(parseEdge(edgeKey(route[i], route[(i + 1) % route.length])));
  }
  return edges;
}

function nearestCityList(distanceMatrix) {
  const n = distanceMatrix.length;
  const near = [];
  for (let i = 0; i < n; i++) {
    const order = Array.from({ length: n }, (_, j) => j).sort((a, b) => distanceMatrix[i][a] - distanceMatrix[i][b]);
    near.push(order);
  }
  return near;
}

function shuffleInPlace(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function randomRoute0(n, rng) {
  return shuffleInPlace(Array.from({ length: n }, (_, i) => i), rng);
}

function prepareInitialRoute(distanceMatrix, route, localSearch = true) {
  let route0 = Math.min(...route) >= 1 ? route1To0(route) : route.slice();
  let closed1 = route0To1(route0);
  let value = distanceCalc(distanceMatrix, closed1);
  if (localSearch) {
    const [optTour, optDist] = localSearch2Opt(distanceMatrix, closed1);
    closed1 = optTour;
    value = optDist;
    route0 = route1To0(closed1);
  }
  return { route: route0, distance: value };
}

function makePopulation(distanceMatrix, populationSize, rng, localSearch = true) {
  const n = distanceMatrix.length;
  const population = [];
  while (population.length < populationSize) {
    population.push(prepareInitialRoute(distanceMatrix, randomRoute0(n, rng), localSearch));
  }
  return population;
}

function computeEdgeFrequency(population) {
  const freq = new Map();
  for (const individual of population) {
    for (const edge of edgeSetFromRoute(individual.route)) {
      freq.set(edge, (freq.get(edge) || 0) + 1);
    }
  }
  return freq;
}

function fallbackRecombine(parentA, parentB, distanceMatrix, nearCities, rng) {
  const n = parentA.length;
  const adjA = adjacencyFromRoute(parentA);
  const adjB = adjacencyFromRoute(parentB);
  const start = Math.floor(rng() * n);
  const route = [start];
  const visited = new Set([start]);
  let curr = start;
  while (route.length < n) {
    const candidates = [...new Set([...adjA[curr], ...adjB[curr]])].filter(node => !visited.has(node));
    let nxt;
    if (candidates.length > 0) {
      nxt = candidates.reduce((best, node) => (distanceMatrix[curr][node] < distanceMatrix[curr][best] ? node : best), candidates[0]);
    } else {
      const remaining = nearCities[curr].filter(node => !visited.has(node));
      nxt = (remaining.length > 0 ? remaining : Array.from({ length: n }, (_, i) => i).filter(node => !visited.has(node)))[0];
    }
    route.push(nxt);
    visited.add(nxt);
    curr = nxt;
  }
  return route;
}

function extractAbCycles(parentA, parentB, distanceMatrix, rng) {
  const n = parentA.length;
  const edgesA = edgeSetFromRoute(parentA);
  const edgesB = edgeSetFromRoute(parentB);
  const onlyA = new Set([...edgesA].filter(edge => !edgesB.has(edge)));
  const onlyB = new Set([...edgesB].filter(edge => !edgesA.has(edge)));
  const adjA = Array.from({ length: n }, () => []);
  const adjB = Array.from({ length: n }, () => []);

  for (const edge of onlyA) {
    const [u, v] = parseEdge(edge);
    adjA[u].push(v);
    adjA[v].push(u);
  }
  for (const edge of onlyB) {
    const [u, v] = parseEdge(edge);
    adjB[u].push(v);
    adjB[v].push(u);
  }

  const cycles = [];
  const maxSteps = 4 * n + 10;
  while (onlyA.size > 0) {
    const onlyAList = [...onlyA];
    const startKey = onlyAList[Math.floor(rng() * onlyAList.length)];
    const [u, v] = parseEdge(startKey);
    const aEdges = [[u, v]];
    const bEdges = [];
    const nodeSet = new Set([u, v]);
    let prev = u;
    let curr = v;
    let nextType = 'B';
    let ok = false;
    let steps = 0;

    while (steps < maxSteps) {
      steps += 1;
      let candidates = (nextType === 'B' ? adjB[curr] : adjA[curr]).slice();
      if (candidates.length > 1 && candidates.includes(prev)) candidates = candidates.filter(x => x !== prev);
      if (candidates.length === 0) break;

      const preferred = [];
      for (const nxt of candidates) {
        const edge = edgeKey(curr, nxt);
        if (nextType === 'B' || onlyA.has(edge)) preferred.push(nxt);
      }
      if (preferred.length > 0) candidates = preferred;

      const nxt = candidates[Math.floor(rng() * candidates.length)];
      if (nextType === 'B') {
        bEdges.push([curr, nxt]);
        nextType = 'A';
      } else {
        aEdges.push([curr, nxt]);
        nextType = 'B';
      }
      nodeSet.add(nxt);
      prev = curr;
      curr = nxt;
      if (curr === u && nextType === 'A') {
        ok = true;
        break;
      }
    }

    if (ok && aEdges.length === bEdges.length && aEdges.length > 0) {
      for (const [i, j] of aEdges) onlyA.delete(edgeKey(i, j));
      let gain = 0;
      for (const [i, j] of aEdges) gain += distanceMatrix[i][j];
      for (const [i, j] of bEdges) gain -= distanceMatrix[i][j];
      cycles.push({ aEdges, bEdges, gain, nodeSet });
    } else {
      onlyA.delete(startKey);
    }
  }
  return cycles;
}

function buildMultiCycleSet(cycles, centerIdx, maxCycles = 3) {
  const selected = [centerIdx];
  const used = new Set(cycles[centerIdx].nodeSet);
  const candidates = Array.from({ length: cycles.length }, (_, idx) => idx)
    .filter(idx => idx !== centerIdx)
    .sort((a, b) => cycles[b].gain - cycles[a].gain);
  for (const idx of candidates) {
    if (selected.length >= maxCycles) break;
    let overlap = 0;
    for (const node of cycles[idx].nodeSet) if (used.has(node)) overlap += 1;
    if (overlap <= Math.max(1, Math.floor(cycles[idx].nodeSet.size / 4))) {
      selected.push(idx);
      for (const node of cycles[idx].nodeSet) used.add(node);
    }
  }
  return selected;
}

function applyCycle(adj, cycle) {
  for (const [u, v] of cycle.aEdges) {
    adj[u].delete(v);
    adj[v].delete(u);
  }
  for (const [u, v] of cycle.bEdges) {
    adj[u].add(v);
    adj[v].add(u);
  }
}

function reconnectSubtours(adj, distanceMatrix, nearCities) {
  while (true) {
    const components = connectedComponents(adj);
    if (components.length <= 1) return adj;

    const compIndex = new Map();
    components.forEach((comp, idx) => comp.forEach(node => compIndex.set(node, idx)));
    const center = components.reduce((best, comp) => (comp.length < best.length ? comp : best), components[0]);
    const centerNodes = new Set(center);
    const centerEdges = cycleEdgesFromComponent(adj, center);
    let bestMove = null;
    let bestGain = -Infinity;

    for (const [a, b] of centerEdges) {
      for (const anchor of [a, b]) {
        for (const c of nearCities[anchor].slice(1)) {
          if (centerNodes.has(c)) continue;
          for (const d of [...adj[c]]) {
            if (compIndex.get(d) !== compIndex.get(c)) continue;
            const delta1 = distanceMatrix[a][b] + distanceMatrix[c][d] - distanceMatrix[a][c] - distanceMatrix[b][d];
            if (delta1 > bestGain) { bestGain = delta1; bestMove = [a, b, c, d, 0]; }
            const delta2 = distanceMatrix[a][b] + distanceMatrix[c][d] - distanceMatrix[a][d] - distanceMatrix[b][c];
            if (delta2 > bestGain) { bestGain = delta2; bestMove = [a, b, c, d, 1]; }
          }
        }
      }
    }

    if (!bestMove) {
      const others = components.filter(comp => comp !== center);
      for (const [a, b] of centerEdges) {
        for (const comp of others) {
          for (const [c, d] of cycleEdgesFromComponent(adj, comp)) {
            const delta1 = distanceMatrix[a][b] + distanceMatrix[c][d] - distanceMatrix[a][c] - distanceMatrix[b][d];
            if (delta1 > bestGain) { bestGain = delta1; bestMove = [a, b, c, d, 0]; }
            const delta2 = distanceMatrix[a][b] + distanceMatrix[c][d] - distanceMatrix[a][d] - distanceMatrix[b][c];
            if (delta2 > bestGain) { bestGain = delta2; bestMove = [a, b, c, d, 1]; }
          }
        }
      }
    }

    if (!bestMove) throw new Error('Failed to reconnect subtours generated by EAX');

    const [a, b, c, d, mode] = bestMove;
    adj[a].delete(b); adj[b].delete(a);
    adj[c].delete(d); adj[d].delete(c);
    if (mode === 0) {
      adj[a].add(c); adj[c].add(a);
      adj[b].add(d); adj[d].add(b);
    } else {
      adj[a].add(d); adj[d].add(a);
      adj[b].add(c); adj[c].add(b);
    }
  }
}

function adpLoss(oldEdges, newEdges, edgeFreq) {
  let penalty = 0;
  for (const edge of oldEdges) {
    if (!newEdges.has(edge)) penalty -= Math.max((edgeFreq.get(edge) || 0) - 1, 0);
  }
  for (const edge of newEdges) {
    if (!oldEdges.has(edge)) penalty += edgeFreq.get(edge) || 0;
  }
  return Math.max(penalty, 1e-8);
}

function entropyLoss(oldEdges, newEdges, edgeFreq, populationSize) {
  const entropyTerm = (count) => {
    if (count <= 0 || populationSize <= 0) return 0;
    const p = count / populationSize;
    return -p * Math.log(p);
  };
  const changed = new Set([...oldEdges].filter(edge => !newEdges.has(edge)).concat([...newEdges].filter(edge => !oldEdges.has(edge))));
  let delta = 0;
  for (const edge of changed) {
    const before = edgeFreq.get(edge) || 0;
    let after = before;
    if (oldEdges.has(edge) && !newEdges.has(edge)) after -= 1;
    if (newEdges.has(edge) && !oldEdges.has(edge)) after += 1;
    delta += entropyTerm(after) - entropyTerm(before);
  }
  return Math.max(-delta, 1e-8);
}

function eaxCandidateFromPair(parentA, parentB, distanceMatrix, nearCities, edgeFreq, populationSize, offspringSize, stageMode, diversityMode, rng) {
  const cycles = extractAbCycles(parentA, parentB, distanceMatrix, rng);
  if (cycles.length === 0) {
    const child = fallbackRecombine(parentA, parentB, distanceMatrix, nearCities, rng);
    return { route: child, distance: routeDistance0(distanceMatrix, child) };
  }

  let order = Array.from({ length: cycles.length }, (_, i) => i);
  if (stageMode === 'single') shuffleInPlace(order, rng);
  else order.sort((a, b) => cycles[b].gain - cycles[a].gain);

  const oldEdges = edgeSetFromRoute(parentA);
  const parentDistance = routeDistance0(distanceMatrix, parentA);
  let bestChild = null;
  let bestDistance = Infinity;
  let bestPoint = -Infinity;

  for (const idx of order.slice(0, Math.min(offspringSize, order.length))) {
    const selectedCycles = stageMode === 'single' ? [idx] : buildMultiCycleSet(cycles, idx);
    const adj = adjacencyFromRoute(parentA);
    let valid = true;

    for (const cycleIdx of selectedCycles) {
      applyCycle(adj, cycles[cycleIdx]);
      if (!validDegrees(adj)) { valid = false; break; }
    }

    let child;
    if (valid) {
      try {
        reconnectSubtours(adj, distanceMatrix, nearCities);
        if (!validDegrees(adj)) valid = false;
        else child = routeFromAdjacency(adj, parentA[0]);
      } catch {
        valid = false;
      }
    }

    if (!valid || !child) child = fallbackRecombine(parentA, parentB, distanceMatrix, nearCities, rng);
    const childDistance = routeDistance0(distanceMatrix, child);
    const gain = parentDistance - childDistance;
    if (gain <= 0) continue;
    if (child.length === parentB.length && child.every((v, i) => v === parentB[i])) continue;

    const newEdges = edgeSetFromRoute(child);
    let loss = 1;
    if (diversityMode === 'distance') loss = adpLoss(oldEdges, newEdges, edgeFreq);
    else if (diversityMode === 'entropy') loss = entropyLoss(oldEdges, newEdges, edgeFreq, populationSize);
    const point = gain / Math.max(loss, 1e-8);

    if (point > bestPoint) {
      bestPoint = point;
      bestChild = child;
      bestDistance = childDistance;
    }
  }

  if (!bestChild) {
    const child = fallbackRecombine(parentA, parentB, distanceMatrix, nearCities, rng);
    return { route: child, distance: routeDistance0(distanceMatrix, child) };
  }
  return { route: bestChild, distance: bestDistance };
}

export async function* run(distanceMatrix, params) {
  const rng = mulberry32(params.seed ?? 42);
  const populationSize = Math.max(4, params.populationSize ?? 30);
  const offspringSize = Math.max(1, params.offspringSize ?? 30);
  const generations = Math.max(1, params.generations ?? 500);
  const localSearch = params.localSearch ?? true;
  const stageSwitch = params.stageSwitch ?? true;
  const diversityMode = 'entropy';

  const nearCities = nearestCityList(distanceMatrix);
  let population = makePopulation(distanceMatrix, populationSize, rng, localSearch);
  let edgeFreq = computeEdgeFrequency(population);

  let best = population.reduce((a, b) => (a.distance <= b.distance ? a : b));
  let bestRoute = best.route.slice();
  let bestDistance = best.distance;
  let stage = 1;
  let stageMode = 'single';
  let noImprove = 0;
  let stageReferenceGeneration = 0;
  let maxStageBest = 0;

  yield {
    phase: 'init',
    tour: route0To1(bestRoute),
    bestTour: route0To1(bestRoute),
    distance: bestDistance,
    bestDistance,
    iteration: 0,
    message: `pop ${populationSize}, stage ${stage}, start ${bestDistance.toFixed(2)}`,
  };

  for (let generation = 1; generation <= generations; generation++) {
    const matingOrder = shuffleInPlace(Array.from({ length: populationSize }, (_, i) => i), rng);
    matingOrder.push(matingOrder[0]);
    const previousBest = bestDistance;

    for (let s = 0; s < populationSize; s++) {
      const parentIndex = matingOrder[s];
      const mateIndex = matingOrder[s + 1];
      const parentA = population[parentIndex].route.slice();
      const parentB = population[mateIndex].route.slice();

      let { route: childRoute, distance: childDistance } = eaxCandidateFromPair(
        parentA,
        parentB,
        distanceMatrix,
        nearCities,
        edgeFreq,
        populationSize,
        offspringSize,
        stageMode,
        diversityMode,
        rng,
      );

      if (localSearch) {
        const [optTour, optDist] = localSearch2Opt(distanceMatrix, route0To1(childRoute));
        childRoute = route1To0(optTour);
        childDistance = optDist;
      }

      if (childDistance < population[parentIndex].distance) {
        const oldEdges = edgeSetFromRoute(population[parentIndex].route);
        const newEdges = edgeSetFromRoute(childRoute);
        for (const edge of oldEdges) {
          if (!newEdges.has(edge)) {
            const next = Math.max(0, (edgeFreq.get(edge) || 0) - 1);
            if (next === 0) edgeFreq.delete(edge);
            else edgeFreq.set(edge, next);
          }
        }
        for (const edge of newEdges) {
          if (!oldEdges.has(edge)) edgeFreq.set(edge, (edgeFreq.get(edge) || 0) + 1);
        }
        population[parentIndex] = { route: childRoute, distance: childDistance };
      }
    }

    const currentBest = population.reduce((a, b) => (a.distance <= b.distance ? a : b));
    const currentBestDistance = currentBest.distance;
    const currentAverage = population.reduce((acc, item) => acc + item.distance, 0) / population.length;

    let improved = false;
    if (currentBestDistance < bestDistance) {
      bestDistance = currentBestDistance;
      bestRoute = currentBest.route.slice();
      noImprove = 0;
      improved = true;
    } else {
      noImprove += 1;
    }

    if (stageSwitch) {
      const threshold = Math.max(1, Math.floor(1500 / Math.max(1, offspringSize)));
      if (stage === 1) {
        if (noImprove === threshold && maxStageBest === 0) {
          maxStageBest = Math.max(1, Math.floor(generation / 10));
        } else if (maxStageBest !== 0 && noImprove >= maxStageBest) {
          stage = 2;
          stageMode = 'multi';
          noImprove = 0;
          maxStageBest = 0;
          stageReferenceGeneration = generation;
        }
      } else {
        if (noImprove === threshold && maxStageBest === 0) {
          maxStageBest = Math.max(1, Math.floor(Math.max(1, generation - stageReferenceGeneration) / 10));
        } else if (maxStageBest !== 0 && noImprove >= maxStageBest) {
          yield {
            phase: improved ? 'improvement' : 'generation',
            tour: route0To1(currentBest.route),
            bestTour: route0To1(bestRoute),
            distance: currentBestDistance,
            bestDistance,
            iteration: generation,
            message: improved
              ? `★ stage ${stage} ${bestDistance.toFixed(2)}`
              : `gen ${generation}: ${currentBestDistance.toFixed(2)}  best ${bestDistance.toFixed(2)}  stage ${stage}`,
          };
          break;
        }
      }
    }

    yield {
      phase: improved ? 'improvement' : 'generation',
      tour: route0To1(currentBest.route),
      bestTour: route0To1(bestRoute),
      distance: currentBestDistance,
      bestDistance,
      iteration: generation,
      message: improved
        ? `★ stage ${stage} ${bestDistance.toFixed(2)}`
        : `gen ${generation}: ${currentBestDistance.toFixed(2)}  best ${bestDistance.toFixed(2)}  stage ${stage}`,
    };

    if (Math.abs(currentAverage - currentBestDistance) < 1e-10) break;
    if (currentBestDistance >= previousBest && generation >= generations) break;
  }

  return { tour: route0To1(bestRoute), distance: bestDistance, summary: `GA-EAX: ${bestDistance.toFixed(2)}` };
}
