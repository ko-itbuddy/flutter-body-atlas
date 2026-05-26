# svg-bezier scripts

`svgpathtools`-based Bezier path subdivision scripts used to produce
the muscle subdivision SVG paths in `assets/svg/muscle_layer_front.svg`
and `assets/svg/muscle_layer_back.svg` (health-customizations branch,
fork `ko-itbuddy/flutter-body-atlas` based on upstream `kit-g/flutter-body-atlas@0.1.4`).

## Purpose

Generate bezier-accurate subdivision SVG paths from existing parent
muscle paths by intersecting them with a horizontal/vertical line and
splitting via de Casteljau subdivision (svgpathtools `Path.cropped()`).
This preserves the parent path's curved silhouette (rounded edges,
fan-shape tapers) in each subdivision — polygon approximations leave
angular gaps when union-rendered as a heatmap.

## Common algorithm

```
parse_path(path_d)
  → Path.intersect(Line(0+y*1j, viewBox_w + y*1j))
    → 2 crossing T values (closed convex path)
      → sort + midpoint sampling to determine which arc is above/below the slice line
        → Path.cropped(T_start, T_end) de Casteljau split
          → Line close + Path.d() export
```

## Scripts

| Script | Slice axis | Slice count | Source muscle | Suffix labels |
|---|---|---|---|---|
| `pec_slice.py` | horizontal (y=233, y=291) | 3 (clavicular/sternal/costal) | `pectoralis_major_l/r` | `_clavicular`, `_sternal`, `_costal` |
| `back_lats_slice.py` | horizontal (y=365.5) | 2 (upper/lower) | `latissimus_dorsi_l/r` | `_upper`, `_lower` |

## Install

```bash
pip install svgpathtools
```

macOS users on PEP 668-managed Python (Homebrew default) — use one of:

```bash
pip3 install --user --break-system-packages svgpathtools
# or
python3 -m venv .venv && source .venv/bin/activate && pip install svgpathtools
```

Windows users (stock Python from python.org — no PEP 668) — `pip install svgpathtools` works as-is in PowerShell or cmd.

## Reuse

To slice another muscle:

1. Copy `pec_slice.py` (vertical/horizontal slice, 2-way or 3-way) or `back_lats_slice.py` as template.
2. Replace path d= constants (`PEC_L`/`PEC_R` etc.) with target muscle path strings from the SVG.
3. Adjust slice coordinates (`Y_TOP`, `Y_BOT`, `Y_MID`) per anatomic ratio.
4. Adjust suffix labels for output (`upper`/`lower`/`clavicular`/etc.).
5. Run script → copy output `d=` strings into SVG `<path id="..._sub_l/r">` entries.
6. Add new `Muscle` enum values + `MuscleCatalog` entries in `lib/src/models/muscle.dart`.

## Generalize (Phase 6+ candidate)

Current two scripts share ~90% of the slicing logic. When a third
subdivision use-case lands (rule-of-3), extract `slice_path(path_d, lines, suffix_map)` into
a shared module. Until then, two parallel scripts keep things obvious.

## Provenance

- `pec_slice.py` introduced in fork commit `cbdb6b8` (tag `health-custom-v0.1.4+2`)
- `back_lats_slice.py` introduced in fork commit `ece5b92` (tag `health-custom-v0.1.4+3`)
- Both scripts mirrored in `ko-itbuddy/health` repo at `docs/research/svg-bezier-scripts/`
- See `.handoff/reports/handoff/20260525-2227-...` + `20260526-0008-...` + `20260526-0017-...` + `20260526-0112-...` + `20260526-0120-...` for full slice rollout history.
