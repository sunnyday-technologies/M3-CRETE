# M3-CRETE Project Context

## Project Identity
- **Name:** M3-CRETE (Mobile, Modular, Meter³)
- **Type:** Open-source concrete 3D printer motion system
- **License:** CERN-OHL-W-2.0 (CAD/Components/ is CC BY-SA 4.0)
- **Repo:** `github.com/sunnyday-technologies/M3-CRETE`
- **Live site:** m3-crete.com (GitHub Pages)
- **BOM viewer:** m3-crete.com/bom (static JSON, client-side rendering)
- **Parent company:** Sunnyday Technologies, Appleton WI

## M3-2 Specifications (Default Build)
- **Build volume:** 2000 x 1000 x 1000mm
- **Frame (2026-04-14 update):** **4080 C-Beam** primary structure (Z-posts, Y-gantry rails) + 2040 bracing. **ALL 1000mm standard lengths** — shipping-constrained, single-SKU procurement. C opening points **inward** toward the printer cube (belt path runs inside the C). Supersedes the 2080/2040 + 1200mm plan from 2026-04-07.
- **X-axis:** 2x 1000mm 4080 spliced = 2000mm build envelope. Splice uses the **straight-line slot-linking kit** (internal T-slot connectors, sits below wheel path) **+ 3× 1m 2040 V-slot bars staggered inside the C-channel with structural adhesive** (center bar bridges 500mm each side of splice; existing 1m stock covers this — no 2m section needed; bom/data.json id 65). Corner joints use T-plate or L-plate 5-screw connectors at every 4080 junction. **NO external reinforcement on the X-gantry beam** — the X-carriage is 2-sided (V-wheels on top AND bottom of exterior), so any protrusion past the 40mm faces blocks carriage travel.
- **Y-axis:** 2x parallel 2080 rails, 1000mm span, dual motors (anti-racking)
- **Z-axis:** 4x independent belt-driven 2040 vertical posts (quad self-tramming via Klipper Z_TILT_ADJUST)
- **Gantry beam:** 2080 spanning Y, carried by dual-Y carriages
- **Motion:** GT2 10mm belt + polycarbonate V-wheels on all axes
- **Motors:** 7x NEMA23 8mm shaft (1X + 2Y + 4Z) + 1 extruder (NEMA34, owner-supplied)
- **Controller:** BTT Kraken (8x TMC5160 onboard) + Raspberry Pi 5 + Klipper
- **Printhead:** 1.5kg target, 1" Male NPT pipe connection, counter-weighted hose

## Model Variants
- **M3-1:** 1000x1000x1000mm (no splice, all single-piece extrusions)
- **M3-2:** 2000x1000x1000mm (default, X-axis spliced)
- **M3-4:** 2000x2000x1000mm (both X and Y spliced)
- Variants configured in `config.js` MODEL_VARIANTS with quantity overrides

## Key Files
| File | Purpose |
|------|---------|
| `bom/data.json` | **BOM source of truth** — 66 parts, 216 supplier options, 37 suppliers |
| `bom/index.html` | BOM viewer (static, loads data.json, multi-supplier selection) |
| `config.js` | Model variants, category order, project metadata |
| `CAD/Components/` | OpenBuilds STEP parts library (70 files, CC BY-SA 4.0) |
| `CAD/Advanced/` | Extended/compatible parts (76 files) |
| `CAD/m3_2_assembly.py` | CadQuery assembly script (generates M3-2_Assembly.step) |
| `migration-005-supplier-coverage.sql` | Historical — data now in data.json |
| `supabase-schema.sql` | Historical — Supabase removed, kept as reference |

## CadQuery Environment
- **Venv:** `cad_venv/` (gitignored, Python 3.11 + CadQuery 2.7.0)
- **Assembly output:** `CAD/M3-2_Assembly.step` (101 components, ~6 MB)
- **Probe script:** `CAD/probe_steps.py` (bounding box inspector for STEP files)
- **Self-check harness:** `CAD/self_check.py` (interference / layout audit — run before and after any model changes)

## BOM Viewer Features (shipped 2026-03-31)
- Multi-supplier selection (click chips to toggle suppliers on/off)
- Coverage tracking with progress bar (green/amber/red)
- Per-part auto-supplier assignment when chip clicked
- Quantity adjusters (+/- per part)
- "I have this" exclusion checkboxes
- Buy/Print/CNC toggle on fabricated parts
- CSV + JSON export with supplier filter
- "Suggest Supplier" opens GitHub Issue
- Model variant selector (M3-1 / M3-2 / M3-4)
- CAD Library panel linking STEP files

## Mechanical Audit Findings (2026-03-31)
### Resolved
- Universal gantry plate works on 2040 AND 2080 (verified)
- Smooth idler pulleys (14x) added to BOM
- Idler pulley mounting plates added to BOM (was a build-blocker)

### Open Items
- Z carriage vs cross brace clearance — needs CAD verification
- Belt tensioning method — motor mount slotted holes, document in assembly guide
- Drag chain end brackets — verify included with chain or add to BOM
- Splice gap — verify internal connectors are flush so V-wheels ride smoothly

## Supplier Strategy
- **No US manufacturer makes V-slot** — all imported from China
- **Bonnell Aluminum / TSLOTS** (Niles, MI — 3hrs from Appleton) makes T-slot. Custom V-groove die possible (~$1,500 tooling)
- **MakerStore USA** (Atoka, OK) — US warehouse, full V-slot ecosystem, domestic shipping
- **Bulkman3D** — China factory-direct, best bulk pricing, bad shipping costs
- **Amazon** — electronics, wiring, fasteners (sourcing channel for the SKUs Amazon does well)

## Product Decisions
- **Pump system is OUT OF SCOPE** — M3-CRETE focuses on the motion system; the printhead connects to any commercial or community pump capable of feeding a 1" Male NPT line at the required pressure.
- Commercial pump references kept as informational in BOM (MAI, M-Tec, StoneFlower)
- Frame stiffener for 2m+ spans: aluminum rectangular tube recommended (not steel — galvanic corrosion)
- Extruder/pump motor: NEMA34 recommended (owner-supplied; not in the kit)

## Out of Scope for This Build
- No HEPA filter, carbon fiber bars, or LED lights on this build
- Custom plates: source from Bulkman3D or Maker Store
- BOM viewer: static JSON architecture (no third-party backend)
- V-Slot ecosystem: community-maintained as of May 2025 (CC BY-SA 4.0)

## Git Hygiene
- **Never push without Nick's explicit approval**
- `.gitignore` covers: `.Codex/`, `conversation-summary.md`, `cad_venv/`, `NEMA_CRETE/`
- The temp clone at `D:\m3crete_fix\` should be deleted once CadQuery venv is moved
- Commit messages use `Co-Authored-By: Codex Opus 4.6 (1M context) <noreply@anthropic.com>`

## CAD Assembly Status (2026-04-07) — v0.2.0, 101 parts ⚠️ SUPERSEDED

> ⚠️ **Historical only. Current strategy is in the "2026-04-14" section below.**
> April 7 used 2040/2080 V-slot at 1200mm. April 14 switched to 4080 C-beam at 1000mm due to shipping constraints, and corner joints moved to T/L-plate 5-screw connectors.

### Extrusion Strategy (updated 2026-04-07)
- **ALL standard 1200mm lengths** — no 1000mm, no custom cuts
- **Stacked/layered corners** — full-length rails alongside posts for max rigidity
- **Single SKU per profile** — simplifies procurement and kit packaging
- **2040 x 1200mm: 9 needed** (4 posts + 3 top braces + 2 bottom braces)
- **2080 x 1200mm: 8 needed** (4 top X-rails + 2 Y-rails + 2 gantry beam)

### Plate Strategy (updated 2026-04-07)
- **Z-carriage: 8 plates** (sandwich pairs, 2 per corner)
- **Y-gantry: 2 plates** (ride Y-rails, carry gantry beam ends)
- **X-carriage: 2 plates** (sandwich gantry beam for printhead)
- **1mm running gap** between Z-carriage and Y-gantry plates
- **Total: 12 gantry plates** (all V-Slot Gantry Plate 20-80mm)

### Assembly Components
| Component | Qty | Notes |
|-----------|-----|-------|
| 2040 posts | 4 | Full height 1200mm, rz=90 (40mm X face) |
| 2080 top X-rails | 4 | 2 front + 2 rear, spliced at X=1200 |
| 2040 top Y-braces | 3 | Left, center (splice), right |
| 2040 bottom Y-braces | 2 | Left + right only (open front/back) |
| 2080 Z-platform Y-rails | 2 | Left + right, carry gantry |
| 2080 gantry beam | 2 | Spliced at center, full X span |
| Gantry plates | 12 | 8 Z-carriage + 2 Y-gantry + 2 X-carriage |
| V-wheels | 32 | 16 Z + 8 Y + 8 X |
| Eccentric spacers | 32 | 1 per wheel |
| NEMA23 motors | 7 | 4 Z + 2 Y + 1 X |
| Motor mount plates | 4 | Z-axis only |
| GT2 pulleys 20T | 3 | Y + X motors (Z uses hub disks) |
| Hub disks | 4 | Z-axis, belt wraps over top brace |
| Smooth idler pulleys | 8 | 4 Z-bottom + 2 Y-front + 2 X-ends |
| Idler plates | 4 | Z-axis bottom mounts |
| Cube connectors | 4 | X-rail splice joints |
| GT2 belts | 7 | 4 Z + 2 Y + 1 X (lime green) |
| Drag chains | 3 | X + Y + Z cable management |

### Z-Motor Configuration
- Motors STRADDLE top Y-brace (body above, shaft down)
- Hub disk below brace routes belt over brace and down to carriage
- Belt path: hub disk -> down post -> bottom idler -> up to carriage

### Next Steps
- Fine-tune plate/rail alignment in Fusion (1mm running gaps)
- Verify no volume intersections
- BOM cross-reference final audit

## Design Exclusions

Explicit non-requirements for M3-CRETE. Documented to keep design
discussions focused on the in-scope motion system.

### ❌ NO mechanical limit switches / endstops

The system uses **StallGuard4 sensorless homing via the TMC5160 drivers
on the BTT Kraken mainboard**. Every stepper axis (X, Y×2, Z×4) homes
by detecting motor back-EMF when the carriage stalls against a hard
stop — no contact switches needed on the machine.

- Driver: TMC5160 (8× onboard on BTT Kraken). Datasheet confirms
  StallGuard on SPI + single-wire diag output.
- Stepper spec: NEMA23 **8mm shaft** is REQUIRED for StallGuard
  torque/inductance compatibility — see bom/data.json id 9 description.
- Prior rationale captured in docs/session-2026-04-13-bom-audit.md
  (section: "No Endstops Confirmed").
- Migration history: `migration-001-wiring-overhaul.sql` removed
  endstop switches from the BOM when the design migrated to StallGuard.

**Any file or part entry still referencing limit switches / endstops
on the machine itself is a stale leftover. Delete or reword, do not
"add it back".** The only "endstops" in the current BOM are DIN-rail
end-stop clamps (the plastic clips that hold terminal blocks against
the DIN rail) — those are electrical panel hardware, not motion control.

### ❌ NO leveling feet (2026-04-21 decision)

Bed leveling is handled via measurement (probe / manual) on the build
plate, not mechanical M16 feet on the frame. Removed from the SN 001
buy list. If the frame needs to sit on something, printed or CNC'd
base plates (local fabrication) carry that.

### ❌ NO external reinforcement on X-gantry beam (2026-04-22 decision)

The X-carriage is 2-sided — V-wheels ride on BOTH top and bottom of
the gantry beam exterior. Any external hardware (L-brackets, gussets,
plates) on the 40mm top/bottom faces of the 4080 C-beam protrudes
into the wheel path and blocks carriage travel. All reinforcement
must be INTERNAL (inside the C-channel) or BELOW the wheel-contact
zone (where the slot-linking kit fits).

Primary reinforcement: **3× 1m 2040 V-slot bars staggered inside
the 4080 C-channel, bonded with structural adhesive** (bom/data.json
id 65). Center bar bridges 500mm each side of the splice; left and
right bars fill the remaining sections. No 2m section needed —
existing 1m stock (Maker Store LR-2040-B-1000, 3 allocated for
SN 001) covers this.

### ❌ NO 5-hole 90° joining plate for X-axis splice (2026-04-22 decision)

Superseded by the **straight-line slot-linking kit** (id 5 —
Straight Line Internal Connectors, 20-Series) PLUS the internal
2040 reinforcement above. The slot-linking kit fits inside the
T-slot channels and sits below the wheel path → no exterior
protrusion. External 5-hole plates were redundant AND would have
interfered with the X-carriage wheel zone on the gantry beam.

Frame top members (non-gantry 2m spans, 2 pieces) can optionally
add a **6mm aluminum plate underneath at the splice** (bom/data.json
id 82) for extra rigidity — cheaper than internal bonded
reinforcement, and external is fine on these members because no
carriage rides past them.

### ❌ NO HEPA filter, carbon fiber bars, or LED lights
### ✅ Static JSON architecture (no third-party backend; see m3-crete.com/bom)
### ✅ Custom plates: source from Bulkman3D or Maker Store
### ✅ V-Slot ecosystem: community-maintained as of May 2025 (CC BY-SA 4.0)

## NEMA23 Motor Mount Fastening (2026-04-21 clarification)

Nick's NEMA23 motors have **PASS-THROUGH mounting holes, not tapped**.
The motor body does NOT accept bolts directly — bolts pass through the
motor body AND through the 3D-printed mount plate, and require M5 nuts
on the back side to secure.

Per-motor hardware: 4× M5 cap screws + 4× M5 nuts (nylock or plain +
blue Loctite). For the 7 NEMA23 motors on SN 001: 28 of each.

Material: EEEEE 880pc Amazon kit covers M5 nuts. Loctite Blue 243
(~$8/bottle) handles the thread-locking. No heat-set inserts needed —
the plastic mount is a CLEARANCE plate, not a threaded anchor.

## CAD Assembly Status (2026-04-14) — v0.3 IN PROGRESS

**✅ Model state (2026-04-22):** Verified current. Splice + reinforcement strategy finalized — slot-linking kit + 3× 1m 2040 bars staggered inside X-gantry C-channel (center bar bridges splice 500mm each side, existing stock covers); 6mm plate optional backup for non-gantry frame splices. No CAD edits pending for this design change.

### Extrusion Strategy (supersedes 2026-04-07)
- **ALL 1000mm standard lengths** (not 1200mm) — driven by shipping constraints; single SKU per profile
- **Primary structure: 4080 C-Beam** replaces 2040/2080 V-slot for Z-posts and Y-gantry rails
- C opening points **inward** toward the printer cube (belt path inside the C)
- C-beam endcaps removed (not realistic); profile rotated 180° so the opening faces the interior
- **11 segments per kit + 1 spare = 12 ordered** per build
- Source STEP: `CAD/Advanced/Linear Rail/C-Beam 40x80x1000 Linear Rail.step`

### Corner Joint Strategy
- **T-plate OR L-plate, 5 screws per corner** at every 4080-to-4080 junction
- The "flat plates" currently in the model are placeholders — replace with real supplier parts
- Supplier sourcing pending — Makerstore USA / Bulkman3D are the expected vendors

### Assembly Refinements (2026-04-14)
- **4mm shims** on Y-direction only (static frame side) — allow Y-gantry travel along Z-posts with proper 1mm running clearance and plate stackup
- No shims in X-direction (2m axis) — Y-gantry shifts outward on Z-axis gantry plate carriage instead
- Rail orientation: bottom Y rail flat-on-top, top Y rail flat-on-top (avoid debris traps; bottom channel may host 2020 leg extensions)
- Tall C channel **always inward** (except up/down axis → down)

### Components to Add to BOM + Model
- Corner connector plates: **27** (T-plate/L-plate, 5-screw)
- Y-motor brackets: **2** (flat NEMA23 mount — cheaper than L-bracket)
- Idler axle brackets: **5**
- X-axis: dual plate sandwich, not yet modeled

### Open Items (2026-04-14)
- **Fix broken model** — run interference check with/without plates to identify clipping
- **Update BOM `data.json`** — quantities reflect old 1200mm/2080 era, needs full sweep for 4080 + 1000mm + corner bracket additions
- **Self-check harness** — reinstate before making further model changes (explicitly cited as "the best progression we had in past sessions")
- **Git history** — Nick decided NOT to rewrite (leave legacy .step blobs in history despite ~100MB bloat)

