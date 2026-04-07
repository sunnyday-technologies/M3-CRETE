# M3-CRETE CAD Assembly — Session Handoff (2026-04-02)

## What Was Done This Session

Built the first AI-generated multi-part CAD assembly of the M3-CRETE M3-2
concrete 3D printer. 40 parts, from OpenBuilds STEP components + parametric
extrusions. 12 iterations to get the frame right.

### Commit Ready to Push
```
Branch: seo-main2
Commit: 29c439c
Message: feat: add draft v0.1.0 CAD assembly — AI-generated 40-part M3-2 digital twin
Push command: cd Z:\SunnydayTech\M3-CRETE && git push origin seo-main2
```

### Files Committed
- `CAD/m3_2_assembly.py` — Main assembly generator (v0.1.0, 40 parts)
- `CAD/parametric_extrusions.py` — Generates exact-length V-Slot via non-uniform Z-scaling
- `CAD/deep_probe.py` — Extracts bolt holes, faces, V-grooves from STEP files
- `CAD/probe_steps.py` — Bounding box inspector for all STEP components
- `CAD/README.md` — Updated with assembly docs
- `.gitignore` — Updated to exclude dev/test files

### Files NOT Committed (dev-only, gitignored)
- `CAD/M3-2_Assembly.step` — Generated output (rebuild with m3_2_assembly.py)
- `CAD/M3-2_Assembly1-4.step` — Nick's Fusion iteration files
- `CAD/box_test.py`, `corner_test.py`, `rotation_test.py` — Test scripts
- `CAD/read_adjusted.py`, `read_v3.py` — Position extraction scripts
- `CAD/Custom/` — Generated parametric extrusion STEPs

### CadQuery Environment
- **Venv:** `Z:/SunnydayTech/M3-CRETE/cad_venv/Scripts/python.exe`
- **Python:** 3.11.9
- **CadQuery:** 2.7.0 (with cadquery-ocp 7.8.1.1)
- **Rebuild:** `cad_venv/Scripts/python.exe CAD/m3_2_assembly.py`

## Current Assembly State (v0.1.0)

### Frame (open-bottom bridge)
- 4x 2040 posts (40x20mm profile, rz=90 rotated, 1200mm full height)
- 4x 2080 top X-rails (1160mm segments, spliced at X=1200, 80mm VERTICAL)
- 3x 2040 top Y-braces (left, center splice, right)
- 2x 2040 bottom Y-braces (left + right only — NO bottom X-rails, open front/back)

### Z-Platform (moves up/down)
- 2x 2080 Y-rails (left + right sides, 1154mm, inside post faces)
- Gantry moves along Y (short axis = less inertia)

### Gantry
- 1x 2080 beam (2270mm, spans X, 80mm vertical)
- Printhead carriage moves along X (long axis) on the beam

### Plates
- 8x gantry plates sandwiching 4 posts (Z-carriages, ride posts with V-wheels)
- 2x X-carriage plates sandwiching gantry beam
- 3x X-end/Y-rail connection plates

### Motors
- 4x Z motors: HORIZONTAL at post tops, shaft pointing INWARD (preserves build height)
- 2x Y motors: INSIDE frame, at back end of Y-rails, shaft along +Y
- 1x X motor: on carriage, above gantry beam

### Key Dimensions
- External: 2400 x 1200 x 1200mm
- Post profile: 40mm(X) x 20mm(Y) (rotated from native 2040)
- Inner X span: 2320mm (post-to-post)
- Inner Y span: 1160mm (post-to-post)
- Top rail Z: 1100-1180mm
- Z-platform at Z=440 (40% height, representative position)
- Gantry beam at Z=360 (80mm below Y-rails, no intersection)

### Parametric Extrusion Technique
Non-uniform Z-scaling of OpenBuilds 1000mm STEP files via OCP `gp_GTrsf` +
`BRepBuilderAPI_GTransform`. Preserves exact V-groove geometry, fillet radii,
and slot dimensions. Only the length axis is scaled. Then bake-in rotation
via `BRepBuilderAPI_Transform` so shapes are pre-oriented (no assembly-time rotation bugs).

## Remaining TODO (v0.2.0)

### Priority 1: Z-Belt System
- [ ] Add GT2 idler pulleys at BOTTOM of each Z-post
- [ ] Belt path: motor pulley (top, horizontal) → down post → around bottom idler → back up to carriage
- [ ] Posts serve dual-purpose: structural + Z guide rail

### Priority 2: V-Wheel Carriages
- [ ] Extract carriage pattern from `Advanced/Assemblies/Nema 17 V Slot Belt Driven Actuator 500mm.step`
- [ ] Carriage = plate + 4 V-wheels (2 eccentric + 2 straight) + eccentric spacers
- [ ] Place at: Z-carriages (4x, ride posts), Y-carriages (2x, ride Y-rails), X-carriage (1x, ride beam)

### Priority 3: Belt Paths
- [ ] GT2 10mm belt for each axis
- [ ] Y-axis: motor pulley → along Y-rail → idler at far end → back
- [ ] X-axis: motor pulley → along gantry beam → idler → back
- [ ] Z-axis: motor pulley → down post → bottom idler → up to carriage

### Priority 4: Remaining Details
- [ ] Splice connectors at X-rail junction (X=1200)
- [ ] Fix any remaining volume intersections (run Fusion interference check)
- [ ] BOM cross-reference audit (assembly parts vs bom/data.json)
- [ ] Add limit switches at axis endpoints

### Priority 5: Git
- [ ] Push commit 29c439c to GitHub (`git push origin seo-main2`)
- [ ] Create PR to main if ready

## Key Technical Decisions

1. **Posts rotated (rz=90)**: 40mm in X, 20mm in Y. Gives wider face for Z-carriage wheels.
2. **Gantry beam below Y-rails**: Beam at Z=360, Y-rails at Z=440. Prevents intersection.
3. **X-Y axis swap**: Gantry moves along Y (short, 1200mm) for less inertia. Printhead moves along X (long, 2400mm) on the beam.
4. **Z-motors horizontal**: At post tops, shaft inward. Preserves build height, prevents knock-off.
5. **Y-motors inside frame**: At back end of Y-rails. Keeps exterior clean.
6. **Open bottom**: No front/back X-rails at floor level. Printer straddles walls for continuous printing.
7. **All extrusions 1200mm cut length**: Single SKU for procurement. Parametric script generates exact lengths.

## Research Finding: AI-Generated CAD Assembly

This appears to be the first documented case of an AI/LLM generating a multi-part
mechanical assembly from real vendor STEP files. All existing AI-CAD tools (Zoo.dev,
STEP-LLM, CADSmith, etc.) only generate single parts. See research details in the
conversation history.

## Nick's Fusion Correction Files
- `M3-2_Assembly2.step` — First corrections (rotated posts, plate orientation)
- `M3-2_Assembly3.step` — Motor positions, plate sandwiching
- `M3-2_Assembly4.step` — Final reference (all positions used in v0.1.0)
These are in the CAD folder locally but gitignored.
