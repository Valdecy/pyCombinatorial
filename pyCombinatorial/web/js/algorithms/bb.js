// ============================================================================
// bb.js — Branch & Bound (exact)
// Mirrors algorithm/bb.py, converted from recursion to iteration so the
// generator can yield at each expand / prune / backtrack / leaf event.
// ============================================================================

export const meta = {
  id: 'bb',
  label: 'Branch & Bound',
  category: 'Exact',
  description: 'Best-first DFS with lower-bound pruning. Optimal but exponential.',
  warnIf: { citiesAbove: 20, message: '> 20 cities may take a long time.' },
  params: [
    {
      key: 'maxNodes',
      label: 'Max nodes',
      type: 'int',
      default: 200000,
      min: 1000,
      max: 10000000,
      hint: 'Safety cap. The search aborts after this many expansions.',
    },
  ],
};

/* helpers: smallest and second-smallest outgoing edge from city i */
function min1(distanceMatrix, i) {
  let a = Infinity, b = Infinity;
  const row = distanceMatrix[i];
  for (let j = 0; j < row.length; j++) {
    if (j === i) continue;
    const v = row[j];
    if (v < a) { b = a; a = v; }
    else if (v < b) { b = v; }
  }
  return a;
}

function min2(distanceMatrix, i) {
  let a = Infinity, b = Infinity;
  const row = distanceMatrix[i];
  for (let j = 0; j < row.length; j++) {
    if (j === i) continue;
    const v = row[j];
    if (v < a) { b = a; a = v; }
    else if (v < b) { b = v; }
  }
  return b;
}

export async function* run(distanceMatrix, params) {
  const n = distanceMatrix.length;
  const maxNodes = params.maxNodes ?? 200000;

  if (n < 2) return { tour: null, distance: 0, summary: 'too few cities' };

  // precompute mins for speed
  const m1 = new Float64Array(n);
  const m2 = new Float64Array(n);
  for (let i = 0; i < n; i++) { m1[i] = min1(distanceMatrix, i); m2[i] = min2(distanceMatrix, i); }

  // initial bound = ceil( sum(min1 + min2) / 2 )
  let s = 0;
  for (let i = 0; i < n; i++) s += m1[i] + m2[i];
  const initBound = Math.ceil(s / 2);

  let bestDist = Infinity;
  let bestPath = null;
  let nodesExplored = 0;
  let nodesPruned = 0;
  let nodesBacktrack = 0;

  const path = new Array(n).fill(-1);
  path[0] = 0;
  const visited = new Array(n).fill(false);
  visited[0] = true;

  // a frame represents "we're currently deciding which city to put at position L"
  const stack = [{ L: 1, bound: initBound, weight: 0, nextChild: 0 }];

  while (stack.length > 0 && nodesExplored < maxNodes) {
    const frame = stack[stack.length - 1];
    const L = frame.L;
    const parent = path[L - 1];

    if (L === n) {
      // leaf — close the tour
      const closeDist = distanceMatrix[parent][path[0]];
      const total = frame.weight + closeDist;
      const improved = total < bestDist;
      if (improved) {
        bestDist = total;
        bestPath = [...path, path[0]].map(x => x + 1);
      }
      yield {
        phase: improved ? 'leaf-improve' : 'leaf',
        tour: bestPath ? [...bestPath] : null,
        bestTour: bestPath ? [...bestPath] : null,
        distance: bestDist,
        bestDistance: bestDist,
        partialPath: [...path],
        iteration: nodesExplored,
        message: improved
          ? `★ leaf: ${total.toFixed(2)} (best)`
          : `leaf: ${total.toFixed(2)} (≥ ${bestDist.toFixed(2)})`,
        extras: { nodesExplored, nodesPruned, nodesBacktrack, depth: L },
      };
      stack.pop();
      if (stack.length > 0) {
        visited[parent] = false;
        path[L - 1] = -1;
      }
      continue;
    }

    // find next valid child
    let i = frame.nextChild;
    while (i < n && (visited[i] || distanceMatrix[parent][i] === 0)) i++;

    if (i >= n) {
      // no more children — backtrack
      stack.pop();
      nodesBacktrack++;
      if (stack.length > 0) {
        visited[parent] = false;
        path[L - 1] = -1;
        yield {
          phase: 'backtrack',
          bestTour: bestPath ? [...bestPath] : null,
          distance: bestDist,
          bestDistance: bestDist,
          partialPath: [...path],
          iteration: nodesExplored,
          message: `← backtrack from L=${L}`,
          extras: { nodesExplored, nodesPruned, nodesBacktrack, depth: L - 1 },
        };
      }
      continue;
    }
    frame.nextChild = i + 1;

    const newWeight = frame.weight + distanceMatrix[parent][i];
    const mp = L === 1 ? m1[parent] : m2[parent];
    const newBound = frame.bound - (mp + m1[i]) / 2;

    if (newBound + newWeight >= bestDist) {
      nodesPruned++;
      yield {
        phase: 'prune',
        bestTour: bestPath ? [...bestPath] : null,
        distance: bestDist,
        bestDistance: bestDist,
        partialPath: [...path],
        candidates: [[parent, i]],
        iteration: nodesExplored,
        message: `× prune ${parent + 1}→${i + 1}  (lb=${(newBound + newWeight).toFixed(2)} ≥ ${bestDist.toFixed(2)})`,
        extras: { nodesExplored, nodesPruned, nodesBacktrack, depth: L },
      };
      continue;
    }

    // descend
    path[L] = i;
    visited[i] = true;
    nodesExplored++;
    stack.push({ L: L + 1, bound: newBound, weight: newWeight, nextChild: 0 });

    yield {
      phase: 'expand',
      bestTour: bestPath ? [...bestPath] : null,
      distance: bestDist,
      bestDistance: bestDist,
      partialPath: [...path],
      highlight: { type: 'edge', from: parent, to: i, color: '#5dd5e6' },
      iteration: nodesExplored,
      message: `→ expand ${parent + 1}→${i + 1}  (lb=${(newBound + newWeight).toFixed(2)})`,
      extras: { nodesExplored, nodesPruned, nodesBacktrack, depth: L + 1 },
    };
  }

  const aborted = nodesExplored >= maxNodes;
  return {
    tour: bestPath,
    distance: bestDist,
    summary: aborted
      ? `B&B aborted at ${nodesExplored} nodes; best so far ${bestDist.toFixed(2)}`
      : `B&B optimal: ${bestDist.toFixed(2)}  (explored ${nodesExplored}, pruned ${nodesPruned})`,
  };
}
