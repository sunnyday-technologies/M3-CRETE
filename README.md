# M3-CRETE — Experimental Open-Hardware Concrete/Paste Printing Reference

**A meter-scale cartesian motion reference for qualified technical teams working
with cementitious material extrusion in controlled R&D, laboratory, or
supervised institutional settings.**

M3-CRETE is an experimental open-hardware reference design, not a consumer
product, hobby kit, finished machine, certified construction printer, or
structural concrete production system.

Read first:

- [Safety Notice](SAFETY_NOTICE.md)
- [Electrical Scope Boundary](ELECTRICAL_SCOPE_BOUNDARY.md)
- [Disclaimer](DISCLAIMER.md)

The public release is limited to mechanical design information, low-voltage
control-interface references, and software/firmware references where published.
It does not include AC mains wiring instructions, control-panel build
instructions, facility-connection instructions, safety-rated emergency-stop
circuit designs, 48 V high-current distribution design, or code-compliance
instructions.

**M³** = **M**obile · **M**odular · **M**eter³

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19647435.svg)](https://doi.org/10.5281/zenodo.19647435)

Developed by [Sunnyday Technologies](https://sunn3d.com).

| Spec | Value |
|------|-------|
| **Open BOM component target** | Under $5,000 for public mechanical/low-voltage reference components where current commodity pricing and substitutions allow; professional electrical/power-control scope is excluded |
| **Build footprint** | Sub-1 m³ — fits on a standard US pallet (48×40 in) |
| **Printhead weight** | ~1.5 kg |
| **License** | CERN-OHL-W-2.0 |

---

## Why M3-CRETE

Most concrete 3D printers are either proprietary industrial systems or one-off
research machines tied to specific institutions. M3-CRETE targets the space
between: an open mechanical and controls reference that qualified teams can
study, adapt, and validate within their own controlled research or development
programs.

### Target Applications

- Non-structural research specimens
- Process-development articles
- Digital formwork, molds, and fixtures
- Controlled materials and toolpath studies
- Laboratory and supervised institutional demonstrations
- Non-structural prototype objects where separately reviewed

Printed outputs require separate physical validation. No printed output from an
M3-CRETE-derived system may be used for structural, load-bearing, life-safety,
building-code, transportation, water-control, pressure-containing, occupied,
public-access, or permanent construction use unless separately designed, tested,
permitted, and approved by the responsible licensed professionals and
authorities for that specific project.

---

## Design Principles

### Mechanical Rigidity, Serviceability

The frame is engineered closer to CNC machine standards than desktop 3D
printers: rigid, durable, and precise. Mechanical components use standard
aluminum extrusions and commodity hardware where practical, so qualified teams
can inspect, replace, and modify parts without single-source dependency.

### Lower Moving Mass, Still Hazardous

With an efficient frame design, the drive system uses smaller motors than many
industrial concrete-printing systems while delivering sufficient torque for the
reference gantry. This does not make the machine safety-rated or safe for
unsupervised use. Moving axes, pinch/crush hazards, cementitious materials,
pressurized hoses, electrical systems, and software-controlled motion all
require qualified review, guarding, PPE, training, and operating procedures.

### No Thermal Management

Concrete cures by hydration — a chemical reaction — not by melting and cooling. This eliminates roughly 25% of the hardware cost and complexity associated with conventional FDM printers (heated beds, hot ends, cooling fans), resulting in a mechanically simpler, more energy-efficient, and more reliable machine.

### Designed for Research Iteration

Some non-structural components such as brackets, guides, and enclosure parts are
designed to be 3D-printable. Those printed parts still require inspection,
material selection, and project-specific validation before use in a working
machine.

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
│   └── index.html               # Interactive BOM viewer (bom.m3-crete.com/bom)
├── firmware/                    # Klipper configs (kinematics, steppers)
├── blog/                        # Build logs and project updates
└── config.js                    # Model variants (M3-1, M3-2, M3-4)
```

### AI-Assisted CAD Workflow

This project uses [CADCLAW](https://github.com/sunnyday-technologies/CADCLAW) — an automated validation framework for STEP assemblies developed during this project. The assembly script generates geometry, the self-check harness validates it (inventory, interference, adjacency, dimensions), and the kinematics module analyzes structural performance. This workflow caught 53 interferences and reduced the STEP file from 70 MB to 13 MB.

See the [CADCLAW repo](https://github.com/sunnyday-technologies/CADCLAW) for the generalized, reusable framework.

---

## Material Compatibility

M3-CRETE is a hardware reference, not a materials approval. It does not
prescribe a construction mix, validate printed outputs, or certify any
cementitious formulation for field use. Mixes, toolpaths, curing, durability,
and acceptance criteria require separate physical testing and professional
review for each use case.

For AI-driven mix-design decision support, see
[CEMFORGE](https://cemforge.ai/concrete-printers/) — a formulation engine
designed to generate candidate mixes and supported performance predictions where
sufficient validated data is available. Candidate mixes require physical
validation before any project use.

---

## Project Status

M3-CRETE is in active development. Current focus areas:

- Finalizing the open BOM and build documentation
- Validating open assembly notes and build sequence
- Establishing firmware profiles for concrete-specific extrusion parameters

Interested in contributing design feedback, supplier corrections, or controlled
build notes?
Open an issue or start a GitHub discussion.

---

## Disclaimer

M3-CRETE is provided as-is for experimental, educational, and development
purposes. Concrete/paste printing involves moving machinery, cementitious
materials, pressurized material handling, and electrical systems that pose real
safety risks. Users assume all responsibility for safe design, construction,
commissioning, guarding, training, inspection, and operation of any system built
from these files.

### Electrical / AC Mains Boundary

Any AC mains wiring, control-box integration, grounding, bonding, overcurrent
protection, disconnects, emergency-stop power circuits, facility connection,
inspection, or code compliance work must be performed by qualified personnel, a
licensed electrician where required, or a qualified control-panel shop.

The public M3-CRETE files may identify electrical interfaces, low-voltage
controls, and component references, but they are not AC mains wiring
instructions, control-panel build instructions, or a substitute for applicable
electrical codes, authority-having-jurisdiction review, or professional
electrical judgment.

See [SAFETY_NOTICE.md](SAFETY_NOTICE.md),
[ELECTRICAL_SCOPE_BOUNDARY.md](ELECTRICAL_SCOPE_BOUNDARY.md), and
[DISCLAIMER.md](DISCLAIMER.md) for full details.

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
| [Convergence Engineering whitepaper](https://doi.org/10.5281/zenodo.19863080) | Methodology paper that uses M3-CRETE as a public case study; introduces the *time to silence* metric. CC BY 4.0 preprint, Zenodo. |
| [Sunnyday Technologies](https://sunn3d.com) | Parent company — concrete 3D printing and engineered cementitious composites |
| [M3-CRETE Project Page](https://sunn3d.com/m3-crete/) | Hosted project overview and Sunnyday contact path |
| [CADCLAW](https://github.com/sunnyday-technologies/CADCLAW) | Automated STEP assembly validation — extracted from this project |
| [CEMFORGE™](https://cemforge.ai/concrete-printers/) | AI-powered concrete formulation platform by Sunnyday Technologies |
| [M3-CRETE Firmware](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE) | Firmware configurations for Klipper |

---

## Author

**Nicholas Sonnentag** ([ORCID 0009-0002-1897-384X](https://orcid.org/0009-0002-1897-384X)) — mechanical engineer, founder of [Sunnyday Technologies](https://sunn3d.com). M3-CRETE is designed and maintained by Nick; CAD iteration is LLM-assisted but the engineering judgment, component selection, build decisions, and direction are his.

- LinkedIn: [Nicholas Sonnentag](https://www.linkedin.com/in/nicholas-sonnentag)
- Email: `info@sunn3d.com`

## Citation

If you use M3-CRETE designs in research, a controlled build, or derivative
work, please cite:

```
Sonnentag, N. (2026). M3-CRETE: Open-Source Concrete 3D Printer.
Sunnyday Technologies.
https://doi.org/10.5281/zenodo.19647435
```

For the methodology paper that uses M3-CRETE as a public case study, cite:

```
Sonnentag, N. (2026). Convergence Engineering: Commissioning Autonomous
Software by Measuring the Rate at Which Novel Failures Trend Toward Zero.
Sunnyday Technologies. https://doi.org/10.5281/zenodo.19863080
```

A [`CITATION.cff`](CITATION.cff) file is included for automated citation tooling.

## Contributing

We welcome issues, pull requests, and design feedback from qualified teams. If
you are working with cementitious extrusion in a controlled technical setting,
your experience is valuable — open an issue or start a
[discussion](https://github.com/sunnyday-technologies/M3-CRETE/discussions).

**Contact:** info@sunn3d.com
