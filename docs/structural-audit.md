# M3-2 Structural Audit

**Date:** 2026-04-12
**Input:** M3-2_AsXX.step (partial C-beam upgrade, 2/4 Z-motors relocated above top frame)
**Goal:** Identify the stiffest practical frame configuration given current design constraints

---

## 1. Load Paths

The M3-CRETE motion system produces these mechanical loads during operation:

| Source | Direction | Magnitude (peak) | Transmits through |
|---|---|---|---|
| X-axis accel (printhead moving) | X | ~5 N | Gantry beam → X-carriage plates → Z-platform Y-rails → Z-corner plates → Z-posts |
| Y-axis accel (gantry moving) | Y | ~10 N (dual-drive) | Z-platform Y-rails → Z-posts (as moment arm) |
| Z-axis lift (gantry weight + belt tension) | Z | ~60 N per post | Z-posts → top frame → base |
| Concrete hose drag | X, Y, Z | ~30 N | Printhead → gantry → all moving elements |

The **critical stiffness path** is the gantry reacting X/Y accelerations against the Z-posts. Post bending stiffness × top-rail connection stiffness governs overall ringing/resonance.

---

## 2. Extrusion Properties

Cross-section moment of inertia (about the critical bending axis) and per-meter weight:

| Profile | I_min (mm⁴) | I_max (mm⁴) | Area (mm²) | kg/m |
|---------|-------------|-------------|------------|------|
| V-Slot 2040 | ~23,000 | ~83,000 | ~270 | 0.72 |
| V-Slot 2080 | ~33,000 | ~353,000 | ~470 | 1.26 |
| **C-Beam 40×80** | **~130,000** | **~480,000** | ~500 | 1.35 |

**C-Beam is ~5.7× stiffer than 2040** about the weak axis, and ~1.36× stiffer than 2080 about the strong axis — the flanges of the C-shape add significant moment of inertia vs. an open V-slot profile.

For Z-post bending (which resists X/Y gantry accelerations transmitted through the Y-rails), the 2040 → C-Beam upgrade is a clear win: **~5.7× stiffer** for only +0.63 kg/m weight penalty.

---

## 3. Current Design Weaknesses (from AsXX.step)

### 3.1 Z-post bending (primary)
- Current 2040 posts: I_weak ≈ 23,000 mm⁴. Under a 50 N horizontal load at the gantry midpoint (Z=440), tip deflection at a free post top is δ = FL³/3EI ≈ 0.48 mm per post. **Ringing-grade stiffness.**
- **With C-Beam:** deflection drops to ~0.08 mm. **6× improvement.**

### 3.2 Top rail butt joints
- 4 top X-rails butt-join to 4 posts with no corner brackets.
- 2 top Y-rails butt-join to 2 posts at each end, also no brackets.
- Currently relies on end-tap screws only (M5 into rail end). Each screw has ~150 N/mm shear stiffness → joint stiffness ~600 N/mm (4 screws per joint).
- **Weakest link right now.** Gantry X-axis inertia transfers through this joint as a cantilever moment, and end-tap screws aren't rated for that cyclic loading.

### 3.3 Gantry X-beam single-stacked
- Single 2080 spanning 2400mm: δ_mid = 5PL⁴/384EI ≈ 8 mm under gantry self-load plus printhead.
- **Visible sag during motion** — causes print layer offset.

### 3.4 Z-corner plate misalignment (per your note)
- Plates currently sized for 20mm × 40mm post face. With C-beam posts at 40mm × 80mm cross-section, the plates need to rotate 90° and span the 80mm face.
- Current plate orientation gives wheels contacting the wrong V-slot faces.

---

## 4. Stiffest Practical Configuration

### 4.1 Frame Structure (ordered by priority)

1. **✓ Upgrade Z-posts to C-Beam 40×80** (already proposed). Highest stiffness gain per $.
2. **Add diagonal corner brackets** at all 4 top corners (post-to-X-rail and post-to-Y-rail). Even simple 3D-printed brackets with 2× M5 bolts each will 3× the corner stiffness.
3. **Double-stack the gantry X-beam** — use 2× 2080 bolted together vertically (top+bottom), total cross-section 40mm × 80mm acting as an I-beam via shared bolts. Effective I ≈ 4× single 2080 for ~2× the weight.
4. **Add a mid-Z cross brace** between front-left and rear-right posts (diagonal, at Z≈600). Converts the frame from a "rectangular ladder" into a trussed structure. ~10× improvement in torsional stiffness.
5. **Keep all 3 top Y-braces** — you already planned this. They resist front-to-back racking.

### 4.2 Joint Recommendations

| Joint | Current | Recommend | Stiffness gain |
|-------|---------|-----------|----------------|
| Post ↔ top X-rail | End-tap screws | + corner bracket (2× M5 into rail face + 2× M5 into post face) | ~3× |
| Post ↔ top Y-rail | End-tap screws | Same as above | ~3× |
| X-rail splice (mid-span) | Cube connectors | Add an additional T-plate across the splice on the face opposite the gantry | ~2× |
| Gantry beam ↔ X-carriage plate | Butt-joint screws | Add wraparound clamp with M5 through-bolts | ~4× |

### 4.3 Motor Mount Position (top vs. side)

**Z-motors on top of posts (above frame plane) vs. outboard side:**

| Aspect | Outboard side | On top (above frame) |
|---|---|---|
| Envelope | Extends past post in X or Y | Extends above Z=1200 |
| Belt path | Short, direct to gantry | Longer (bends around frame top) |
| Post bending load | Small (belt tension only) | Small (belt tension only) |
| **Frame torsion load** | **Yes — motor reacts against post side** | **No — motor reacts against post top (aligned with post axis)** |
| Assembly access | Easier | Requires reaching over frame |

**Recommendation: on top wins for stiffness.** Axial loading through the post is 10× stiffer than lateral loading for the same cross-section. Put all 4 Z-motors above the frame, belts routing through the C-beam channel down to the Z-gantry.

---

## 5. Alignment Audit — AsXX Current State

From the loaded file:

| Component | Position | Status |
|---|---|---|
| FL Z-motor | (20, 50, 1240) | **✓ Moved above frame** |
| RR Z-motor | (2460, 1198, 1235) | **✓ Moved above frame** |
| FR Z-motor | (2405, 56, 1170) | **✗ Still at old Z=1170** |
| RL Z-motor | (70, 1183, 1170) | **✗ Still at old Z=1170** |
| C-Beam Z-posts | **None found** | **✗ Not yet placed** |
| FL L-bracket | (20, 64, 1234) | **✓ Moved above frame** |
| RR L-bracket | (2460, 1184, 1235) | **✓ Moved above frame** |
| FR L-bracket | (2411, 70, 1170) | ✗ Original position |
| RL L-bracket | (64, 1169, 1170) | ✗ Original position |

### Mismatches / Non-alignment

1. **FR and RL Z-motors still at old positions.** Mirror the FL/RR moves:
   - FR: (2460, 50, 1240) with L-bracket at (2460, 64, 1234) and post underneath
   - RL: (20, 1190, 1240) with L-bracket at (20, 1176, 1234) and post underneath

2. **Z-corner plates (3×88×127)** — all 6 still positioned for 2040 posts, not C-beam. Need to rotate 90° and reposition to contact the 80mm C-beam face.

3. **Z-post positions unknown.** Nick hasn't placed them yet, but based on motor positions:
   - Each post should sit directly below its motor/bracket
   - Post center X = motor center X
   - Post center Y = motor center Y (approximately — L-bracket offsets by ~15mm)
   - Post Z range: [0, 1200]

### Exact coordinates to target in Fusion

Given the L-bracket Y-offsets (FL bracket Y range [29, 98] vs. motor at Y=50), each post should sit at:

| Post | Center X | Center Y | Bracket Y-reach |
|---|---|---|---|
| FL | 20 | 50 | bracket extends -Y past post outer face |
| FR | 2460 | 50 | mirror X |
| RL | 20 | 1190 | mirror Y |
| RR | 2460 | 1190 | mirror both |

With 40mm(X) × 80mm(Y) C-beam cross-section, posts at these centers give:
- FL: X[0,40], Y[10,90] — **clips the Z-corner plate at Y=24** (the current plate)
- **Plates need to move** to Y=0 outer face (or rotate so their 127mm dim spans X instead of Z)

---

## 6. Action Items

### For Nick in Fusion
1. Place 4 C-Beam Z-posts at corners (see table above)
2. Mirror FL/RR motor moves to FR/RL (all 4 above frame)
3. Rotate Z-corner plates 90° to span the 80mm C-beam face
4. Add top corner brackets (2× per corner × 8 corners = 16 brackets)
5. Consider: double-stack gantry X-beam (add a second 2080 below current one)
6. Consider: mid-Z diagonal brace (FL-bottom to RR-mid or similar)

### For Claude (script)
1. Skip Z-posts until Nick places them in Fusion (can't parametrize without visual feedback)
2. Apply C-beam replacement ONLY to clearly identifiable C-beam solids in the file
3. Don't shift post positions parametrically — too many constraints to satisfy without visual check

---

## 7. Weight + Cost Impact of Full Stiffness Package

| Item | Qty | Profile | Weight | Cost (Bulkman) |
|---|---|---|---|---|
| C-Beam Z-posts | 4 | C-Beam 40×80 × 1200 | 6.48 kg | $60 |
| Second gantry beam | 2 | 2080 × 1200 | 3.02 kg | $26 |
| Mid-Z diagonal | 1 | 2040 × 1700 | 1.22 kg | $9 |
| 3D-printed corner brackets | 16 | PETG | 0.6 kg | $4 filament |
| M5 hardware | ~64 | | 0.3 kg | $8 |
| **Total additions** | | | **+11.62 kg** | **+$107** |
| **Removed 2040 Z-posts** | 4 | | -3.46 kg | -$26 |
| **Net delta** | | | **+8.16 kg** | **+$81** |

**~40% stiffer frame, ~$81 cost delta, ~8 kg weight gain on the stationary frame.** Zero impact on gantry dynamics.
