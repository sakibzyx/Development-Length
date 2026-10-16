# Development Length Calculator

A Python script that computes the **tension development length** of reinforcing bars in reinforced concrete, following ACI 318 (as presented in Nilson–Darwin–Dolan, Chapter 6).

**Units:** psi and inches.

Development Length Calculator: https://sakibzyx.github.io/Development-Length/

## Features

| # | Calculation | Reference |
|---|---|---|
| 1 | Straight bar, simplified equations | Eqs. (6.5a, 6.5b) / Table 6.1 |
| 2 | Straight bar, table lookup with interpolation | Table A.10 (`table_A10.csv`) |
| 3 | Standard hook (90° / 180°) plus hook dimensions | Eq. (6.6), Fig. 6.9, Table 6.2 |
| 4 | Headed bar | Eq. (6.7) / Table 6.3 |

Also included:

- Modification factors: ψt (top bar), ψe (epoxy / dual coating), ψc and ψr (hooks), λ (lightweight concrete)
- Excess reinforcement reduction (As,required / As,provided)
- Minimum length checks: 12 in. (straight), 8db and 6 in. (hook, headed)
- Optional **OK / NOT OK** check against the available length
- Warnings for code limits (headed bar restrictions, missing stirrups at discontinuous ends, and so on)

## Files

```
development_length.py   # the calculator
table_A10.csv           # Table A.10 data (must be in the same folder)
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
| `mode` | `"straight"`, `"hook"`, `"headed"` or `"all"` |
| `available_length` | Length available (in.). `None` skips the OK / NOT OK check. Straight: from the critical section. Hook: embedment past the critical section. Headed: bearing face to critical section. |

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
| `hook_type` | `90` or `180` (`135` only for stirrups/ties) |
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

## Example

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

## Notes on the results

- **Table A.10** covers f'c = 4000 to 6000 psi and fy = 40 to 80 ksi in the provided CSV. Outside that range the script prints a message and skips the table. Use Table 6.1 in that case.
- Table A.10 applies **only to uncoated bars and normalweight concrete**.
- Table 6.1 and Table A.10 can differ slightly because the table values are rounded.
- The results are **sensitive to the inputs** (clear spacing, cover, stirrup condition). The script does not check that your geometry is consistent.

## Limitations

This script is **not** a complete development length tool. It does not include:

- Compression development length (column dowels, compression bars)
- Lap splices (Class A / Class B, compression splices)
- Bundled bars and welded wire reinforcement
- Flexural bar cutoff and anchorage checks (moment diagram, inflection points, ld ≤ 1.3·Mn/Vu + la)
- The hook location factor ψo and the ACI 318-19 hook equation (the script follows the ACI 318-14 style Eq. 6.6)
- The detailed confinement term (cb + Ktr)/db. Only the simplified Table 6.1 is used

For splices, a common workaround is to compute ld here and multiply by 1.0 (Class A) or 1.3 (Class B), with a 12 in. minimum. Do **not** apply the As excess reduction to splices.

For compression, ldc = max(0.02·fy·db / (λ·√f'c), 0.0003·fy·db, 8 in.).

## Disclaimer

For learning and preliminary checks. Always verify results against the governing code edition and have final design checked by a licensed engineer.
