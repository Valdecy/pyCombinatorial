// ============================================================================
// algorithms/index.js — registry for all ported algorithms
// ============================================================================

// Phase 1
import * as nn         from './nn.js';
import * as opt_2      from './opt_2.js';
import * as sa         from './sa.js';
import * as bb         from './bb.js';
import * as som        from './som.js';

// Phase 2a — Constructive
import * as ins_c      from './ins_c.js';
import * as ins_n      from './ins_n.js';
import * as ins_f      from './ins_f.js';
import * as ins_r      from './ins_r.js';
import * as frnn       from './frnn.js';
import * as conv_hull  from './conv_hull.js';
import * as conc_hull  from './conc_hull.js';
import * as swp        from './swp.js';
import * as mf         from './mf.js';
import * as cw         from './cw.js';
import * as spfc_h     from './spfc_h.js';
import * as spfc_m     from './spfc_m.js';
import * as spfc_s     from './spfc_s.js';
import * as tat        from './tat.js';
import * as tbb        from './tbb.js';
import * as christofides from './christofides.js';
import * as bt         from './bt.js';
import * as zs         from './zs.js';
import * as rt         from './rt.js';
import * as ssi        from './ssi.js';
import * as rss        from './rss.js';

// Phase 2b — k-opt family + search heuristics
import * as opt_2s     from './opt_2s.js';
import * as opt_2_5    from './opt_2_5.js';
import * as opt_2_5s   from './opt_2_5s.js';
import * as opt_3      from './opt_3.js';
import * as opt_3s     from './opt_3s.js';
import * as opt_4      from './opt_4.js';
import * as opt_4s     from './opt_4s.js';
import * as opt_5      from './opt_5.js';
import * as opt_5s     from './opt_5s.js';
import * as opt_or     from './opt_or.js';
import * as s_shc      from './s_shc.js';
import * as s_itr      from './s_itr.js';
import * as s_vns      from './s_vns.js';
import * as s_gui      from './s_gui.js';
import * as s_tabu     from './s_tabu.js';
import * as s_sct      from './s_sct.js';
import * as rr         from './rr.js';
import * as lns        from './lns.js';
import * as alns       from './alns.js';

// Phase 2c — population, exact, neural/RL
import * as bf            from './bf.js';
import * as bhk           from './bhk.js';
import * as ksp           from './ksp.js';
import * as gksp          from './gksp.js';
import * as aco           from './aco.js';
import * as ga            from './ga.js';
import * as brkga         from './brkga.js';
import * as ga_eax        from './ga_eax.js';
import * as grasp         from './grasp.js';
import * as eo            from './eo.js';
import * as rl_ql         from './rl_ql.js';
import * as rl_sarsa      from './rl_sarsa.js';
import * as rl_double_ql  from './rl_double_ql.js';
import * as hpn           from './hpn.js';
import * as eln           from './eln.js';

export const ALGORITHMS = {
  // Phase 1
  nn:           { ...nn.meta,           run: nn.run },
  opt_2:        { ...opt_2.meta,        run: opt_2.run },
  sa:           { ...sa.meta,           run: sa.run },
  bb:           { ...bb.meta,           run: bb.run },
  som:          { ...som.meta,          run: som.run },
  // Phase 2a
  ins_c:        { ...ins_c.meta,        run: ins_c.run },
  ins_n:        { ...ins_n.meta,        run: ins_n.run },
  ins_f:        { ...ins_f.meta,        run: ins_f.run },
  ins_r:        { ...ins_r.meta,        run: ins_r.run },
  frnn:         { ...frnn.meta,         run: frnn.run },
  conv_hull:    { ...conv_hull.meta,    run: conv_hull.run },
  conc_hull:    { ...conc_hull.meta,    run: conc_hull.run },
  swp:          { ...swp.meta,          run: swp.run },
  mf:           { ...mf.meta,           run: mf.run },
  cw:           { ...cw.meta,           run: cw.run },
  spfc_h:       { ...spfc_h.meta,       run: spfc_h.run },
  spfc_m:       { ...spfc_m.meta,       run: spfc_m.run },
  spfc_s:       { ...spfc_s.meta,       run: spfc_s.run },
  tat:          { ...tat.meta,          run: tat.run },
  tbb:          { ...tbb.meta,          run: tbb.run },
  christofides: { ...christofides.meta, run: christofides.run },
  bt:           { ...bt.meta,           run: bt.run },
  zs:           { ...zs.meta,           run: zs.run },
  rt:           { ...rt.meta,           run: rt.run },
  ssi:          { ...ssi.meta,          run: ssi.run },
  rss:          { ...rss.meta,          run: rss.run },
  // Phase 2b — k-opt family
  opt_2s:       { ...opt_2s.meta,       run: opt_2s.run },
  opt_2_5:      { ...opt_2_5.meta,      run: opt_2_5.run },
  opt_2_5s:     { ...opt_2_5s.meta,     run: opt_2_5s.run },
  opt_3:        { ...opt_3.meta,        run: opt_3.run },
  opt_3s:       { ...opt_3s.meta,       run: opt_3s.run },
  opt_4:        { ...opt_4.meta,        run: opt_4.run },
  opt_4s:       { ...opt_4s.meta,       run: opt_4s.run },
  opt_5:        { ...opt_5.meta,        run: opt_5.run },
  opt_5s:       { ...opt_5s.meta,       run: opt_5s.run },
  opt_or:       { ...opt_or.meta,       run: opt_or.run },
  // Phase 2b — search heuristics
  s_shc:        { ...s_shc.meta,        run: s_shc.run },
  s_itr:        { ...s_itr.meta,        run: s_itr.run },
  s_vns:        { ...s_vns.meta,        run: s_vns.run },
  s_gui:        { ...s_gui.meta,        run: s_gui.run },
  s_tabu:       { ...s_tabu.meta,       run: s_tabu.run },
  s_sct:        { ...s_sct.meta,        run: s_sct.run },
  rr:           { ...rr.meta,           run: rr.run },
  lns:          { ...lns.meta,          run: lns.run },
  alns:         { ...alns.meta,         run: alns.run },
  // Phase 2c — exact, population, RL/neural
  bf:           { ...bf.meta,           run: bf.run },
  bhk:          { ...bhk.meta,          run: bhk.run },
  ksp:          { ...ksp.meta,          run: ksp.run },
  gksp:         { ...gksp.meta,         run: gksp.run },
  aco:          { ...aco.meta,          run: aco.run },
  ga:           { ...ga.meta,           run: ga.run },
  brkga:        { ...brkga.meta,        run: brkga.run },
  ga_eax:       { ...ga_eax.meta,       run: ga_eax.run },
  grasp:        { ...grasp.meta,        run: grasp.run },
  eo:           { ...eo.meta,           run: eo.run },
  rl_ql:        { ...rl_ql.meta,        run: rl_ql.run },
  rl_sarsa:     { ...rl_sarsa.meta,     run: rl_sarsa.run },
  rl_double_ql: { ...rl_double_ql.meta, run: rl_double_ql.run },
  hpn:          { ...hpn.meta,          run: hpn.run },
  eln:          { ...eln.meta,          run: eln.run },
};

/** Group algorithms by category for the UI dropdown. */
export function groupedAlgorithms() {
  const groups = {};
  for (const id in ALGORITHMS) {
    const a = ALGORITHMS[id];
    const cat = a.category || 'Other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push({ id, ...a });
  }
  for (const cat in groups) groups[cat].sort((a, b) => a.label.localeCompare(b.label));
  return groups;
}
