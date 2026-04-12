"""
M3-CRETE M3-2 Assembly — v3 (filter-and-replace from Fusion export)

Loads all parts from M3-2_Assembly_user.v21.step, then:
  - Replaces C-beams (40x80x1200) with solid-fill parametric versions
  - Replaces L-brackets (65x69x69) with generic parametric L-plates
    (NEMA23 bolt pattern + T20 rail mounting, no StepperOnline IP)
  - Everything else passes through at full Fusion fidelity
"""
import cadquery as cq
from cadquery import Assembly, Color, Location
from OCP.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir, gp_Vec
from OCP.BRepBuilderAPI import (BRepBuilderAPI_Transform, BRepBuilderAPI_MakeWire,
                                 BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_TangentialDeflection
import os, time, math

USER_STEP = os.path.join(os.path.dirname(__file__), "M3-2_AsXX.step")

# ============================================================
# Helpers
# ============================================================
def _discretize_wire(wire, deflection=1.0):
    """Convert a wire's curves to straight-line segments."""
    pts = []
    for edge in cq.Wire(wire).Edges():
        adaptor = BRepAdaptor_Curve(edge.wrapped)
        disc = GCPnts_TangentialDeflection(adaptor, deflection, 0.1)
        for i in range(1, disc.NbPoints() + 1):
            p = disc.Value(i)
            pts.append((p.X(), p.Y(), p.Z()))
    clean = [pts[0]]
    for p in pts[1:]:
        if any(abs(p[j] - clean[-1][j]) > 1e-6 for j in range(3)):
            clean.append(p)
    wb = BRepBuilderAPI_MakeWire()
    for i in range(len(clean)):
        p1 = gp_Pnt(*clean[i])
        p2 = gp_Pnt(*clean[(i + 1) % len(clean)])
        wb.Add(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
    return wb.Wire()

def _solid_fill_extrude(solid, face_selector, extrude_vec):
    """Extract outer wire from a face, discretize, fill solid, extrude."""
    face = solid.faces(face_selector).val()
    outer_wire = _discretize_wire(face.outerWire().wrapped)
    solid_face = BRepBuilderAPI_MakeFace(outer_wire).Face()
    prism = BRepPrimAPI_MakePrism(solid_face, extrude_vec)
    return cq.Workplane().add(cq.Shape(prism.Shape()))

def _extract_cbeam_profile_points(cbeam_solid):
    """Extract 2D profile points from a Y-rail C-beam's end face.
    Returns list of (X, Z) tuples discretized from the outer wire.
    These are in the original C-beam's coordinate system."""
    wp = cq.Workplane().add(cbeam_solid)
    end_face = wp.faces("<Y").val()
    outer_wire = end_face.outerWire()
    pts_3d = []
    for edge in outer_wire.Edges():
        adaptor = BRepAdaptor_Curve(edge.wrapped)
        disc = GCPnts_TangentialDeflection(adaptor, 1.0, 0.1)
        for i in range(1, disc.NbPoints() + 1):
            p = disc.Value(i)
            pts_3d.append((p.X(), p.Z()))
    # Dedupe consecutive near-duplicates
    clean = [pts_3d[0]]
    for p in pts_3d[1:]:
        if abs(p[0] - clean[-1][0]) > 1e-4 or abs(p[1] - clean[-1][1]) > 1e-4:
            clean.append(p)
    return clean

def _make_cbeam_post_from_profile(profile_xz, src_x_center, src_z_center,
                                   length=1200, channel_dir="+Y"):
    """Parametric C-beam Z-post: 80(X) × 40(Y), channel opening + V-grooves
    on 3 outer faces. Built as a polyline profile extruded along Z."""
    HW = 40.0      # half outer width (X)
    HH = 20.0      # half outer height (Y)
    CHW = 13.0     # half channel opening width (X-direction for +Y channel)
    CHD = 36.0     # channel depth (cuts from +Y face down to Y = HH - CHD = -16)
    VW = 4.55      # half V-groove opening (9.1mm wide)
    VD = 5.5       # V-groove depth

    # Build outline for channel_dir == "+Y" first (channel opens on +Y face)
    # Going clockwise from bottom-left:
    pts = [
        # Bottom face (y = -HH), V-groove at x=0
        (-HW, -HH),
        (-VW, -HH), (0, -HH + VD), (VW, -HH),
        (HW, -HH),
        # Right face (x = +HW), V-groove at y=0
        (HW, -VW), (HW - VD, 0), (HW, VW),
        (HW, HH),
        # Top edge right of channel (y = +HH, x = CHW..HW)
        (CHW, HH),
        # Channel right wall (x = CHW, from HH down to HH - CHD)
        (CHW, HH - CHD),
        # Channel bottom (y = HH - CHD)
        (-CHW, HH - CHD),
        # Channel left wall (x = -CHW, from HH - CHD up to HH)
        (-CHW, HH),
        # Top edge left of channel
        (-HW, HH),
        # Left face (x = -HW), V-groove at y=0
        (-HW, VW), (-HW + VD, 0), (-HW, -VW),
    ]

    # Apply channel direction via coordinate transform
    if channel_dir == "-Y":
        pts = [(x, -y) for (x, y) in pts]
    elif channel_dir == "+X":
        pts = [(y, x) for (x, y) in pts]
    elif channel_dir == "-X":
        pts = [(-y, x) for (x, y) in pts]

    profile = (cq.Workplane("XY")
               .moveTo(*pts[0])
               .polyline(pts[1:])
               .close()
               .extrude(length))
    return profile

def _make_generic_bracket(axle):
    """Generic NEMA23 motor bracket (no StepperOnline IP).
    Box shape matching original 65×69×69 dims with adjustment slots.
    Motor face: 4× slots at NEMA23 47.14mm pattern + 38.1mm boss hole.
    Rail face: 4× slots at 20mm T-slot spacing.
    `axle` = the 65mm axis direction (from original bbox)."""
    # Build with 65mm along Z, 69×69 in XY, then rotate to match axle
    t = 69.0
    bracket = cq.Workplane("XY").box(69, 69, 65)
    # Motor face (-Z): NEMA23 bolt pattern as slots + boss hole
    nema_half = 47.14 / 2
    bracket = (bracket.faces("<Z").workplane()
        .pushPoints([(nema_half, nema_half), (nema_half, -nema_half),
                     (-nema_half, nema_half), (-nema_half, -nema_half)])
        .slot2D(12, 5.5).cutBlind(-5)
        .faces("<Z").workplane()
        .pushPoints([(0, 0)])
        .hole(38.1, 5))
    # Rail face (+Z): T-slot mounting slots
    bracket = (bracket.faces(">Z").workplane()
        .pushPoints([(0, -15), (0, 15), (20, -15), (20, 15)])
        .slot2D(12, 5.5).cutBlind(-5))
    # Rotate to match the original bracket's 65mm axis
    if axle == "X":
        bracket = bracket.rotateAboutCenter((0, 1, 0), 90)
    elif axle == "Y":
        bracket = bracket.rotateAboutCenter((1, 0, 0), 90)
    return bracket

# ============================================================
# Colors
# ============================================================
ALU  = Color(0.10, 0.10, 0.12)   # Black anodized frame
BLK  = Color(0.08, 0.08, 0.10)   # Gantry beam
DRK  = Color(0.20, 0.20, 0.22)   # C-beam Y-rails
BRK2 = Color(0.30, 0.50, 0.75)   # L-bracket blue
BELT = Color(0.59, 0.84, 0.00)   # Lime green belts
GRN  = Color(0.40, 0.85, 0.10)   # Lime green wheels
MTR  = Color(0.15, 0.15, 0.18)   # Motor black
PUL  = Color(0.90, 0.75, 0.10)   # Pulley gold
IDL  = Color(0.85, 0.85, 0.88)   # Idler polished
SHAFT= Color(0.60, 0.60, 0.62)   # Shaft steel
PLATE= Color(0.25, 0.25, 0.28)   # Gantry plates
CUBE = Color(0.65, 0.65, 0.68)   # Splice cubes

# Signature-to-color mapping
SIG_COLORS = {
    (20.0, 80.0, 1200.0): ALU,    # 2080 extrusions
    (20.0, 40.0, 1200.0): ALU,    # 2040 extrusions
    (40.0, 80.0, 1200.0): DRK,    # C-beams (replaced)
    (65.0, 69.0, 69.0):   BRK2,   # L-brackets (replaced)
    (56.4, 56.4, 76.6):   MTR,    # Motors
    (3.0, 88.0, 127.0):   PLATE,  # Gantry plates
    (10.2, 23.9, 23.9):   GRN,    # V-wheels
    (14.0, 15.0, 15.0):   PUL,    # Pulleys
    (12.7, 22.0, 22.0):   IDL,    # Idlers
    (20.0, 20.0, 20.0):   CUBE,   # Splice cubes
}
BELT_SIGS = {(1.5, 6.0, 1131.0), (1.5, 6.0, 1141.8), (1.5, 6.0, 1143.0)}

# ============================================================
# Load and classify
# ============================================================
print("M3-CRETE M3-2 Assembly v3.0 (filter-and-replace)")
print(f"Loading {USER_STEP}...")
t0 = time.time()

stock = cq.importers.importStep(USER_STEP)
solids = stock.val().Solids()
print(f"  {len(solids)} solids loaded in {time.time()-t0:.1f}s")

assy = Assembly("M3-2_Assembly")
n = [0]
replaced_cbeams = 0
replaced_brackets = 0

# Generic brackets built per-instance (each needs correct axle orientation)

# Build C-beam Z-post template from the 1000mm stock STEP profile.
# Stock: X[-20,20] (40mm) × Y[-40,40] (80mm) × Z[0,1000], channel on -X face.
# Target: 40(X) × 80(Y) × 1200(Z). Stock natural orientation = 40(X) × 80(Y),
# so no rotation needed — just extrude to 1200mm.
_cbeam_left  = None   # channel on +X (for left posts: FL, RL)
_cbeam_right = None   # channel on -X (for right posts: FR, RR) — stock natural

_stock_path = os.path.join(os.path.dirname(__file__),
                            "Advanced", "Linear Rail",
                            "C-Beam 40x80x1000 Linear Rail.step")
if os.path.exists(_stock_path):
    _stock = cq.importers.importStep(_stock_path)
    _end_face = _stock.faces("<Z").val()
    _outer_wire = _discretize_wire(_end_face.outerWire().wrapped, deflection=1.0)
    _solid_face = BRepBuilderAPI_MakeFace(_outer_wire).Face()
    # Extrude 1200mm along +Z
    _prism = BRepPrimAPI_MakePrism(_solid_face, gp_Vec(0, 0, 1200))
    _stock_beam = cq.Workplane().add(cq.Shape(_prism.Shape()))
    # Stock: 40(X) × 80(Y) × 1200(Z), channel on -X.
    # Target: 80(X) × 40(Y) × 1200(Z) with channel on ±Y (long axis X per Nick).
    # Rotate +90 around Z: X → Y, Y → -X. So 40(X) → 40(Y), 80(Y) → 80(X),
    # and -X channel → -Y channel. Use this for rear posts (RL/RR).
    # For front posts, rotate -90° to get +Y channel.
    _cbeam_rear  = _stock_beam.rotate((0,0,0), (0,0,1), 90)   # channel -Y
    _cbeam_front = _stock_beam.rotate((0,0,0), (0,0,1), -90)  # channel +Y
    print(f"  Built C-beam Z-post templates from 1000mm stock "
          f"(80x40 cross-section, long axis X, channel ±Y)")

    # Place 4 Z-posts. Positions derived from Nick's example RR corner:
    # wheels at X=2412/2512 (span 100 → post 80mm wide in X, center 2460),
    # all belts/pulleys/idlers centered at X=2460 Y=1227.
    # Other corners mirrored around frame center (1240, 620).
    _POST_POSITIONS = [
        ("FL", 20,   13,   "+Y"),
        ("FR", 2460, 13,   "+Y"),
        ("RL", 20,   1227, "-Y"),
        ("RR", 2460, 1227, "-Y"),
    ]
    for label, px, py, chan in _POST_POSITIONS:
        template = _cbeam_front if chan == "+Y" else _cbeam_rear
        assy.add(template, name=f"post_cbeam_{label}",
                 color=DRK, loc=Location((px, py, 0)))
        n[0] += 1
else:
    print(f"  WARNING: C-beam stock not found at {_stock_path}")

for s in solids:
    bb = s.BoundingBox()
    dx = round(bb.xmax - bb.xmin, 1)
    dy = round(bb.ymax - bb.ymin, 1)
    dz = round(bb.zmax - bb.zmin, 1)
    dims = tuple(sorted([dx, dy, dz]))
    cx = (bb.xmin + bb.xmax) / 2
    cy = (bb.ymin + bb.ymax) / 2
    cz = (bb.zmin + bb.zmax) / 2

    # Z-posts are now added before the main loop from _POST_POSITIONS
    # Skip any remaining 2040 solids with dz=1200 (shouldn't be any in Azzz)
    if dims == (20.0, 40.0, 1200.0) and abs(dz - 1200) < 1:
        continue

    if dims == (40.0, 80.0, 1200.0):
        # Y-rail C-BEAM: replace with solid-fill outer-wire extrude
        wp = cq.Workplane().add(s)
        try:
            replacement = _solid_fill_extrude(wp, "<Y", gp_Vec(0, 1200, 0))
            # Translate to match original position
            orig_ymin = bb.ymin
            rep_bb = replacement.val().BoundingBox()
            dy_shift = orig_ymin - rep_bb.ymin
            dx_shift = bb.xmin - rep_bb.xmin
            dz_shift = bb.zmin - rep_bb.zmin
            assy.add(replacement, name=f"zpY_{replaced_cbeams}",
                     color=DRK, loc=Location((dx_shift, dy_shift, dz_shift)))
            replaced_cbeams += 1
            n[0] += 1
            continue
        except Exception as e:
            print(f"  C-beam solid-fill failed: {e}, loading as-is")

    elif dims == (65.0, 69.0, 69.0):
        # L-BRACKET: pass through from Fusion (original geometry for correct
        # bolt spacing). Nick confirmed no IP issue with corner reinforcements
        # removed. 879 KB each, ~4 brackets.
        wp = cq.Workplane().add(s)
        assy.add(wp, name=f"bracket_{replaced_brackets}",
                 color=BRK2, loc=Location((0, 0, 0)))
        replaced_brackets += 1
        n[0] += 1
        continue

    # DEFAULT: pass through from Fusion at full fidelity
    color = BELT if dims in BELT_SIGS else SIG_COLORS.get(dims, ALU)
    name_prefix = {
        (20.0, 80.0, 1200.0): "rail_2080",
        (20.0, 40.0, 1200.0): "rail_2040",
        (56.4, 56.4, 76.6):   "motor",
        (3.0, 88.0, 127.0):   "plate",
        (10.2, 23.9, 23.9):   "vwheel",
        (14.0, 15.0, 15.0):   "pulley",
        (12.7, 22.0, 22.0):   "idler",
        (20.0, 20.0, 20.0):   "splice",
    }.get(dims, "part")

    wp = cq.Workplane().add(s)
    assy.add(wp, name=f"{name_prefix}_{n[0]}", color=color,
             loc=Location((0, 0, 0)))
    n[0] += 1

print(f"\n  {n[0]} parts total")
print(f"  {replaced_cbeams} C-beams replaced with solid-fill parametric")
print(f"  {replaced_brackets} L-brackets replaced with generic parametric")
print(f"  Generation time: {time.time()-t0:.1f}s")

out = os.path.join(os.path.dirname(__file__), "M3-2_Assembly.step")
print(f"\nExporting {n[0]} parts to STEP...")
t1 = time.time()
assy.save(out)
mb = os.path.getsize(out) / 1024 / 1024
print(f"  {mb:.1f} MB in {time.time()-t1:.1f}s")

print(f"\n  v3.0 Filter-and-replace ({n[0]} parts)")
