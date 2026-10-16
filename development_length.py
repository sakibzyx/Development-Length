"""
Development Length Calculator  (ACI 318 / Nilson-Darwin-Dolan, Chapter 6)
Units: psi, inch

  [1] Straight bar - Simplified Eqs. (6.5a, 6.5b) / Table 6.1
  [2] Straight bar - Table A.10  (lookup from table_A10.csv)
  [3] Standard hook - Eq. (6.6)  + hook dimensions (Fig. 6.9, Table 6.2)
  [4] Headed bar    - Eq. (6.7)  / Table 6.3
"""
import csv
import math
import os

# Input parameters

mode = "all"               # "straight" | "hook" | "headed" | "all"
available_length = None    # in. - length actually available for the selected mode
                           # (straight: from critical section; hook: embedment past the
                           #  critical section; headed: bearing face to critical section)
                           # None -> no OK / NOT OK check

# Common
fy = 60000           # psi  - steel yield strength
fc = 4000            # psi  - concrete f'c
bar_no = 8           # US bar no. (3,4,5,6,7,8,9,10,11,14,18)

concrete_below_bar = 8.0   # in. - depth of fresh concrete placed below the bar
                           # (> 12 in. -> top bar, ψt = 1.3)
coating = "uncoated"       # "uncoated" | "galvanized" | "epoxy" | "dual"
                           # (dual = zinc and epoxy dual-coated)

lam = 1.0                  # λ : normalweight = 1.0, lightweight = 0.75
                           # (if fct is specified, calculate it yourself and enter it:
                           #  λ = fct/(6.7*sqrt(fcm)) <= 1.0)

# ---- Reinforcement in excess (As,required / As,provided) ----
As_required = None         # in²  (None -> no reduction)
As_provided = None         # in²
no_reduction_case = False  # True: anchorage/development for fy specifically
                           # required, or Seismic Design Category D, E, F
                           # -> reduction not applicable

# ---- Straight bar : spacing / cover ----
clear_spacing = 2.5        # in. - clear spacing of bars being developed/spliced
clear_cover = 2.0          # in. - clear cover
stirrups_ok = True         # stirrups/ties throughout ld >= Code minimum?
USE_ACI408 = False         # True -> ACI 408: use No.7+ formulas/values for all bar sizes

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "table_A10.csv")

# ---- Hooked bar (Eq. 6.6) ----
hook_type = 90             # 90 | 180   (135 only for stirrups/ties)
is_stirrup_hook = False    # True -> only hook dimensions are shown (stirrup/tie)
side_cover = 3.0           # in. - side cover (normal to plane of hook)
ext_cover = 2.0            # in. - cover on bar extension of a 90° hook
hook_confined_along_ldh = False  # ties/stirrups along ldh (perpendicular to ldh), s <= 3db?
hook_ext_confined = False        # (90° only) bar extension beyond hook, including the
                                 # bend, enclosed by ties (perpendicular to tail), s <= 3db?
discontinuous_end_small_cover = False  # discontinuous end with both side cover and
                                       # top/bottom cover < 2.5 in.?

# ---- Headed bar (Eq. 6.7) ----
head_net_bearing_area = None  # in² - net bearing area Abrg of head (None = not checked)
obstruction_dist = None       # in. - obstruction of deformations, from bearing face
                              # (None = no obstruction)

# Calculation
BAR_DIA = {3: 0.375, 4: 0.500, 5: 0.625, 6: 0.750, 7: 0.875, 8: 1.000,
           9: 1.128, 10: 1.270, 11: 1.410, 14: 1.693, 18: 2.257}
BAR_AREA = {3: 0.11, 4: 0.20, 5: 0.31, 6: 0.44, 7: 0.60, 8: 0.79,
            9: 1.00, 10: 1.27, 11: 1.56, 14: 2.25, 18: 4.00}

db = BAR_DIA[bar_no]
Ab = BAR_AREA[bar_no]
top_bar = concrete_below_bar > 12.0
is_epoxy = coating in ("epoxy", "dual")
warnings = []


sqrt_fc = math.sqrt(fc)


def reduction():
    if no_reduction_case:
        return 1.0
    if As_required and As_provided:
        ratio = As_required / As_provided
        if ratio > 1.0:
            warnings.append("As,required > As,provided: reduction factor limited "
                            "to 1.0 (ld can never be increased by this factor)")
            return 1.0
        return ratio
    return 1.0


def psi_t():
    return 1.3 if top_bar else 1.0


def psi_e_straight():
    if not is_epoxy:
        return 1.0
    if clear_cover < 3 * db or clear_spacing < 6 * db:
        return 1.5
    return 1.2


def spacing_case():
    case_a = clear_spacing >= db and clear_cover >= db and stirrups_ok
    case_b = clear_spacing >= 2 * db and clear_cover >= db
    return ("a" if case_a else "b" if case_b else "other")


def large_group():
    return bar_no >= 7 or USE_ACI408


# Straight bar - Table 6.1 - Eqs. 6.5a, 6.5b
def straight_table61():
    case = spacing_case()
    pt, pe = psi_t(), psi_e_straight()
    pte = min(pt * pe, 1.7)
    if case in ("a", "b"):
        k = 20 if large_group() else 25
        ld_db = fy * pte / (k * lam * sqrt_fc)
    else:
        k = 40 if large_group() else 50
        ld_db = 3 * fy * pte / (k * lam * sqrt_fc)
    return dict(case=case, psi_t=pt, psi_e=pe, psi_te=pte, k=k,
                ld_db=ld_db, ld=ld_db * db)


# Table A.10 (CSV)
def load_table_a10(path=CSV_FILE):
    data = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["position"], row["case"], row["bar_group"],
                   float(row["fy_ksi"]), float(row["fc_psi"]))
            data[key] = float(row["ld_over_db"])
    return data


def _bracket(values, x, name):
    values = sorted(values)
    if x < values[0] or x > values[-1]:
        raise ValueError(f"{name} = {x} is outside the range of Table A.10 "
                         f"({values[0]}-{values[-1]})")
    return (max(v for v in values if v <= x),
            min(v for v in values if v >= x))


def _lin(x, x0, x1, y0, y1):
    return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def table_a10():
    case = spacing_case()
    position = "top" if top_bar else "bottom"
    csv_case = "case_ab" if case in ("a", "b") else "other"
    group = "No7_larger" if large_group() else "No6_smaller"

    data = load_table_a10()
    fy_ksi = fy / 1000.0
    fy0, fy1 = _bracket({k[3] for k in data}, fy_ksi, "fy (ksi)")
    fc0, fc1 = _bracket({k[4] for k in data}, fc, "f'c (psi)")

    def v(a, b):
        return data[(position, csv_case, group, a, b)]

    low = _lin(fc, fc0, fc1, v(fy0, fc0), v(fy0, fc1))
    high = _lin(fc, fc0, fc1, v(fy1, fc0), v(fy1, fc1))
    ld_db = _lin(fy_ksi, fy0, fy1, low, high)
    return dict(position=position, case=csv_case, group=group, ld_db=ld_db,
                ld=ld_db * db, exact=(fy0 == fy1 and fc0 == fc1))


# Standard hook - Eq. 6.6 - dimensions
def hook_factors():
    pe = 1.2 if is_epoxy else 1.0

    # ψc : No.11 and smaller, side cover >= 2.5 in., and for 90° hooks
    #      cover on bar extension beyond hook >= 2 in.
    cover_ok = (bar_no <= 11 and side_cover >= 2.5 and
                (hook_type != 90 or ext_cover >= 2.0))
    pc = 0.7 if cover_ok else 1.0

    # ψr : confining reinforcement factor
    pr = 1.0
    if discontinuous_end_small_cover:
        # ACI 25.4.3.3: closed ties/stirrups (s <= 3db) are mandatory along
        # the full ldh, and ψr = 0.8 does not apply
        if not hook_confined_along_ldh:
            warnings.append("Discontinuous end (side and top/bottom cover < 2.5 in.): "
                            "closed ties/stirrups (s <= 3db, first one within 2db of "
                            "the bend) are required along ldh - not provided!")
        pr = 1.0
    elif bar_no <= 11:
        if hook_type == 90 and (hook_confined_along_ldh or hook_ext_confined):
            pr = 0.8
        elif hook_type == 180 and hook_confined_along_ldh:
            pr = 0.8
    return pe, pc, pr


def hooked():
    pe, pc, pr = hook_factors()
    ldh = fy * pe * pc * pr / (50 * lam * sqrt_fc) * db
    return dict(psi_e=pe, psi_c=pc, psi_r=pr, ldh_raw=ldh)


def hook_dimensions():
    """Standard hook per Fig. 6.9 / Table 6.2"""
    # minimum inside bend diameter (Table 6.2)
    if bar_no <= 8:
        D = 6 * db
        if is_stirrup_hook and bar_no <= 5:
            D = 4 * db
    elif bar_no <= 11:
        D = 8 * db
    else:
        D = 10 * db

    if not is_stirrup_hook:
        if hook_type == 90:
            ext = 12 * db
        elif hook_type == 180:
            ext = max(4 * db, 2.5)
        else:
            warnings.append("Standard hook for main bars is only 90° or 180°")
            ext = None
    else:   # stirrup / tie
        if hook_type == 90:
            ext = max(6 * db, 3.0) if bar_no <= 5 else 12 * db
        elif hook_type == 135:
            ext = max(6 * db, 3.0)
        else:
            ext = max(4 * db, 2.5)
        if hook_type in (135, 180) and bar_no > 8:
            warnings.append("Stirrup/tie 135°/180° hooks are only for No. 8 and smaller bars")
        if hook_type == 90 and bar_no > 8:
            warnings.append("Stirrup/tie hooks are only for No. 8 and smaller bars")
    return D, ext


# Headed bar - Eq. 6.7 - Table 6.3
def headed():
    pe = 1.2 if is_epoxy else 1.0
    fc_used = min(fc, 6000)
    ldt = 0.016 * fy * pe / math.sqrt(fc_used) * db

    # Code restrictions
    if bar_no > 11:
        warnings.append("Headed bar: only No. 11 (No. 36) and smaller bars")
    if fy > 60000:
        warnings.append("Headed bar: fy must be <= 60,000 psi")
    if lam != 1.0:
        warnings.append("Headed bar: normalweight concrete only")
    if clear_cover < 2 * db:
        warnings.append(f"Headed bar: clear cover >= 2db ({2*db:.2f} in.) required")
    if clear_spacing < 4 * db:
        warnings.append(f"Headed bar: clear spacing between bars >= 4db "
                        f"({4*db:.2f} in.) required")
    if head_net_bearing_area is None:
        warnings.append("Headed bar: Abrg >= 4Ab not checked (bearing area not given)")
    elif head_net_bearing_area < 4 * Ab:
        warnings.append(f"Headed bar: Abrg = {head_net_bearing_area} in² < 4Ab "
                        f"= {4*Ab:.2f} in²")
    if obstruction_dist is not None and obstruction_dist > 2 * db:
        warnings.append("Headed bar: obstruction extends more than 2db from the "
                        "bearing face - HA head requirement not met")
    if fc > 6000:
        warnings.append("Headed bar: f'c = 6000 psi used (Code limit)")
    return dict(psi_e=pe, fc_used=fc_used, ldt_raw=ldt)


# Compare the required length with available_length (if given).
def check_available(required, label):
    if available_length is None:
        return
    diff = available_length - required
    if diff >= 0:
        print(f"  Check {label}: available {available_length:.1f} in. >= required "
              f"{required:.1f} in.  ->  OK (margin {diff:.1f} in.)")
    else:
        print(f"  Check {label}: available {available_length:.1f} in. < required "
              f"{required:.1f} in.  ->  NOT OK (short by {-diff:.1f} in.)")


def main():
    if mode not in ("straight", "hook", "headed", "all"):
        raise ValueError('mode must be "straight", "hook", "headed" or "all"')
    r = reduction() if mode in ("straight", "hook", "all") else 1.0

    print("=" * 64)
    print(f"Mode: {mode}")
    print(f"Bar No. {bar_no} (db = {db:.3f} in., Ab = {Ab} in²)   "
          f"fy = {fy} psi   f'c = {fc} psi")
    line = f"λ = {lam:.3f}   coating = {coating}"
    if mode in ("straight", "all"):
        line += f"   {'Top' if top_bar else 'Bottom'} bar (ψt = {psi_t()})"
    print(line)
    if mode in ("straight", "hook", "all"):
        print(f"As,req/As,prov reduction factor = {r:.3f}"
              f"{'  (not applicable)' if no_reduction_case else ''}")
    print("=" * 64)

    if mode in ("straight", "all"):
        # Table 6.1
        a = straight_table61()
        ld1 = max(a['ld'] * r, 12.0)
        print("\n[1] STRAIGHT BAR - Table 6.1 / Eq. (6.5a, 6.5b)")
        print(f"  Spacing case : {a['case']}   | group : "
              f"{'No.7 & larger' if large_group() else 'No.6 & smaller'}")
        print(f"  ψt = {a['psi_t']}, ψe = {a['psi_e']}, ψtψe = {a['psi_te']} (max 1.7)")
        print(f"  ld/db = {a['ld_db']:.1f}   ->   ld = {a['ld']:.1f} in.")
        print(f"  Final (reduction + min 12 in.) : {ld1:.1f} in. = {ld1/12:.2f} ft")
        check_available(ld1, "Table 6.1")

        # Table A.10
        print("\n[2] STRAIGHT BAR - Table A.10 (CSV)")
        if is_epoxy or lam != 1.0:
            print("  ** Table A.10 is only for uncoated bars and normalweight concrete **")
        else:
            try:
                c = table_a10()
                ld2 = max(c['ld'] * r, 12.0)
                print(f"  {c['position']} bar | {c['case']} | {c['group']} | "
                      f"{'exact' if c['exact'] else 'interpolated'}")
                print(f"  ld/db = {c['ld_db']:.1f}   ->   ld = {c['ld']:.1f} in.")
                print(f"  Final (reduction + min 12 in.) : {ld2:.1f} in. = {ld2/12:.2f} ft")
                check_available(ld2, "Table A.10")
            except ValueError as e:
                print("  " + str(e))

    if mode in ("hook", "all"):
        # Hook
        h = hooked()
        D, ext = hook_dimensions()
        print("\n[3] STANDARD HOOK - Eq. (6.6)")
        print(f"  Hook dimension: {hook_type}° {'stirrup/tie' if is_stirrup_hook else 'main bar'}"
              f" | min inside bend dia D = {D:.2f} in."
              + (f" | extension >= {ext:.2f} in." if ext else ""))
        if not is_stirrup_hook:
            ldh = max(h['ldh_raw'] * r, 8 * db, 6.0)
            print(f"  ψe = {h['psi_e']}, ψc = {h['psi_c']}, ψr = {h['psi_r']}, λ = {lam:.2f}")
            print(f"  ldh = {h['ldh_raw']:.1f} in.   ->   Final (reduction + "
                  f"min 8db, 6 in.) : {ldh:.1f} in.")
            check_available(ldh, "hook")

    if mode in ("headed", "all"):
        # Headed
        t = headed()
        ldt = max(t['ldt_raw'], 8 * db, 6.0)
        print("\n[4] HEADED BAR - Eq. (6.7) / Table 6.3")
        print(f"  ψe = {t['psi_e']}, f'c used = {t['fc_used']} psi")
        print(f"  ldt = {t['ldt_raw']:.1f} in.   ->   Final (min 8db, 6 in.; "
              f"no As reduction) : {ldt:.1f} in.")
        print("  (ldt is measured from the bearing face of the head to the critical section)")
        check_available(ldt, "headed bar")

    if warnings:
        print("\n--- WARNINGS ---")
        for w in dict.fromkeys(warnings):
            print("  * " + w)
    print()


if __name__ == "__main__":
    main()