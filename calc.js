// Development length calculator - JS port of development_length.py (psi, in.)
const BAR_DIA = {3:.375,4:.5,5:.625,6:.75,7:.875,8:1,9:1.128,10:1.27,11:1.41,14:1.693,18:2.257};
const BAR_AREA = {3:.11,4:.2,5:.31,6:.44,7:.6,8:.79,9:1,10:1.27,11:1.56,14:2.25,18:4};

// Parse table_A10.csv text -> {key: ld/db}
function parseA10(text) {
  const d = {};
  text.trim().split(/\r?\n/).slice(1).forEach(l => {
    const [pos, cs, fy, grp, fc, v] = l.split(',');
    d[[pos, cs, grp, +fy, +fc].join('|')] = +v;
  });
  return d;
}

function calc(p, A10) {
  const W = [], out = [];
  const db = BAR_DIA[p.bar_no], Ab = BAR_AREA[p.bar_no];
  const top = p.concrete_below_bar > 12, epoxy = p.coating === 'epoxy' || p.coating === 'dual';
  const lam = p.lam, sq = Math.sqrt(p.fc), large = p.bar_no >= 7 || p.aci408;
  const f1 = x => x.toFixed(1), has = v => v !== null && v !== undefined && !isNaN(v);
  const m = p.mode;

  let r = 1;
  if (!p.no_reduction && has(p.As_req) && has(p.As_prov) && p.As_req > 0 && p.As_prov > 0) {
    const q = p.As_req / p.As_prov;
    if (q > 1) W.push('As,required > As,provided: reduction factor limited to 1.0');
    else r = q;
  }
  const pt = top ? 1.3 : 1;
  const pe = !epoxy ? 1 : (p.clear_cover < 3 * db || p.clear_spacing < 6 * db ? 1.5 : 1.2);
  const sc = (p.clear_spacing >= db && p.clear_cover >= db && p.stirrups_ok) ? 'a'
           : (p.clear_spacing >= 2 * db && p.clear_cover >= db) ? 'b' : 'other';

  const head = [`Bar No. ${p.bar_no} (db = ${db.toFixed(3)} in., Ab = ${Ab} in²)  fy = ${p.fy} psi  f'c = ${p.fc} psi`,
    `λ = ${lam}  coating = ${p.coating}  ${top ? 'Top' : 'Bottom'} bar (ψt = ${pt})`,
    `As,req/As,prov reduction factor = ${r.toFixed(3)}${p.no_reduction ? ' (not applicable)' : ''}`];

  const avail = (req, label) => {
    if (!has(p.available)) return [];
    const d = p.available - req;
    return [d >= 0 ? `Check ${label}: available ${f1(p.available)} ≥ required ${f1(req)} in. → OK (margin ${f1(d)} in.)`
                   : `Check ${label}: available ${f1(p.available)} < required ${f1(req)} in. → NOT OK (short by ${f1(-d)} in.)`];
  };

  // base straight-bar ld (Table 6.1), no reduction / minimum applied
  const t61 = () => {
    const pte = Math.min(pt * pe, 1.7);
    const k = sc === 'other' ? (large ? 40 : 50) : (large ? 20 : 25);
    const ldDb = (sc === 'other' ? 3 : 1) * p.fy * pte / (k * lam * sq);
    return { pte, ldDb, ld: ldDb * db };
  };

  if (m === 'straight' || m === 'all') {
    const a = t61(), fin = Math.max(a.ld * r, 12);
    out.push({ title: '[1] Straight bar - Table 6.1 / Eq. (6.5a, 6.5b)', lines: [
      `Spacing case: ${sc} | group: ${large ? 'No.7 & larger' : 'No.6 & smaller'}`,
      `ψt = ${pt}, ψe = ${pe}, ψtψe = ${a.pte} (max 1.7)`,
      `ld/db = ${f1(a.ldDb)} → ld = ${f1(a.ld)} in.`,
      `Final (reduction + min 12 in.): ${f1(fin)} in. = ${(fin / 12).toFixed(2)} ft`, ...avail(fin, 'Table 6.1')], final: fin });

    const L = [];
    if (epoxy || lam !== 1) L.push('Table A.10 is only for uncoated bars and normalweight concrete');
    else if (!A10) L.push('table_A10.csv not loaded');
    else try {
      const pos = top ? 'top' : 'bottom', cs = sc === 'other' ? 'other' : 'case_ab', g = large ? 'No7_larger' : 'No6_smaller';
      const keys = Object.keys(A10).map(k => k.split('|'));
      const uniq = i => [...new Set(keys.map(k => +k[i]))].sort((x, y) => x - y);
      const br = (vals, x, n) => {
        if (x < vals[0] || x > vals[vals.length - 1]) throw new Error(`${n} = ${x} is outside Table A.10 range (${vals[0]}-${vals[vals.length - 1]})`);
        return [Math.max(...vals.filter(v => v <= x)), Math.min(...vals.filter(v => v >= x))];
      };
      const fk = p.fy / 1000, [y0, y1] = br(uniq(3), fk, 'fy (ksi)'), [c0, c1] = br(uniq(4), p.fc, "f'c (psi)");
      const v = (y, c) => A10[[pos, cs, g, y, c].join('|')];
      const lin = (x, x0, x1, a0, a1) => x1 === x0 ? a0 : a0 + (a1 - a0) * (x - x0) / (x1 - x0);
      const ldDb = lin(fk, y0, y1, lin(p.fc, c0, c1, v(y0, c0), v(y0, c1)), lin(p.fc, c0, c1, v(y1, c0), v(y1, c1)));
      const fin = Math.max(ldDb * db * r, 12);
      L.push(`${pos} bar | ${cs} | ${g} | ${(y0 === y1 && c0 === c1) ? 'exact' : 'interpolated'}`,
        `ld/db = ${f1(ldDb)} → ld = ${f1(ldDb * db)} in.`,
        `Final (reduction + min 12 in.): ${f1(fin)} in. = ${(fin / 12).toFixed(2)} ft`, ...avail(fin, 'Table A.10'));
    } catch (e) { L.push(e.message); }
    out.push({ title: '[2] Straight bar - Table A.10', lines: L });
  }

  if (m === 'hook' || m === 'all') {
    const pe_h = epoxy ? 1.2 : 1;
    const pc = (p.bar_no <= 11 && p.side_cover >= 2.5 && (p.hook_type !== 90 || p.ext_cover >= 2)) ? 0.7 : 1;
    let pr = 1;
    if (p.disc_end) {
      if (!p.hook_conf) W.push('Discontinuous end (cover < 2.5 in.): closed ties/stirrups (s ≤ 3db) required along ldh - not provided!');
    } else if (p.bar_no <= 11) {
      if (p.hook_type === 90 && (p.hook_conf || p.hook_ext_conf)) pr = 0.8;
      else if (p.hook_type === 180 && p.hook_conf) pr = 0.8;
    }
    // hook dimensions (Table 6.2)
    let D = p.bar_no <= 8 ? 6 * db : p.bar_no <= 11 ? 8 * db : 10 * db, ext;
    if (p.stirrup_hook && p.bar_no <= 5) D = 4 * db;
    if (!p.stirrup_hook) ext = p.hook_type === 90 ? 12 * db : Math.max(4 * db, 2.5);
    else {
      ext = p.hook_type === 90 ? (p.bar_no <= 5 ? Math.max(6 * db, 3) : 12 * db)
          : p.hook_type === 135 ? Math.max(6 * db, 3) : Math.max(4 * db, 2.5);
      if (p.bar_no > 8) W.push('Stirrup/tie hooks are only for No. 8 and smaller bars');
    }
    const L = [`${p.hook_type}° ${p.stirrup_hook ? 'stirrup/tie' : 'main bar'} | min inside bend dia D = ${D.toFixed(2)} in. | extension ≥ ${ext.toFixed(2)} in.`];
    if (!p.stirrup_hook) {
      const raw = p.fy * pe_h * pc * pr / (50 * lam * sq) * db, fin = Math.max(raw * r, 8 * db, 6);
      L.push(`ψe = ${pe_h}, ψc = ${pc}, ψr = ${pr}, λ = ${lam}`,
        `ldh = ${f1(raw)} in. → Final (reduction + min 8db, 6 in.): ${f1(fin)} in.`, ...avail(fin, 'hook'));
    }
    out.push({ title: '[3] Standard hook - Eq. (6.6)', lines: L });
  }

  if (m === 'headed' || m === 'all') {
    const fcu = Math.min(p.fc, 6000), raw = 0.016 * p.fy * (epoxy ? 1.2 : 1) / Math.sqrt(fcu) * db;
    const fin = Math.max(raw, 8 * db, 6);
    if (p.bar_no > 11) W.push('Headed bar: only No. 11 and smaller bars');
    if (p.fy > 60000) W.push('Headed bar: fy must be ≤ 60,000 psi');
    if (lam !== 1) W.push('Headed bar: normalweight concrete only');
    if (p.clear_cover < 2 * db) W.push(`Headed bar: clear cover ≥ 2db (${(2 * db).toFixed(2)} in.) required`);
    if (p.clear_spacing < 4 * db) W.push(`Headed bar: clear spacing ≥ 4db (${(4 * db).toFixed(2)} in.) required`);
    if (!has(p.Abrg)) W.push('Headed bar: Abrg ≥ 4Ab not checked (bearing area not given)');
    else if (p.Abrg < 4 * Ab) W.push(`Headed bar: Abrg = ${p.Abrg} in² < 4Ab = ${(4 * Ab).toFixed(2)} in²`);
    if (has(p.obstruction) && p.obstruction > 2 * db) W.push('Headed bar: obstruction > 2db from bearing face - HA head requirement not met');
    if (p.fc > 6000) W.push("Headed bar: f'c = 6000 psi used (Code limit)");
    out.push({ title: '[4] Headed bar - Eq. (6.7) / Table 6.3', lines: [
      `ψe = ${epoxy ? 1.2 : 1}, f'c used = ${fcu} psi`,
      `ldt = ${f1(raw)} in. → Final (min 8db, 6 in.; no As reduction): ${f1(fin)} in.`,
      'ldt is measured from the bearing face of the head to the critical section', ...avail(fin, 'headed bar')] });
  }

  if (m === 'compression' || m === 'all') {
    const raw = Math.max(0.02 * p.fy * db / (lam * sq), 0.0003 * p.fy * db), fin = Math.max(raw * r, 8);
    out.push({ title: '[5] Compression development length', lines: [
      `ldc = max(0.02·fy·db/(λ√f'c), 0.0003·fy·db) = ${f1(raw)} in.`,
      `Final (reduction + min 8 in.): ${f1(fin)} in.`, ...avail(fin, 'compression')] });
  }

  if (m === 'splice' || m === 'all') {
    const a = t61(), ratio = (has(p.As_req) && has(p.As_prov) && p.As_req > 0) ? p.As_prov / p.As_req : null;
    const classA = ratio !== null && ratio >= 2 && p.pct_spliced <= 50;
    const fin = Math.max(a.ld * (classA ? 1 : 1.3), 12);
    out.push({ title: '[6] Tension lap splice (Table 6.1 ld; no As reduction)', lines: [
      `ld = ${f1(a.ld)} in. | As,prov/As,req = ${ratio === null ? 'not given → Class B' : ratio.toFixed(2)} | spliced = ${p.pct_spliced}%`,
      `Class ${classA ? 'A (1.0 ld)' : 'B (1.3 ld)'} → splice length (min 12 in.): ${f1(fin)} in. = ${(fin / 12).toFixed(2)} ft`, ...avail(fin, 'splice')] });
  }

  return { head, out, warnings: [...new Set(W)] };
}

if (typeof module !== 'undefined') module.exports = { calc, parseA10 };
