# M3-CRETE — Open-Source Concrete 3D Printer

**A large-format gantry printer for cementitious extrusion at construction scale.**

M3-CRETE is an open-source hardware project for building a concrete 3D printer from standard, commercially available components. The system is purpose-built for layer-by-layer extrusion of cementitious materials — no heated beds, no proprietary toolchains, no vendor lock-in.

**M³** = **M**obile · **M**odular · **M**eter³

Developed by [Sunnyday Technologies](https://sunn3d.com).

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

The system is designed so that printed structural components can be produced on an existing M3-CRETE unit. A working printer helps produce parts for the next one. Scalability is a feature, not an afterthought.

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

> This project is under active development. Contents will expand as the design is finalized for the first build-it-yourself kit release.

```
M3-CRETE/
├── README.md
├── DISCLAIMER.md
├── LICENSES/            # CERN-OHL-W-2.0 license files
├── docs/
│   └── bom/             # Bill of materials
├── .gitignore
```

Planned additions: CAD files, printed part STLs, assembly documentation, wiring diagrams, and reference images.

---

## Material Compatibility

M3-CRETE is a hardware platform — it does not prescribe a specific concrete mix. The system is designed to work with a range of cementitious formulations optimized for layered extrusion, including OPC, LC3, and specialty blends.

For AI-driven mix design optimized for 3D printing, see [CEMFORGE™](https://cemforge.ai/concrete-printers/) — a formulation engine that uses physics-based models and an 8,000+ formulation dataset to generate printable concrete mixes with target performance characteristics.

---

## Project Status

M3-CRETE is in active development. Current focus areas:

- Finalizing the build-it-yourself kit BOM and documentation
- Preparing for the first production run
- Establishing firmware profiles for concrete-specific extrusion parameters

Interested in early access, collaboration, or providing field feedback?
See the **[project page →](https://sunn3d.com/2025/12/31/concrete-printer/)**

---

## Disclaimer

M3-CRETE is provided as-is for educational and development purposes. Concrete 3D printing involves heavy machinery, cementitious materials, and electrical systems that pose safety risks. Users assume all responsibility for safe design, construction, and operation of any system built from these files. Sunnyday Technologies makes no warranties regarding fitness for any particular purpose and assumes no liability for injury, damage, or loss resulting from the use of these designs. Consult applicable local building codes, electrical codes, and safety regulations before construction or operation.

See [DISCLAIMER.md](DISCLAIMER.md) for full details.

---

## License

This project is licensed under the **CERN Open Hardware Licence Version 2 — Weakly Reciprocal** ([CERN-OHL-W-2.0](https://ohwr.org/cern_ohl_w_v2.txt)).

You may use, modify, and distribute this design under the terms of that license. Modifications to covered files must be made available under the same license. This project includes no warranty of any kind.

See [LICENSES/](LICENSES/) for full license text.

---

## Related Projects and Resources

| Resource | Description |
|----------|-------------|
| [Sunnyday Technologies](https://sunn3d.com) | Parent company — concrete 3D printing and engineered cementitious composites |
| [M3-CRETE Project Page](https://sunn3d.com/2025/12/31/concrete-printer/) | Kit details, design philosophy, and contact for early access |
| [CEMFORGE™](https://cemforge.ai/concrete-printers/) | AI-powered concrete formulation platform by Sunnyday Technologies |
| [M3-CRETE Firmware](https://github.com/sunnyday-technologies/M3-CRETE-FIRMWARE) | Firmware configurations for Marlin/Klipper |

---

## Contributing

We welcome issues, pull requests, and design feedback. If you're building a concrete printer or working with cementitious extrusion, your field experience is valuable — open an issue or start a [discussion](https://github.com/sunnyday-technologies/M3-CRETE/discussions).

**Contact:** info@sunn3d.com
**LinkedIn:** [Nicholas Sonnentag](https://www.linkedin.com/in/nicholas-sonnentag)
