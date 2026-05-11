// ============================================================================
// main.js — UI orchestration for the pyCombinatorial web visualizer
// ============================================================================

import { Renderer }   from './core/renderer.js';
import { Stepper }    from './core/stepper.js';
import { ALGORITHMS } from './algorithms/index.js';
import { makeRefiner } from './core/twoopt_refiner.js';
import { buildDistanceMatrix } from './core/distance.js';
import {
  parseCoords, parseFile, tourToCSV, generateRandom, PRESETS,
} from './core/dataset.js';

// ---- DOM refs --------------------------------------------------------------
const $ = sel => document.querySelector(sel);

const ui = {
  canvas:          $('#canvas'),
  hint:            $('#canvas-hint'),
  textarea:        $('#dataset-input'),
  presetSelect:    $('#preset-select'),
  presetNotes:     $('#preset-notes'),
  randomCount:     $('#random-count'),
  algoSelect:      $('#algo-select'),
  algoDescription: $('#algo-description'),
  paramsBox:       $('#params-box'),
  log:             $('#log'),
  fileInput:       $('#file-input'),

  btnLoadText:     $('#btn-load-text'),
  btnLoadPreset:   $('#btn-load-preset'),
  btnRandom:       $('#btn-random'),
  btnClear:        $('#btn-clear'),
  btnImport:       $('#btn-import'),
  btnResetParams:  $('#btn-reset-params'),
  btnClearLog:     $('#btn-clear-log'),

  btnReset:        $('#btn-reset'),
  btnStep:         $('#btn-step'),
  btnPlay:         $('#btn-play'),
  btnPause:        $('#btn-pause'),
  btnEnd:          $('#btn-end'),
  speedRange:      $('#speed-range'),
  speedVal:        $('#speed-val'),

  statusPill:      $('#status-pill'),
  statusText:      $('#status-text'),

  ovCount:         $('#ov-count'),
  hmOptWrap:       $('#hm-optimum-wrap'),
  hmOptimum:       $('#hm-optimum'),
  hmResultWrap:    $('#hm-result-wrap'),
  hmResult:        $('#hm-result'),
  hmGap:           $('#hm-gap'),

  refineBox:       $('#refine-box'),
  btnRefine:       $('#btn-refine'),
  btnSaveTour:     $('#btn-save-tour'),

  dropOverlay:     $('#drop-overlay'),
  toast:           $('#toast'),
};

// ---- state -----------------------------------------------------------------
const state = {
  coords: [],
  distanceMatrix: null,
  algoId: null,
  algoMeta: null,
  paramValues: {},
  renderer: null,
  stepper: new Stepper(),
  finalResult: null,
  refining: false,
  optimum: null,           // currently-known optimum (from preset or import)
  datasetName: null,       // display name of current dataset
};

// ---- init ------------------------------------------------------------------
function init() {
  state.renderer = new Renderer(ui.canvas);
  state.renderer.drawEmpty();

  // populate preset select
  for (const [id, p] of Object.entries(PRESETS)) {
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = p.optimum != null
      ? `${p.name} — opt ≈ ${p.optimum}`
      : p.name;
    ui.presetSelect.appendChild(opt);
  }


  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

  const specialOrder = new Map([
    ['opt_2', 1],
    ['opt_2_5', 2],
    ['opt_3', 3],
    ['opt_4', 4],
    ['opt_5', 5],
    ['opt_or', 6],
    ['opt_2s', 7],
    ['opt_2_5s', 8],
    ['opt_3s', 9],
    ['opt_4s', 10],
    ['opt_5s', 11],
  ]);

  const algorithms = Object.entries(ALGORITHMS)
    .map(([id, algo]) => ({ id, ...algo }))
    .sort((a, b) => {
      const aRank = specialOrder.get(a.id);
      const bRank = specialOrder.get(b.id);

      if (aRank != null && bRank != null) return aRank - bRank;
      if (aRank != null) return -1;
      if (bRank != null) return 1;

      return collator.compare(a.label, b.label);
    });

  for (const algo of algorithms) {
    const opt = document.createElement('option');
    opt.value = algo.id;
    opt.textContent = algo.label;
    ui.algoSelect.appendChild(opt);
  }

  ui.algoSelect.value = 'opt_2';
  switchAlgorithm('opt_2');

  bindEvents();
  setupStepper();
  setStatus('idle', 'awaiting dataset');
  setSpeed(parseInt(ui.speedRange.value, 10));
  updatePresetNotes();

  // default-load Berlin52
  loadPreset('berlin52');
}

// ---- events ----------------------------------------------------------------
function bindEvents() {
  ui.btnLoadText.addEventListener('click', () => {
    const c = parseCoords(ui.textarea.value);
    if (c.length < 3) return toast('need at least 3 valid (x, y) pairs', 'bad');
    setCoords(c, { name: 'pasted', optimum: null });
    toast(`loaded ${c.length} cities`, 'good');
  });

  ui.btnLoadPreset.addEventListener('click', () => loadPreset(ui.presetSelect.value));
  ui.presetSelect.addEventListener('change', updatePresetNotes);

  ui.btnRandom.addEventListener('click', () => {
    const n = Math.max(3, Math.min(500, parseInt(ui.randomCount.value, 10) || 30));
    const seed = (Date.now() & 0xffff);
    setCoords(generateRandom(n, 1000, 1000, seed), {
      name: `random ${n} (seed ${seed})`,
      optimum: null,
    });
    toast(`generated ${n} random cities`, 'good');
  });

  ui.btnClear.addEventListener('click', () => {
    setCoords([], { name: null, optimum: null });
    ui.textarea.value = '';
  });

  ui.btnImport.addEventListener('click', () => ui.fileInput.click());
  ui.fileInput.addEventListener('change', e => {
    const f = e.target.files[0];
    if (f) handleFile(f);
    e.target.value = '';
  });

  // drag-drop on whole window
  let dragDepth = 0;
  window.addEventListener('dragenter', e => {
    if (!hasFiles(e)) return;
    e.preventDefault();
    dragDepth++;
    ui.dropOverlay.classList.add('show');
  });
  window.addEventListener('dragover', e => { if (hasFiles(e)) e.preventDefault(); });
  window.addEventListener('dragleave', () => {
    dragDepth--;
    if (dragDepth <= 0) { dragDepth = 0; ui.dropOverlay.classList.remove('show'); }
  });
  window.addEventListener('drop', e => {
    if (!hasFiles(e)) return;
    e.preventDefault();
    dragDepth = 0;
    ui.dropOverlay.classList.remove('show');
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  });

  ui.algoSelect.addEventListener('change', e => switchAlgorithm(e.target.value));

  ui.btnReset.addEventListener('click', resetRun);
  ui.btnStep.addEventListener('click', () => state.stepper.step());
  ui.btnPlay.addEventListener('click', () => {
    if (!state.stepper.gen) startRun();
    else state.stepper.play();
  });
  ui.btnPause.addEventListener('click', () => state.stepper.pause());
  ui.btnEnd.addEventListener('click', async () => {
    if (!state.stepper.gen) startRun();
    state.stepper.pause();
    await state.stepper.runToEnd();
  });

  ui.speedRange.addEventListener('input', e => setSpeed(parseInt(e.target.value, 10)));

  ui.btnRefine.addEventListener('click', startRefine);
  ui.btnSaveTour.addEventListener('click', saveTour);
  ui.btnResetParams.addEventListener('click', () => {
    if (state.algoMeta) buildParamsUI(state.algoMeta);
    toast('parameters reset', 'good');
  });
  ui.btnClearLog.addEventListener('click', () => { ui.log.innerHTML = ''; });

  // canvas click-to-add
  ui.canvas.addEventListener('click', e => {
    const rect = ui.canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    if (state.coords.length === 0) state.renderer.setCoords([[0, 0], [1000, 1000]]);
    const [x, y] = state.renderer.invert(px, py);
    setCoords([...state.coords, [x, y]], { name: state.datasetName, optimum: null });
  });

  // keyboard shortcuts
  window.addEventListener('keydown', e => {
    if (e.target.matches('input, textarea, select')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const code = e.code;
    if (code === 'Space') {
      e.preventDefault();
      state.stepper.step();
    } else if (code === 'KeyP') {
      e.preventDefault();
      if (state.stepper.playing) state.stepper.pause();
      else if (state.stepper.gen) state.stepper.play();
      else startRun();
    } else if (code === 'KeyR') {
      e.preventDefault();
      resetRun();
    } else if (code === 'KeyE') {
      e.preventDefault();
      (async () => {
        if (!state.stepper.gen) startRun();
        state.stepper.pause();
        await state.stepper.runToEnd();
      })();
    }
  });
}

function hasFiles(e) {
  const t = e.dataTransfer?.types;
  return t && (t.includes ? t.includes('Files') : Array.from(t).indexOf('Files') >= 0);
}

async function handleFile(file) {
  const text = await file.text();
  const parsed = parseFile(file.name, text);
  if (!parsed.coords || parsed.coords.length < 3) {
    return toast('could not parse — need at least 3 (x, y) pairs', 'bad');
  }
  setCoords(parsed.coords, {
    name: parsed.name || file.name,
    optimum: null,
  });
  let summary = `${parsed.coords.length} cities`;
  if (parsed.name) summary += ` · ${parsed.name}`;
  if (parsed.edgeWeightType) summary += ` · ${parsed.edgeWeightType}`;
  toast(summary, 'good');
  log(`imported ${file.name} (${parsed.coords.length} cities)`, 'cyan');
}

// ---- algorithm selection ---------------------------------------------------
function switchAlgorithm(id) {
  state.algoId = id;
  const algo = ALGORITHMS[id];
  state.algoMeta = algo;
  ui.algoDescription.textContent = algo.description;
  buildParamsUI(algo);
  resetRun();
}

function buildParamsUI(algo) {
  ui.paramsBox.innerHTML = '';
  state.paramValues = {};

  if (!algo.params || algo.params.length === 0) {
    const note = document.createElement('div');
    note.className = 'hint';
    note.textContent = 'no parameters';
    ui.paramsBox.appendChild(note);
    return;
  }

  for (const p of algo.params) {
    state.paramValues[p.key] = p.default;
    const wrap = document.createElement('div');
    wrap.className = 'field';

    const label = document.createElement('label');
    label.innerHTML = `<span>${p.label}</span><span class="val" id="pval-${p.key}"></span>`;
    wrap.appendChild(label);

    if (p.type === 'bool') {
      buildToggle(wrap, p);
    } else if (p.min != null && p.max != null) {
      buildSlider(wrap, p);
    } else {
      buildNumber(wrap, p);
    }

    if (p.hint) {
      const hint = document.createElement('div');
      hint.className = 'hint';
      hint.style.marginTop = '4px';
      hint.textContent = p.hint;
      wrap.appendChild(hint);
    }

    ui.paramsBox.appendChild(wrap);
  }
}

function setParam(p, v) {
  state.paramValues[p.key] = v;
  const tgt = $(`#pval-${p.key}`);
  if (tgt) tgt.textContent = formatVal(v);
}

function formatVal(v) {
  if (typeof v === 'boolean') return v ? 'on' : 'off';
  if (typeof v !== 'number') return String(v);
  if (Number.isInteger(v)) return String(v);
  if (Math.abs(v) >= 1) return v.toFixed(2);
  return v.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
}

function buildToggle(wrap, p) {
  const tog = document.createElement('div');
  tog.className = 'toggle';
  const off = document.createElement('button');
  off.type = 'button'; off.textContent = 'off';
  const on  = document.createElement('button');
  on.type = 'button';  on.textContent = 'on';
  const apply = v => {
    on.classList.toggle('on', v);
    off.classList.toggle('on', !v);
    setParam(p, v);
  };
  off.addEventListener('click', () => apply(false));
  on.addEventListener('click',  () => apply(true));
  tog.append(off, on);
  wrap.appendChild(tog);
  apply(!!p.default);
}

function buildSlider(wrap, p) {
  const row = document.createElement('div');
  row.className = 'param-row';
  const num = document.createElement('input');
  num.type = 'number';
  num.className = 'input input-num';
  num.value = p.default;
  if (p.min  != null) num.min  = p.min;
  if (p.max  != null) num.max  = p.max;
  num.step = p.step != null ? p.step : (p.type === 'int' ? 1 : 'any');

  const range = document.createElement('input');
  range.type = 'range';
  // for very wide ranges, use log-friendly heuristics? Keep linear for now.
  range.min = p.min;
  range.max = p.max;
  range.step = p.step != null ? p.step : (p.type === 'int' ? 1 : (p.max - p.min) / 1000);
  range.value = p.default;

  const apply = (raw, src) => {
    let v = (p.type === 'int') ? parseInt(raw, 10) : parseFloat(raw);
    if (!Number.isFinite(v)) return;
    if (p.min != null && v < p.min) v = p.min;
    if (p.max != null && v > p.max) v = p.max;
    if (src !== num) num.value = v;
    if (src !== range) range.value = v;
    setParam(p, v);
  };
  num.addEventListener('input',   () => apply(num.value,   num));
  num.addEventListener('change',  () => apply(num.value,   num));
  range.addEventListener('input', () => apply(range.value, range));

  row.append(num, range);
  wrap.appendChild(row);
  apply(p.default, null);
}

function buildNumber(wrap, p) {
  const num = document.createElement('input');
  num.type = 'number';
  num.className = 'input';
  num.value = p.default;
  if (p.min  != null) num.min  = p.min;
  if (p.max  != null) num.max  = p.max;
  num.step = p.step != null ? p.step : (p.type === 'int' ? 1 : 'any');
  const apply = () => {
    let v = (p.type === 'int') ? parseInt(num.value, 10) : parseFloat(num.value);
    if (!Number.isFinite(v)) return;
    setParam(p, v);
  };
  num.addEventListener('input', apply);
  num.addEventListener('change', apply);
  wrap.appendChild(num);
  apply();
}

// ---- coords ---------------------------------------------------------------
function setCoords(coords, info = {}) {
  state.coords = coords;
  state.distanceMatrix = coords.length >= 2 ? buildDistanceMatrix(coords) : null;
  state.optimum = info.optimum ?? null;
  state.datasetName = info.name ?? null;
  state.renderer.setCoords(coords);
  state.renderer.drawEmpty();
  ui.hint.classList.toggle('hidden', coords.length > 0);
  ui.ovCount.textContent = String(coords.length);
  updateHeaderOptimum();
  resetRun();
  if (coords.length > 0) state.renderer.render({ tour: null });
}

function loadPreset(id) {
  const p = PRESETS[id];
  if (!p) return;
  setCoords([...p.coords], { name: p.name, optimum: p.optimum });
  toast(`preset: ${p.name}`, 'good');
}

function updatePresetNotes() {
  const id = ui.presetSelect.value;
  const p = PRESETS[id];
  ui.presetNotes.textContent = p?.notes || '';
}

function updateHeaderOptimum() {
  if (state.optimum != null) {
    ui.hmOptimum.textContent = state.optimum.toFixed(2);
    ui.hmOptWrap.classList.remove('hidden');
  } else {
    ui.hmOptWrap.classList.add('hidden');
  }
  ui.hmResultWrap.classList.add('hidden');
}

// ---- run lifecycle --------------------------------------------------------
function setupStepper() {
  state.stepper.onState = s => onAlgoState(s);
  state.stepper.onDone = result => onAlgoDone(result);
  state.stepper.onStatus = (s, extra) => {
    if (s === 'running')      setStatus('running', state.refining ? 'refining (2-opt)' : 'running');
    else if (s === 'paused')  setStatus('idle', 'paused');
    else if (s === 'done')    setStatus('done', state.refining ? 'refine done' : 'algorithm done');
    else if (s === 'error')   setStatus('error', extra || 'error');
  };
}

function startRun() {
  if (!state.distanceMatrix) {
    toast('load a dataset first', 'bad');
    return;
  }
  const algo = ALGORITHMS[state.algoId];
  if (algo.warnIf && state.coords.length > algo.warnIf.citiesAbove) {
    if (!confirm(`${algo.label}: ${algo.warnIf.message}\nProceed anyway?`)) return;
  }
  state.refining = false;
  state.finalResult = null;
  ui.refineBox.classList.add('hidden');
  ui.hmResultWrap.classList.add('hidden');
  log(`▶ ${algo.label}`, 'amber');
  const gen = algo.run(state.distanceMatrix, { ...state.paramValues }, { coords: state.coords });
  state.stepper.load(gen, {
    onState: onAlgoState,
    onDone: onAlgoDone,
    onStatus: state.stepper.onStatus,
  });
  state.stepper.play();
}

function startRefine() {
  if (!state.finalResult || !state.finalResult.tour) {
    toast('no completed tour to refine', 'bad');
    return;
  }
  state.refining = true;
  ui.refineBox.classList.add('hidden');
  log('▶ 2-opt refinement', 'cyan');
  const gen = makeRefiner(state.distanceMatrix, state.finalResult.tour);
  state.stepper.load(gen, {
    onState: onAlgoState,
    onDone: onAlgoDone,
    onStatus: state.stepper.onStatus,
  });
  state.stepper.play();
}

function resetRun() {
  state.stepper.cancel();
  state.refining = false;
  state.finalResult = null;
  ui.refineBox.classList.add('hidden');
  ui.hmResultWrap.classList.add('hidden');
  if (state.coords.length > 0) state.renderer.render({ tour: null });
  else state.renderer.drawEmpty();
  setStatus('idle', 'idle');
}

// ---- render hooks ---------------------------------------------------------
function onAlgoState(s) {
  state.renderer.render(s);
  if (s.message && Number.isFinite(s.bestDistance)) {
    setStatus('running', `best ${s.bestDistance.toFixed(2)}`);
  } else if (s.message) {
    setStatus('running', s.message.slice(0, 60));
  }
  if (s.message) {
    if (s.phase === 'improvement' || s.phase === 'leaf-improve') log(s.message, 'good');
    else if (s.phase === 'prune') log(s.message, 'amber');
  }
}

function onAlgoDone(result) {
  if (!result) return;
  state.finalResult = result;
  log(result.summary || 'done', 'good');
  setStatus('done', state.refining ? 'refine done' : 'algorithm done');
  showResultInHeader(result.distance);
  if (!state.refining && result.tour) {
    ui.refineBox.classList.remove('hidden');
  } else if (state.refining) {
    state.refining = false;
  }
}

function showResultInHeader(distance) {
  if (!Number.isFinite(distance)) return;
  ui.hmResult.textContent = distance.toFixed(2);
  ui.hmResultWrap.classList.remove('hidden');
  if (state.optimum != null && state.optimum > 0) {
    const gap = (distance - state.optimum) / state.optimum;
    if (gap <= 0.001) {
      ui.hmGap.textContent = 'optimal';
      ui.hmGap.className = 'hm-gap good';
    } else {
      const pct = (gap * 100).toFixed(1);
      ui.hmGap.textContent = `+${pct}%`;
      ui.hmGap.className = 'hm-gap ' + (gap < 0.05 ? 'good' : '');
    }
  } else {
    ui.hmGap.textContent = '';
    ui.hmGap.className = 'hm-gap';
  }
}

// ---- save tour ------------------------------------------------------------
function saveTour() {
  if (!state.finalResult || !state.finalResult.tour) {
    return toast('no tour to save', 'bad');
  }
  const csv = tourToCSV(state.coords, state.finalResult.tour);
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  const url = URL.createObjectURL(blob);
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const baseName = state.datasetName ? state.datasetName.replace(/[^A-Za-z0-9]+/g, '_') : 'tour';
  a.href = url;
  a.download = `${baseName}_${state.algoId}_${ts}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toast('tour saved', 'good');
}

// ---- utilities ------------------------------------------------------------
function setStatus(kind, text) {
  ui.statusPill.classList.remove('idle', 'running', 'done', 'error');
  ui.statusPill.classList.add(kind);
  ui.statusText.textContent = text;
}

function setSpeed(ms) {
  ui.speedVal.textContent = ms === 0 ? 'max' : `${ms}ms`;
  state.stepper.setSpeed(ms);
}

let toastT = null;
function toast(msg, kind = '') {
  if (toastT) clearTimeout(toastT);
  ui.toast.textContent = msg;
  ui.toast.className = `toast ${kind} show`;
  toastT = setTimeout(() => ui.toast.classList.remove('show'), 1800);
}

function log(msg, kind = 'info') {
  const ts = new Date().toTimeString().slice(0, 8);
  const d = document.createElement('div');
  d.className = `log-line ${kind}`;
  d.innerHTML = `<span class="ts">${ts}</span>${msg}`;
  ui.log.appendChild(d);
  ui.log.scrollTop = ui.log.scrollHeight;
  while (ui.log.children.length > 200) ui.log.removeChild(ui.log.firstChild);
}

// ---- go --------------------------------------------------------------------
window.addEventListener('DOMContentLoaded', init);
