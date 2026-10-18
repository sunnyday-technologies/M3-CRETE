# M3-CRETE CAD Files

3D models for the M3-CRETE concrete 3D printer motion system.

## Assembly (Draft v0.1 — In Development)

The M3-2 digital twin assembly is generated programmatically from the STEP
component library using CadQuery + Python. This is believed to be the first
AI-assisted multi-part mechanical assembly generated from real vendor STEP files.

**Status:** frame, gantry and lead-screw Z modeled (BOM v2.9.0, 2026-10-12);
see `bom/data.json` for parts whose printable geometry is still pending.

### Source of Truth: `m3_2_assembly.py`

`CAD/m3_2_assembly.py` is the **canonical source** for the M3-2 assembly. It
starts from `M3-2_V1.0_baseline.step`, the 146-part V1.0 assembly (2026-04-29),
and adds the lead-screw Z on top of it. It also restores the 17 C-beams from
the complete supplier solid, preserving all holes, cavities and world
placements. All 17 use one shared STEP part definition to limit file size.
The script writes `M3-2_Assembly_cbeam_candidate.step` and refuses to overwrite
an existing candidate. The baseline is preserved. The tracked
`M3-2_Assembly.step` contains the verified complete-solid correction promoted
on 2026-10-17; the previous open-shell export remains in Git LFS history.
Future regeneration still writes a local candidate for verification before
owner-approved replacement of the tracked export.

The promoted STEP is 20,663,068 bytes, down from 24,668,018 bytes (16.2%).
Its SHA-256 is `6c41f5ee9417a362556eef24541dcb32627a9314ed751aa88a6340c7a23dbfde`.
All 17 supplier profiles and placements were preserved without simplifying
slots. CADCLAW's unchanged source-group qualification reconciled 158 solids
across flat and XCAF imports with complete coverage; the assembly self-check
also passed. These results establish numerical CAD checks, not physical
validation.

To modify the design, edit parameters in `m3_2_assembly.py` and regenerate the
candidate. Do **not** hand-edit the derived STEP and expect those edits to
be reproduced by the generator.

This satisfies the CERN-OHL-W-2.0 requirement to distribute the preferred form
for modification: the parametric Python script is human-readable, diffable, and
tool-agnostic — a better open-source workflow than shipping a binary Fusion 360
file that requires a specific version of proprietary software to open.

```
python CAD/derive_z_motor_mount.py  # Custom/Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step + .stl
python CAD/z_bottom_holder.py       # Custom/Z_Bottom_Bearing_Holder_M3-2.step + .stl
python CAD/m3_2_assembly.py         # Generates a new M3-2_Assembly_cbeam_candidate.step
python CAD/self_check.py CAD/M3-2_Assembly_cbeam_candidate.step  # Check the saved candidate
python CAD/z_travel.py              # Z carriage stroke -> firmware position_max
python CAD/bom_generate.py          # bom_structural.csv, bom_hardware.csv, BOM_README.md
```

**Requirements:** Python 3.11 + CadQuery 2.7.0 (`pip install cadquery`)

For the bounded C-beam correction of the existing export, without regenerating
other components:

```
python CAD/cbeam_solids.py --receipt build/cbeam-export.json
python CAD/verify_cbeam_candidate.py --original path/to/pre-correction.step --candidate CAD/M3-2_Assembly.step --cadclaw ../CADCLAW --receipt build/cbeam-verification.json
```

Create the receipt directory first. For the historical correction regression,
restore the pre-correction export from Git LFS history to a separate local
path and pass it with `--original`; its SHA-256 is
`9d6f4e94d025ce30f80eb827451663e24e19dffb4fdc393c3a3c3636f3da5fd8`.
The verifier expects that historical source to fail the solid gate and the
corrected export to pass. Verification compares all 158 occurrences,
requires 17 valid closed supplier solids with 11 internal loops at both ends,
and runs CADCLAW's existing source-group qualification without changing its
rules. The candidate is ignored; keep recovery copies outside the repository.
Replace the tracked export after approval rather than publishing
duplicate full assemblies; Git LFS history retains prior revisions.

**Assembly contents (158 occurrences):**
- 17x C-Beam 4080 1000mm extrusions (posts, top frame, bottom Y rails, Y and X gantry beams) + 3x internal 2040 splice inserts
- 8x gantry plates and 32x V-wheels
- 7x NEMA23 motors (4 Z shaft-down on the post tops, 2 Y, 1 X)
- Per Z post: printed motor mount, coupler, 2 lock collars + 2 thrust bearings, Tr8x2 lead screw, nut block, printed bottom holder with a 608 bearing
- Printed plates: 2 Y-motor mounts, 4 Z-post bottom plates (6 mm), 2 center T-gussets; 6 mm post-to-end-beam spacers throughout
- Y belts and pulleys; one Y return idler (envelope of the 20T toothless part) inside each Y rail's channel

**Open-bottom bridge frame** — no front/back bottom rails, allowing the printer
to straddle walls for continuous printing.

## Directory Structure

```
CAD/
├── Components/     Standard parts (OpenBuilds-compatible, CC BY-SA 4.0)
│   ├── V-Slot/         Extrusion profiles (4080 C-Beam primary)
│   ├── Plates/         Gantry plates, motor mounts, idler plates
│   ├── Wheels/         V-wheels (Delrin, Xtreme, idler pulleys)
│   ├── Bearings/       625-2RS, 688Z ball bearings
│   ├── Brackets/       Corner brackets, actuator end mounts
│   └── Hardware/       Eccentric spacers, shims, T-nuts
├── Custom/         Sunnyday-designed parts (CERN-OHL-W-2.0)
│   ├── Center_T_Bracket_Expanded.step / .stl
│   ├── Corner_Bracket_Combined.step / .stl
│   ├── Z_NEMA23_Leadscrew_Motor_Mount_GrokBot.step   (as authored; input to derive_z_motor_mount.py)
│   ├── Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step / .stl  (BOM id 24)
│   └── Z_Bottom_Bearing_Holder_M3-2.step / .stl      (BOM id 91)
└── Advanced/       Compatible hardware for extended builds
    └── (alternative extrusion profiles, reinforcement options)
```

## Format

Component parts (`Components/`, `Advanced/`) and custom parts (`Custom/`) are
provided in **STEP** format (.step / .stp) for maximum compatibility with
FreeCAD, Fusion 360, SolidWorks, Onshape, and other CAD tools.

The **M3-2 assembly itself** uses the parametric Python script
(`m3_2_assembly.py`) as its source format, with `M3-2_Assembly.step` as the
generated output (see "Source of Truth" above).

## Component Parts — Sources

The standard V-Slot components in `Components/` are based on the [OpenBuilds](https://openbuilds.com) parts ecosystem, licensed under **CC BY-SA 4.0**.

### Where to Get STEP Files

If a part is not yet in this repo, you can download STEP models from:

| Source | URL | Notes |
|--------|-----|-------|
| **GrabCAD — OpenBuilds Gantry Set** | [grabcad.com/library/openbuilds-v-slot-gantry-set-all-sizes-1](https://grabcad.com/library/openbuilds-v-slot-gantry-set-all-sizes-1) | Complete gantry assemblies, all V-Slot sizes |
| **GrabCAD — V-Slot Tag** | [grabcad.com/library/tag/v-slot](https://grabcad.com/library/tag/v-slot) | Individual parts and assemblies |
| **Printables — Universal Gantry Plate** | [printables.com/model/459195](https://www.printables.com/model/459195-openbuilds-v-slot-gantry-plate-universal) | STL for 3D printing |
| **StepperOnline — NEMA23 Models** | [omc-stepperonline.com/download](https://www.omc-stepperonline.com/download) | Motor STEP files by MPN |
| **BTT — Kraken Board** | [github.com/bigtreetech/Kraken](https://github.com/bigtreetech/Kraken/tree/master/Hardware) | Controller board models |

### M3-CRETE Part Count

The M3-2 uses approximately **20 unique component types** (many repeated):

| Component | Unique Models | Total Qty |
|-----------|--------------|-----------|
| C-Beam 4080 extrusions | 1 (4080 C-Beam) | ~17 segments |
| Gantry/carriage plates | 3 types | 12 plates |
| Motor mounts | 1 type | 8 mounts |
| V-wheels | 2 types | 36 wheels |
| GT2 pulleys | 2 types | 20 pulleys |
| Bearings/spacers | 3 types | 28+ pieces |
| Custom parts | 2 (stiffener, extruder mount) | 5 parts |

## License

- **Components/** — CC BY-SA 4.0 (based on OpenBuilds designs, attribution required)
- **Custom/** — CERN-OHL-W-2.0 (same as M3-CRETE project)
- **Advanced/** — Mixed, see individual files

## Contributing

**To modify the M3-2 assembly:** Edit `m3_2_assembly.py` (the canonical
source), regenerate `M3-2_Assembly.step`, and commit both. Do not edit the
STEP directly.

**To add a new component model:**
1. Export as STEP (.step or .stp)
2. Name it to match the BOM part name
3. Place in the appropriate directory (`Components/`, `Custom/`, or `Advanced/`)
4. Submit a Pull Request

Models are linked to the [BOM Viewer](https://bom.m3-crete.com/bom/) via the `step_url` field in `bom/data.json`.
