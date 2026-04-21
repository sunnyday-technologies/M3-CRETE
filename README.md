# M3-CRETE — Open-Source Concrete 3D Printer

**A large-format cartesian printer built for cementitious material extrusion at scale.**

M3-CRETE is an open-source hardware project for building a concrete 3D printer from standard, commercially available components. The system is purpose-built for layer-by-layer extrusion of cementitious materials — no heated beds, no proprietary toolchains, no vendor lock-in.

**M³** = **M**obile · **M**odular · **M**eter³

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19647436.svg)](https://doi.org/10.5281/zenodo.19647436)

Developed by [Sunnyday Technologies](https://sunn3d.com).

| Spec | Value |
|------|-------|
| **Target system cost** | Under $5,000 |
| **Build footprint** | Sub-1 m³ — fits on a standard US pallet (48×40 in) |
| **Printhead weight** | ~1.5 kg |
| **License** | CERN-OHL-W-2.0 |

---

## Why M3-CRETE

Most concrete 3D printers are either proprietary industrial systems or one-off research machines tied to specific institutions. M3-CRETE targets the space between — a buildable, field-serviceable, production-capable printer that teams can replicate, maintain, and scale independently.

### Target Applications

- Hardscape and site elements
- Agricultural and industrial processing infrastructure
- Urban water control and drainage components
- Construction and infrastructure parts
- Modular elements for rapid deployment and disaster response
- Digital formwork and precast molds

These are applications where repeatability, throughput, and reliability matter — and where accessible hardware can have the most immediate impact.

---

## Design Principles

### CNC Rigidity, Field Serviceability

The frame is engineered closer to CNC machine standards than desktop 3D printers: rigid, durable, and precise. Every structural component uses standard aluminum extrusions and commodity hardware. If something breaks on a job site, you source a replacement locally — not from a single-source vendor.

### Small Motors, Safe Envelope

With an efficient frame design, the drive system uses motors comparable in size to hobbyist 3D printers while delivering sufficient torque for the full gantry. This provides a significantly safer working envelope for students, researchers, and craftsmen compared to heavy industrial machinery.

### No Thermal Management

Concrete cures by hydration — a chemical reaction — not by melting and cooling. This eliminates roughly 25% of the hardware cost and complexity associated with conventional FDM printers (heated beds, hot ends, cooling fans), resulting in a mechanically simpler, more energy-efficient, and more reliable machine.

### Built to Multiply

Many non-structural components — brackets, guides, and enclosure parts — are designed to be 3D-printable using an existing M3-CRETE unit or any FDM printer. This reduces replication cost and simplifies field replacement. Scalability is a feature, not an afterthought.

---

## Firmware and Software Compatibility

M3-CRETE runs on established open-source toolchains. No proprietary software required.

| Layer | Compatible Tools |
|-------|-----------------|
| **Firmware** | Marlin, Klipper |
| **Slicers** | Cura, OrcaSlicer, PrusaSlicer |
| **Controls** | Standard stepper drivers, common control boards |
| **CAD/CAM** | Any tool that exports STL, OBJ, or 3MF |

Standard G-code workflows provide full, transparent control over toolpaths, layer heights, and extrusion parameters.

Firmware configurations are maintained separately:
[M3-CRETE-FIRMWARE](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE)

---

## Repository Structure

```
M3-CRETE/
├── CAD/
│   ├── M3-2_Assembly.step       # Full assembly (99 parts, 13.5 MB via LFS)
│   ├── m3_2_assembly.py         # CadQuery assembly generator (source of truth)
│   ├── self_check.py            # 5-gate automated validation harness
│   ├── kinematics_eval.py       # Structural analysis (deflection, torque, belts)
│   ├── Custom/                  # 3D-printable brackets (STEP + STL)
│   ├── Components/              # OpenBuilds parts library (CC BY-SA 4.0)
│   └── Advanced/                # Extended parts (C-beam, joining plates)
├── bom/
│   ├── data.json                # BOM source of truth (62 parts, v2.5.0)
│   └── index.html               # Interactive BOM viewer (m3-crete.com/bom)
├── firmware/                    # Klipper configs (kinematics, steppers)
├── blog/                        # Build logs and project updates
└── config.js                    # Model variants (M3-1, M3-2, M3-4)
```

### AI-Assisted CAD Workflow

This project uses [CADCLAW](https://github.com/sunnyday-technologies/CADCLAW) — an automated validation framework for STEP assemblies developed during this project. The assembly script generates geometry, the self-check harness validates it (inventory, interference, adjacency, dimensions), and the kinematics module analyzes structural performance. This workflow caught 53 interferences and reduced the STEP file from 70 MB to 13 MB.

See the [CADCLAW repo](https://github.com/sunnyday-technologies/CADCLAW) for the generalized, reusable framework.

---

## Material Compatibility

M3-CRETE is a hardware platform — it does not prescribe a specific concrete mix. The system is designed to work with a range of cementitious formulations optimized for layered extrusion, including OPC, LC3, and specialty blends.

For AI-driven mix design optimized for 3D printing, see [CEMFORGE™](https://cemforge.ai/concrete-printers/) — a machine learning formulation engine trained exclusively on 3D-printed cementitious specimen data, designed to generate printable concrete mixes with target performance characteristics.

---

## Project Status

M3-CRETE is in active development. Current focus areas:

- Finalizing the build-it-yourself kit BOM and documentation
- Preparing for the first production run
- Establishing firmware profiles for concrete-specific extrusion parameters

Interested in early access, collaboration, or providing field feedback?
See the **[project page →](https://sunn3d.com/m3-crete/)**

---

## Disclaimer

M3-CRETE is provided as-is for educational and development purposes. Concrete 3D printing involves heavy machinery, cementitious materials, and electrical systems that pose safety risks. Users assume all responsibility for safe design, construction, and operation of any system built from these files. Sunnyday Technologies makes no warranties regarding fitness for any particular purpose and assumes no liability for injury, damage, or loss resulting from the use of these designs. Consult applicable local building codes, electrical codes, and safety regulations before construction or operation.

See [DISCLAIMER.md](DISCLAIMER.md) for full details.

---

## License

This project is licensed under the **CERN Open Hardware Licence Version 2 — Weakly Reciprocal** ([CERN-OHL-W-2.0](https://ohwr.org/cern_ohl_w_v2.txt)).

You may use, modify, and distribute this design under the terms of that license. Modifications to covered files must be made available under the same license. This project includes no warranty of any kind.

**Dual License Notice:** V-Slot component CAD models in `CAD/Components/` are based on [OpenBuilds](https://openbuilds.com) designs and are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). All other project files (custom parts, BOM viewer, firmware configs, documentation) are licensed under CERN-OHL-W-2.0.

See [LICENSES/](LICENSES/) for full license texts.

---

## Related Projects and Resources

| Resource | Description |
|----------|-------------|
| [Sunnyday Technologies](https://sunn3d.com) | Parent company — concrete 3D printing and engineered cementitious composites |
| [M3-CRETE Project Page](https://sunn3d.com/m3-crete/) | Kit details, design philosophy, and contact for early access |
| [CADCLAW](https://github.com/sunnyday-technologies/CADCLAW) | Automated STEP assembly validation — extracted from this project |
| [CEMFORGE™](https://cemforge.ai/concrete-printers/) | AI-powered concrete formulation platform by Sunnyday Technologies |
| [M3-CRETE Firmware](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE) | Firmware configurations for Klipper |

---

## Author

**Nicholas Sonnentag** — mechanical engineer, founder of [Sunnyday Technologies](https://sunn3d.com). M3-CRETE is designed and maintained by Nick; CAD iteration is AI-assisted (Claude, Anthropic) but the engineering judgment, component selection, build decisions, and direction are his.

- LinkedIn: [Nicholas Sonnentag](https://www.linkedin.com/in/nicholas-sonnentag)
- Email: `nickworks@sunn3d.com`

## Citation

If you use M3-CRETE designs in research, a build, or derivative work, please cite:

```
Sonnentag, N. (2026). M3-CRETE: Open-Source Concrete 3D Printer.
Sunnyday Technologies.
https://github.com/sunnyday-technologies/M3-CRETE
```

A [`CITATION.cff`](CITATION.cff) file is included for automated citation tooling.

## Contributing

We welcome issues, pull requests, and design feedback. If you're building a concrete printer or working with cementitious extrusion, your field experience is valuable — open an issue or start a [discussion](https://github.com/sunnyday-technologies/M3-CRETE/discussions).

**Contact:** info@sunn3d.com
