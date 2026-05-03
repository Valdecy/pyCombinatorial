// ============================================================================
// dataset.js — input handling, presets, parsers
// ============================================================================

import { makeRng } from './seed.js';

/**
 * Berlin52 — classic TSP benchmark, 52 cities. Optimal ≈ 7544.37.
 */
export const BERLIN52 = [
  [565,575],[25,185],[345,750],[945,685],[845,655],[880,660],[25,230],[525,1000],
  [580,1175],[650,1130],[1605,620],[1220,580],[1465,200],[1530,5],[845,680],
  [725,370],[145,665],[415,635],[510,875],[560,365],[300,465],[520,585],[480,415],
  [835,625],[975,580],[1215,245],[1320,315],[1250,400],[660,180],[410,250],
  [420,555],[575,665],[1150,1160],[700,580],[685,595],[685,610],[770,610],[795,645],
  [720,635],[760,650],[475,960],[95,260],[875,920],[700,500],[555,815],[830,485],
  [1170,65],[830,610],[605,625],[595,360],[1340,725],[1740,245]
];

/**
 * Att48 — 48 US capitals (compact). Optimal ≈ 33523.7.
 */
export const ATT48 = [
  [6734,1453],[2233,10],[5530,1424],[401,841],[3082,1644],[7608,4458],[7573,3716],
  [7265,1268],[6898,1885],[1112,2049],[5468,2606],[5989,2873],[4706,2674],
  [4612,2035],[6347,2683],[6107,669],[7611,5184],[7462,3590],[7732,4723],[5900,3561],
  [4483,3369],[6101,1110],[5199,2182],[1633,2809],[4307,2322],[675,1006],[7555,4819],
  [7541,3981],[3177,756],[7352,4506],[7545,2801],[3245,3305],[6426,3173],[4608,1198],
  [23,2216],[7248,3779],[7762,4595],[7392,2244],[3484,2829],[6271,2135],[4985,140],
  [1916,1569],[7280,4899],[7509,3239],[10,2676],[6807,2993],[5185,3258],[3023,1942]
];

/**
 * Tiny example: ulysses-style ring of 16 cities.
 */
export const RING16 = (() => {
  const out = [];
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2;
    out.push([500 + 400 * Math.cos(a), 500 + 400 * Math.sin(a)]);
  }
  return out;
})();

/**
 * Tiny grid (good for branch & bound — 9 cities).
 */
export const GRID9 = [
  [100,100],[300,100],[500,100],
  [100,300],[300,300],[500,300],
  [100,500],[300,500],[500,500]
];

/**
 * Four visible clusters (60 cities). Great for showing where greedy heuristics
 * struggle vs. methods that perceive structure (hull, spectral, GA).
 * Deterministic via inline pseudo-random.
 */
export const CLUSTERS60 = (() => {
  const out = [];
  const centers = [[200, 200], [800, 200], [200, 800], [800, 800]];
  let s = 12345;
  const rand = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
  for (let c = 0; c < 4; c++) {
    for (let i = 0; i < 15; i++) {
      const r = 90 * Math.sqrt(rand());
      const a = rand() * Math.PI * 2;
      out.push([
        centers[c][0] + r * Math.cos(a),
        centers[c][1] + r * Math.sin(a),
      ]);
    }
  }
  return out;
})();

/**
 * Spiral of 40 cities — a tour that follows the spiral inward is near-optimal,
 * which is unusual and trips up many heuristics.
 */
export const SPIRAL40 = (() => {
  const out = [];
  for (let i = 0; i < 40; i++) {
    const t = (i / 39) * Math.PI * 4.5;
    const r = 60 + 14 * t;
    out.push([500 + r * Math.cos(t), 500 + r * Math.sin(t)]);
  }
  return out;
})();

export const PRESETS = {
  'berlin52':   { name: 'Berlin 52',   coords: BERLIN52,   optimum: 7544.37,
                  notes: 'classic TSPLIB benchmark' },
  'att48':      { name: 'ATT 48',      coords: ATT48,      optimum: 33523.7,
                  notes: 'US capitals; non-Euclidean optimum reference' },
  'clusters60': { name: 'Clusters 60', coords: CLUSTERS60, optimum: null,
                  notes: '4 visible clusters — tests structure-aware methods' },
  'spiral40':   { name: 'Spiral 40',   coords: SPIRAL40,   optimum: null,
                  notes: 'tour following the spiral is near-optimal' },
  'ring16':     { name: 'Ring 16',     coords: RING16,     optimum: 2497.18,
                  notes: 'analytic optimum 16·800·sin(π/16) ≈ 2497.18' },
  'grid9':      { name: 'Grid 9',      coords: GRID9,      optimum: 1882.84,
                  notes: '3×3 grid; verified optimum' },
};

/**
 * Parse coordinates from text. Accepts:
 *   - CSV / TSV with optional header
 *   - "x y" pairs one per line
 *   - "x,y" or "x, y"
 * Returns array of [x, y] tuples.
 */
export function parseCoords(text) {
  const lines = text
    .split(/\r?\n/)
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#'));

  const out = [];
  let skippedHeader = false;

  for (const line of lines) {
    const parts = line.split(/[\s,;\t]+/).filter(Boolean);
    if (parts.length < 2) continue;

    // try last two fields as x,y (handles "id x y" format too)
    const a = parts.length >= 3 ? parts[parts.length - 2] : parts[0];
    const b = parts[parts.length - 1];
    const x = parseFloat(a);
    const y = parseFloat(b);

    if (Number.isFinite(x) && Number.isFinite(y)) {
      out.push([x, y]);
    } else if (!skippedHeader) {
      skippedHeader = true; // probably a header row
    }
  }

  return out;
}

/**
 * Random uniform points in [0, w] x [0, h].
 */
export function generateRandom(n, w = 1000, h = 1000, seed = null) {
  const rng = seed != null ? makeRng(seed) : Math.random;
  const out = [];
  for (let i = 0; i < n; i++) {
    out.push([rng() * w, rng() * h]);
  }
  return out;
}

/**
 * Compute bounding box of coords with optional padding.
 * Returns { minX, minY, maxX, maxY, width, height }.
 */
export function boundingBox(coords, padFrac = 0.05) {
  if (coords.length === 0) return { minX:0, minY:0, maxX:1, maxY:1, width:1, height:1 };
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const [x, y] of coords) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  const w = Math.max(1, maxX - minX);
  const h = Math.max(1, maxY - minY);
  const pad = Math.max(w, h) * padFrac;
  return {
    minX: minX - pad, minY: minY - pad,
    maxX: maxX + pad, maxY: maxY + pad,
    width: w + 2 * pad, height: h + 2 * pad,
  };
}

/**
 * Parse a TSPLIB-format file. Supports NODE_COORD_SECTION and the common
 * EDGE_WEIGHT_TYPE values (EUC_2D, ATT, GEO are all rendered as-is —
 * the visualization remains valid even if the official TSPLIB distance
 * formula differs from straight Euclidean).
 *
 * Returns { coords, name, edgeWeightType, dimension }.
 */
export function parseTSPLIB(text) {
  const lines = text.split(/\r?\n/);
  const out = { coords: [], name: null, edgeWeightType: null, dimension: null };
  let inCoords = false;

  for (let raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const upper = line.toUpperCase();

    if (upper === 'EOF' || upper === 'TOUR_SECTION') break;

    if (!inCoords) {
      if (upper.startsWith('NAME')) {
        out.name = line.split(/[:\s]+/).slice(1).join(' ').trim() || null;
      } else if (upper.startsWith('DIMENSION')) {
        const m = line.match(/(\d+)/);
        if (m) out.dimension = parseInt(m[1], 10);
      } else if (upper.startsWith('EDGE_WEIGHT_TYPE')) {
        out.edgeWeightType = line.split(/[:\s]+/).slice(1).join(' ').trim() || null;
      } else if (upper === 'NODE_COORD_SECTION' || upper === 'DISPLAY_DATA_SECTION') {
        inCoords = true;
      }
      continue;
    }

    // inside coord section: "id x y" — treat last two numeric tokens as (x,y)
    const parts = line.split(/\s+/).filter(Boolean);
    if (parts.length >= 3) {
      const x = parseFloat(parts[parts.length - 2]);
      const y = parseFloat(parts[parts.length - 1]);
      if (Number.isFinite(x) && Number.isFinite(y)) out.coords.push([x, y]);
    } else if (parts.length === 2) {
      const x = parseFloat(parts[0]);
      const y = parseFloat(parts[1]);
      if (Number.isFinite(x) && Number.isFinite(y)) out.coords.push([x, y]);
    }
  }
  return out;
}

/**
 * Detect format from filename + content; dispatch to the right parser.
 * Returns { coords, name?, optimum?, edgeWeightType?, dimension? }.
 */
export function parseFile(filename, text) {
  const isTSPLIB = /\.(tsp|tsplib)$/i.test(filename || '') ||
                   /NODE_COORD_SECTION/i.test(text);
  if (isTSPLIB) {
    const r = parseTSPLIB(text);
    return { coords: r.coords, name: r.name, edgeWeightType: r.edgeWeightType,
             dimension: r.dimension };
  }
  return { coords: parseCoords(text), name: filename ? filename.replace(/\.[^.]+$/, '') : null };
}

/**
 * Format a tour as CSV text suitable for "Save tour".
 */
export function tourToCSV(coords, tour) {
  const lines = ['index,city,x,y'];
  for (let i = 0; i < tour.length; i++) {
    const c = tour[i] - 1;
    lines.push(`${i + 1},${tour[i]},${coords[c][0]},${coords[c][1]}`);
  }
  return lines.join('\n') + '\n';
}
