# Development Length Calculator

A Python-based calculator for determining the development length of reinforcing bars in reinforced concrete, covering both tension and compression, in accordance with ACI 318 provisions as presented in Design of Concrete Structures by Nilson, Darwin, and Dolan (15th Edition, Chapter 6).

**Units:** psi and inches.

**Development Length Calculator:** https://sakibzyx.github.io/Development-Length/

## Features

| # | Calculation | Reference |
|---|---|---|
| 1 | Straight bar, simplified equations | Eqs. (6.5a, 6.5b) / Table 6.1 |
| 2 | Straight bar, table lookup with interpolation | Table A.10 (`table_A10.csv`) |
| 3 | Standard hook (90° / 180°) plus hook dimensions | Eq. (6.6), Fig. 6.9, Table 6.2 |
| 4 | Headed bar | Eq. (6.7) / Table 6.3 |
| 5 | Bar in compression, formula | Eqs. (6.10a, 6.10b) / Table 6.4 |
| 6 | Bar in compression, table lookup with interpolation, compared with [5] | Table A.11 (`table_A11.csv`) |

Also included:

- Modification factors: ψt (top bar), ψe (epoxy / dual coating), ψc and ψr (hooks), ψr (compression confinement), λ (lightweight concrete)
- Excess reinforcement reduction (As,required / As,provided)
- Minimum length checks: 12 in. (straight), 8db and 6 in. (hook, headed), 8 in. (compression)
- Optional **OK / NOT OK** check against the available length
- Warnings for code limits (headed bar restrictions, missing stirrups at discontinuous ends, hooks and heads not effective in compression, and so on)

## Files

```
development_length.py   # the calculator
table_A10.csv           # Table A.10 data
table_A11.csv           # Table A.11 data
```

## Requirements

- Python 3.8 or newer
- Standard library only (`csv`, `math`, `os`), so there is nothing to install

## Usage

1. Open `development_length.py`.
2. Edit the **Input parameters** block at the top.
3. Run:

```bash
python development_length.py
```

## Input parameters

### Mode and check

| Variable | Description |
|---|---|
| `mode` | `"straight"`, `"hook"`, `"headed"`, `"compression"` or `"all"` |
| `available_length` | Length available (in.). `None` skips the OK / NOT OK check. Straight: from the critical section. Hook: embedment past the critical section. Headed: bearing face to critical section. Compression: embedment length of the straight bar. |

### Common

| Variable | Description |
|---|---|
| `fy` | Steel yield strength (psi) |
| `fc` | Concrete f'c (psi) |
| `bar_no` | US bar number: 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 18 |
| `concrete_below_bar` | Depth of fresh concrete below the bar (in.). Above 12 in. means top bar, ψt = 1.3 |
| `coating` | `"uncoated"`, `"galvanized"`, `"epoxy"` or `"dual"` |
| `lam` | λ: 1.0 for normalweight, 0.75 for lightweight (or λ = fct / (6.7·√f'c) ≤ 1.0 if fct is specified) |
| `As_required`, `As_provided` | in². Used for the excess reinforcement reduction. `None` means no reduction |
| `no_reduction_case` | `True` if the reduction is not applicable (anchorage for fy specifically required, or SDC D, E, F) |

### Straight bar

| Variable | Description |
|---|---|
| `clear_spacing` | Clear spacing of bars being developed (in.) |
| `clear_cover` | Clear cover (in.) |
| `stirrups_ok` | Stirrups/ties throughout ld at least the Code minimum? |
| `USE_ACI408` | `True` uses the No. 7 and larger formulas for all bar sizes |

### Hook

| Variable | Description |
|---|---|
| `hook_type` | `90` or `180` for main bars (`135` only for stirrups/ties; for a main bar the script shows a warning and does not calculate ldh) |
| `is_stirrup_hook` | `True` shows only the hook dimensions |
| `side_cover` | Side cover normal to the plane of the hook (in.) |
| `ext_cover` | Cover on the bar extension of a 90° hook (in.) |
| `hook_confined_along_ldh` | Ties/stirrups along ldh with s ≤ 3db? |
| `hook_ext_confined` | (90° only) Bar extension enclosed by ties with s ≤ 3db? |
| `discontinuous_end_small_cover` | Discontinuous end with side and top/bottom cover both < 2.5 in.? |

### Headed bar

| Variable | Description |
|---|---|
| `head_net_bearing_area` | Net bearing area Abrg (in²). `None` means not checked |
| `obstruction_dist` | Obstruction of deformations from the bearing face (in.). `None` means no obstruction |

### Compression

| Variable | Description |
|---|---|
| `comp_confined` | `True` if the bar is enclosed by a spiral (at least 1/4 in. diameter, pitch ≤ 4 in.) or by No. 4 ties at ≤ 4 in. on centers. This gives ψr = 0.75 and selects the Confined column of Table A.11. `False` gives ψr = 1.0 |

## Examples

### Straight bar

Bottom bars, 4 No. 8, f'c = 3 ksi, fy = 60 ksi, uncoated:

```python
mode = "straight"
fy = 60000
fc = 3000
bar_no = 8
concrete_below_bar = 8.0
clear_spacing = 7/3 - 1     # about 1.33 in.
clear_cover = 2.0
stirrups_ok = True
```

Output:

```
[1] STRAIGHT BAR - Table 6.1 / Eq. (6.5a, 6.5b)
  Spacing case : a   | group : No.7 & larger
  ld/db = 54.8   ->   ld = 54.8 in.
  Final (reduction + min 12 in.) : 54.8 in. = 4.56 ft
```

### Compression

No. 8 bar, f'c = 4 ksi, fy = 60 ksi, no confinement, no excess reinforcement:

```python
mode = "compression"
fy = 60000
fc = 4000
bar_no = 8
comp_confined = False
```

Output:

```
[5] BAR IN COMPRESSION - Eqs. (6.10a, 6.10b) / Table 6.4
  lambda = 1.00
  Eq. 6.10a : fy/(50*lambda*sqrt(f'c)) * db = 19.0 in.
  Eq. 6.10b : 0.0003*fy*db                  = 18.0 in.
  Basic ldc (greater) = 19.0 in.
  x psi_r 1.0  x excess-reinforcement factor 1.000  ->  19.0 in.
  Final (min 8 in.) : 19.0 in. = 1.58 ft

[6] BAR IN COMPRESSION - Table A.11 (CSV)
  Column: Basic | exact
  Table ldc = 19.0 in.   x excess-reinforcement factor 1.000
  Final (min 8 in.) : 19.0 in. = 1.58 ft
  Comparison: Table A.11 = 19.0 in.  vs  formula [5] = 19.0 in.  ->  difference +0.0 in. (table values are rounded up to whole inches)
```

## Notes on the results

- **Table A.10** covers f'c = 4000 to 6000 psi and fy = 40 to 80 ksi in the provided CSV. Outside that range the script prints a message and skips the table. Use Table 6.1 in that case.
- Table A.10 applies **only to uncoated bars and normalweight concrete**.
- Table 6.1 and Table A.10 can differ slightly because the table values are rounded.
- **Table A.11** covers f'c = 3000 to 6000 psi and fy = 40 to 80 ksi for all bar sizes, **normalweight concrete only**. Its values are rounded up to whole inches, so it can be up to about 1 in. longer than the formula result.
- **Compression:** ψr (0.75 for confinement) and the excess reinforcement factor are modification factors applied to the **greater** of Eq. (6.10a) and Eq. (6.10b), as in Table 6.4 B. Table A.11 is built the same way (for example No. 8, fy = 60 ksi, f'c = 5000 psi: Basic 18 in., Confined 14 in. = 0.75 × 18). The 8 in. minimum is applied last.
- Hooks and heads are **not** effective in compression and are ignored.
- The results are **sensitive to the inputs** (clear spacing, cover, stirrup condition). The script does not check that your geometry is consistent.

## Limitations

This script is **not** a complete development length tool. It does not include:

- Lap splices (Class A / Class B, compression splices) in the Python script. The web version includes a tension lap splice section
- Bundled bars and welded wire reinforcement
- Flexural bar cutoff and anchorage checks (moment diagram, inflection points, ld ≤ 1.3·Mn/Vu + la)
- The hook location factor ψo and the ACI 318-19 hook equation (the script follows the ACI 318-14 style Eq. 6.6)
- The detailed confinement term (cb + Ktr)/db. Only the simplified Table 6.1 is used

For splices in the Python script, a common workaround is to compute ld here and multiply by 1.0 (Class A) or 1.3 (Class B), with a 12 in. minimum. Do **not** apply the As excess reduction to splices.

## Disclaimer

For learning and preliminary checks. Always verify results against the governing code edition and have final design checked by a licensed engineer.
