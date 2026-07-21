# M3-CRETE Electrical Content Inventory

Date: 2026-07-03

> **Status update 2026-07-21.** The three `docs/electrical/**` documents listed
> below as "allowed after remediation" were **withdrawn rather than published** —
> see `risk_register.md`. `ELECTRICAL_SCOPE_BOUNDARY.md` on `main` is now the
> only public electrical-scope document. The `bom/index.html` row below was
> missed in the first pass and was corrected on 2026-07-21.

This inventory separates public low-voltage reference content from high-risk
power/control content that must not be published as implementation guidance.

## High-risk public content to remove or supersede

| Path | Content class | Action |
| --- | --- | --- |
| `control-panel/tool.html` | Interactive default control-panel layout and netlist with AC, PE, contactor, breaker, E-stop terminal, 48 V, and PSU elements. | Replace with supersession notice. |
| `control-panel/index.html` | Public landing page embedding the planner. | Replace with electrical-scope boundary notice. |
| `blog/control-panel-layout-tool/index.html` | Public announcement and screenshot of planner. | Replace CTA with supersession note and safety links. |
| `images/control-panel-tool.png` | Prototype/planner image showing a control-panel layout. | Do not promote as current public guidance; caption or remove from public entry points. |
| `sitemap.xml` | Public indexing of control-panel route. | Remove route from sitemap after notice replacement unless owner intentionally wants the notice indexed. |

## Public electrical content allowed after remediation

| Path | Intended role |
| --- | --- |
| `ELECTRICAL_SCOPE_BOUNDARY.md` | Root public scope boundary. |
| `docs/electrical/24v_low_voltage_interface.md` | 24 VDC-only interface boundary with reviewer placeholders. |
| `docs/electrical/controller_enclosure_outline.md` | Mechanical/low-voltage enclosure constraints without wiring instructions. |
| `docs/electrical/professional_power_control_scope.md` | Public-safe explanation of professional panel-shop scope. |

## BOM items requiring public-scope treatment

| Path | Item | Treatment |
| --- | --- | --- |
| `bom/data.json` | External stepper driver, 48 V high-current use. | Mark professional/private scope and not public wiring guidance. |
| `bom/data.json` | 48 V power supply for pump driver. | Mark professional/private scope and exclude from public build instruction. |
| `bom/index.html` | BOM disclaimer and fallback examples. | Make clear that public BOM excludes mains, high-current distribution, control-panel construction, and safety-rated circuits. |

## Review requirement

Electrical/control-panel review is required for any public text that defines
low-voltage connector values, current limits, fuse/current-limiting behavior,
operator interface boundaries, motor-driver enclosure constraints, or
professional power/control scope.
