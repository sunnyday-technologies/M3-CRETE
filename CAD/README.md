# M3-CRETE CAD Files

3D models for the M3-CRETE concrete 3D printer motion system.

## Directory Structure

```
CAD/
├── Components/     Standard V-Slot parts (OpenBuilds-compatible, CC BY-SA 4.0)
│   ├── V-Slot/         Extrusion profiles (2020, 2040, 2080)
│   ├── Plates/         Gantry plates, motor mounts, idler plates
│   ├── Wheels/         V-wheels (Delrin, Xtreme, idler pulleys)
│   ├── Bearings/       625-2RS, 688Z ball bearings
│   ├── Brackets/       Corner brackets, actuator end mounts
│   └── Hardware/       Eccentric spacers, shims, T-nuts
├── Custom/         Sunnyday-designed parts (CERN-OHL-W-2.0)
│   ├── Frame-Stiffener.step
│   └── Extruder-Mount-NPT.step
└── Advanced/       Compatible hardware for extended builds
    └── (alternative extrusion profiles, reinforcement options)
```

## Format

All models are provided in **STEP** format (.step / .stp) for maximum compatibility with FreeCAD, Fusion 360, SolidWorks, Onshape, and other CAD tools.

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
| V-Slot extrusions | 3 (2080, 2040×2) | 27 lengths |
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

To add a CAD model:
1. Export as STEP (.step or .stp)
2. Name it to match the BOM part name
3. Place in the appropriate directory
4. Submit a Pull Request

Models are linked to the [BOM Viewer](https://m3-crete.com/bom/) via the `step_url` field in `bom/data.json`.
