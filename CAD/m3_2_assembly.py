"""
M3-CRETE M3-2 Assembly — v3 (filter-and-replace from Fusion export)

Loads all parts from M3-2_Assembly_user.v21.step, then:
  - Replaces C-beams (40x80x1000) with solid-fill parametric versions
  - Removes legacy metal NEMA23 L-brackets
  - Adds simple printed motor-mount/spacer combination plates for Z corners
    and flat printed adapter plates for the two Y motors
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

USER_STEP = os.path.join(os.path.dirname(__file__), "M3-2_nudge.step")

# ============================================================
# Frame: 1000mm C-beam extrusions (shipping constraint).
# Source M3-2_AllC.step is already in the 1000mm envelope (Nick's manual
# corner-RR adjustments baked in), so SXY=SZ=1 — no scaling. Corner
# fixups below mirror Nick's RR edits onto the other three corners.
# ============================================================
L         = 1000.0                              # extrusion length (= source)
OLD_L     = 1000.0                              # SXY/SZ become 1.0
SHIM_THK  = 4.0                                 # 4mm spacer between Y-rail end and Z-post
NX_RIGHT  = 2.0 * L + 80.0                      # right Z-post X center  (2080)
NZ_TOP    = L                                   # top of frame Z         (1000)
# Y-direction frame rails span Y[Y_RAIL_START, Y_RAIL_END]; Z-posts and
# top X rails are pushed OUT by SHIM_THK to leave room for end spacers.
Y_RAIL_START = 20.0                                       # all Y rails start here
Y_RAIL_END   = L + 20.0                                   # all Y rails end here
Y_POST_F     = Y_RAIL_START - 20.0 - SHIM_THK             # front Z-post Y center  (-4)
Y_POST_R     = Y_RAIL_END   + 20.0 + SHIM_THK             # rear  Z-post Y center  (1044)
NY_REAR      = Y_POST_R                                   # alias for back-compat
SXY       = (2.0 * L + 80.0) / (2.0 * OLD_L + 80.0)       # 2080/2080 = 1.0
SZ        = L / OLD_L                                      # 1000/1000 = 1.0

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

# Load both solids AND free shells — Nick's C-beams are exported as shells,
# not solids, so we must iterate both.
stock = cq.importers.importStep(USER_STEP)
_stock_compound = stock.val()
solids = list(_stock_compound.Solids())

# Collect C-beam shells (not inside any solid). These are Nick's Fusion-placed
# C-beam Z-posts and Y-rails, which export as shells instead of solids.
# Filter: sorted bbox dims match (40, 80, 1200) within tolerance.
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

cbeam_shells = []
e = TopExp_Explorer(_stock_compound.wrapped, TopAbs_SHELL)
seen_bboxes = set()
while e.More():
    sh = e.Current()
    bb = Bnd_Box()
    BRepBndLib.Add_s(sh, bb)
    if not bb.IsVoid():
        xmin,ymin,zmin,xmax,ymax,zmax = bb.Get()
        dx = round(xmax-xmin, 1); dy = round(ymax-ymin, 1); dz = round(zmax-zmin, 1)
        sorted_dims = tuple(sorted([dx,dy,dz]))
        if sorted_dims == (40.0, 80.0, 1000.0):
            # Dedup by bbox tuple (distinct C-beams will have different positions)
            key = (round(xmin,1),round(ymin,1),round(zmin,1),round(xmax,1),round(ymax,1),round(zmax,1))
            if key not in seen_bboxes:
                seen_bboxes.add(key)
                try:
                    shell = TopoDS.Shell_s(sh)
                    solid = BRepBuilderAPI_MakeSolid(shell).Solid()
                    cbeam_shells.append(cq.Solid(solid))
                except: pass
    e.Next()

solids = list(solids) + cbeam_shells
print(f"  {len(solids)} total parts ({len(cbeam_shells)} C-beam shells loaded)")

assy = Assembly("M3-2_Assembly")
n = [0]
replaced_cbeams = 0
replaced_brackets = 0

# Tracking lists for post-loop additions (corner connectors, Y-motor
# brackets, idler axle brackets) — each entry is a world bbox tuple
# (xmin, xmax, ymin, ymax, zmin, zmax).
cbeam_bbs   = []   # for joint detection
ymotor_bbs  = []   # for Y-motor bracket placement
idler_bbs   = []   # for idler axle bracket placement
_vwheel_template_shape = None  # populated from first loaded V-wheel; cloned for X-carriage
FRAME_CTR = (NX_RIGHT / 2.0, (Y_POST_F + Y_POST_R) / 2.0, NZ_TOP / 2.0)

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
    # EXPERIMENT: feed the native wire (with CIRCLE arcs preserved) straight
    # into MakePrism instead of discretizing to straight segments. Should
    # produce proper cylindrical side faces for the V-grooves and drop the
    # STEP file size dramatically (was 68 MB w/ discretization).
    _outer_wire = _end_face.outerWire().wrapped
    _prism = BRepPrimAPI_MakePrism(_outer_wire, gp_Vec(0, 0, L))
    _stock_beam = cq.Workplane().add(cq.Shape(_prism.Shape()))
    # Stock: 40(X) × 80(Y) × 1200(Z), channel on -X.
    # Target: 80(X) × 40(Y) × 1200(Z) with channel on ±Y (long axis X per Nick).
    # Rotate +90 around Z: X → Y, Y → -X. So 40(X) → 40(Y), 80(Y) → 80(X),
    # and -X channel → -Y channel. Use this for rear posts (RL/RR).
    # For front posts, rotate -90° to get +Y channel.
    _cbeam_rear  = _stock_beam.rotate((0,0,0), (0,0,1), 90)   # channel -Y
    _cbeam_front = _stock_beam.rotate((0,0,0), (0,0,1), -90)  # channel +Y
    # Y-rail templates: rotate stock -90° around X so long axis Z→Y.
    # Result: X[-20,20] (40), Y[0,1200] (1200), Z[-40,40] (80).
    # Channel stays on -X face (suitable for RIGHT rail at high X).
    _cbeam_yrail_R = _stock_beam.rotate((0,0,0), (1,0,0), -90)
    # Mirror around Y for LEFT rail (channel on +X face, facing inward).
    _cbeam_yrail_L = _cbeam_yrail_R.rotate((0,0,0), (0,1,0), 180)

    # Flat-lying Y-rail: 80(X) × 1200(Y) × 40(Z), channel -Z.
    # For top + bottom Y-direction frame members — wider stiffness, channel
    # facing down avoids debris catch (top) and accepts leg extensions (bottom).
    _cbeam_yrail_flat = (_stock_beam
                         .rotate((0,0,0), (1,0,0), -90)
                         .rotate((0,0,0), (0,1,0), 90))

    # Tall X-rail: 1200(X) × 40(Y) × 80(Z), channel ±Y inward.
    _cbeam_xrail_chanYp = (_stock_beam
                           .rotate((0,0,0), (0,1,0), 90)
                           .rotate((0,0,0), (1,0,0), 90))
    _cbeam_xrail_chanYn = _cbeam_xrail_chanYp.rotate((0,0,0), (1,0,0), 180)

    # Flat-lying X-rail: 1200(X) × 80(Y) × 40(Z), channel -Z.
    # For mid-frame X-direction cross-braces (frame center, channel down).
    _cbeam_xrail_flat = _cbeam_yrail_flat.rotate((0,0,0), (0,0,1), -90)

    print(f"  Built C-beam templates: Z-posts, Y-rails (tall + flat), "
          f"X-rails (tall + flat)")

    # Place 4 Z-posts. Posts shifted outward in Y by 4mm to make room for
    # 4mm shims between top Y-rails / bottom Y-skids and Z-post inner faces.
    # This gives the 1200mm C-beam Y-gantry an 8mm running clearance
    # (4mm + 3mm carriage plate + 1mm working gap on each side).
    _POST_POSITIONS = [
        ("FL", 0,    -4,   "+Y"),
        ("FR", 2480, -4,   "+Y"),
        ("RL", 0,    1244, "-Y"),
        ("RR", 2480, 1244, "-Y"),
    ]
    # Nick's C-beam shells (Z-posts + Y-rails) are matched to template
    # instances inside the main loop below — keyed by orientation + position.

    # 8x 4mm Y-direction shims between flat top/bottom Y C-beams and Z-post
    # inner faces. New flat C-beam end face is 80(X) × 40(Z), so shim is
    # 80×4×40, anchored on Z-post X-centerline (X=0 left, X=2480 right).
    SHIM = Color(0.85, 0.45, 0.10)   # orange — visually distinct from frame
    # Shims sit only between STATIC frame Y-members (top, bottom, top middle)
    # and the Z-posts they butt against — they create the 4 mm clearance
    # the gantry needs to traverse along the Z-posts. The mid-height gantry
    # rails carry the moving gantry; their ends don't need shims.
    shim_4080_flat = cq.Workplane("XY").box(80, SHIM_THK, 40)
    _SY_F = Y_RAIL_START - SHIM_THK / 2.0    # 18 — front shim Y center (Y[16,20])
    _SY_R = Y_RAIL_END   + SHIM_THK / 2.0    # 1022 — rear  shim Y center
    _SZ_T = NZ_TOP - 20.0                    # 980 — top   shim Z center
    _SZ_B = 20.0                             # 20  — bot   shim Z center
    _SX_TM = NX_RIGHT / 2.0                  # 1040 — top mid Y rail X center
    shim_specs = [
        # Top mid-frame Y rails: 2 shims (only the center spreader needs
        # them). The 4 top-corner shims were removed — superseded by the
        # combined zmount plate which integrates the Y-spacer role.
        ("topmid_front",  _SX_TM,   _SY_F, _SZ_T, shim_4080_flat),
        ("topmid_rear",   _SX_TM,   _SY_R, _SZ_T, shim_4080_flat),
        # Bottom 4 corner shims removed — replaced by combined bottom
        # spacer/idler-mount plates in post-loop section
    ]
    for name, sx, sy, sz, shim_shape in shim_specs:
        assy.add(shim_shape, name=f"shim_{name}", color=SHIM,
                 loc=Location((sx, sy, sz)))
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

    # Skip the OLD shims baked into the source — script rebuilds shims fresh.
    if dims == (4.0, 40.0, 80.0):
        continue

    # ============================================================
    # CORNER FIXUPS — mirror Nick's RR edits to FL/FR/RL.
    # Nick adjusted the rear-right Z-motor stack so the bracket / motor /
    # belt align correctly with the corner Z-gantry plate. The same
    # geometry applies symmetrically to the other three corners.
    #
    # Per-part deltas (toward frame center for Y, away for X):
    #   Z-motor:  X ±4.25 (outward), Y ±12 (inward), Z +6.75 (up)
    #   bracket:  X ±4.25 (outward), Y ±12 (inward)
    #   plate:    Y ±3 (inward) — Z-corner gantry plate only
    # ============================================================
    fix_dx = fix_dy = fix_dz = 0.0

    # M3-2_newZMM.step authors the front-right simplified Z motor stack.
    # Mirror those motor, pulley, idler, and vertical belt positions to
    # every Z post so all four corners share one belt path.
    if dims == (56.4, 56.4, 76.6) and cz > 900:
        is_left = cx < FRAME_CTR[0]
        is_front = cy < FRAME_CTR[1]
        target_x = 0.6 if is_left else NX_RIGHT - 0.6
        target_y = 36.1 if is_front else (2 * FRAME_CTR[1] - 36.1)
        target_z = 1028.2
        fix_dx, fix_dy, fix_dz = target_x - cx, target_y - cy, target_z - cz
    elif dims == (14.0, 15.0, 15.0) and cz > 900:
        is_left = cx < FRAME_CTR[0]
        is_front = cy < FRAME_CTR[1]
        target_x = 0.6 if is_left else NX_RIGHT - 0.6
        target_y = 7.2 if is_front else (2 * FRAME_CTR[1] - 7.2)
        target_z = 1028.1
        fix_dx, fix_dy, fix_dz = target_x - cx, target_y - cy, target_z - cz
    elif dims == (12.7, 22.0, 22.0) and cz < 150 and (cx < 100 or cx > NX_RIGHT - 100):
        is_left = cx < FRAME_CTR[0]
        is_front = cy < FRAME_CTR[1]
        target_x = 0.6 if is_left else NX_RIGHT - 0.6
        target_y = 5.1 if is_front else (2 * FRAME_CTR[1] - 5.1)
        target_z = 101.7
        fix_dx, fix_dy, fix_dz = target_x - cx, target_y - cy, target_z - cz
    elif dims[0] == 1.5 and dims[1] == 6.0 and dz > 900 and (cx < 100 or cx > NX_RIGHT - 100):
        is_left = cx < FRAME_CTR[0]
        is_front = cy < FRAME_CTR[1]
        post_x = 0.0 if is_left else NX_RIGHT
        if is_left:
            rel_x = -4.9 if cx < post_x else 6.0
        else:
            rel_x = -6.0 if cx < post_x else 4.9
        target_x = post_x + rel_x
        target_y = 5.1 if is_front else (2 * FRAME_CTR[1] - 5.1)
        target_z = 557.1
        fix_dx, fix_dy, fix_dz = target_x - cx, target_y - cy, target_z - cz

    # 1. Z-motor corner stack — motors rest on 5mm cap (zmin ≈ 1005)
    #    Source non-RR motors already at correct Z (zmin=1005.1). No Z fixup.
    #    Source RR motor is higher (zmin=1011.9), fix down to match.
    #    Verified against Nick's Fusion placement: M3-2_Ass_3dbrak.step
    if False and cz > 900 and dims in {(56.4, 56.4, 76.6), (65.0, 69.0, 69.0)}:
        is_left  = cx < 1040
        is_front = cy < 520
        is_RR    = (not is_left) and (not is_front)
        if is_RR:
            if dims == (56.4, 56.4, 76.6):
                fix_dz = -6.9   # 1005 - 1011.9 (match cap top)
        else:
            sign_x = -1.0 if is_left  else +1.0
            sign_y = +1.0 if is_front else -1.0
            fix_dx = 4.25 * sign_x
            fix_dy = 12.0 * sign_y
            # No Z fixup — source motors already at correct height

    # 2. Gantry plates (mid-height, signature 3x88x127)
    #    — Corner Z-gantry plates snap to an ABSOLUTE Y target so all 4
    #      corners match Nick's RR position uniformly (front cy=18.52,
    #      rear cy=1021.48). This removes the 0.65 mm clip FR had from
    #      the relative +3 fixup because the source cy values aren't
    #      perfectly symmetric.
    #    — Mid X-carriage plates (at cy~520) snap to X targets so their
    #      inner face clears the mid Y rail by 1 mm. The source has them
    #      clipping 0.3-2.1 mm into the rail, never modeled flush.
    elif dims == (3.0, 88.0, 127.0) and 200 < cz < 600:
        # 1 mm gap to mid Y rail end. Plate is 3 mm thick (3/2=1.5 half);
        # rail starts at Y=20 (front) or ends at Y=1020 (rear). Gap 1 mm
        # -> plate inner face at Y=19 (front) or Y=1021 (rear).
        if cy < 100:                                  # front corner plate
            fix_dy = 17.5 - cy                        # plate Y[16, 19], 1 mm gap
        elif cy > 940:                                # rear corner plate
            fix_dy = 1022.5 - cy                      # plate Y[1021, 1024], 1 mm gap
        elif 400 < cy < 600 and dx < 10:              # mid Y-gantry carrier plate
            # Mid Y rail inner X faces: left rail ends at X=32.9, right
            # rail starts at X=2048.9. Plate is 3 mm thick in X, want
            # 1 mm clearance -> plate cx = rail_face ± (1 + 1.5).
            if cx < 1040:
                fix_dx = 35.4 - cx
            else:
                fix_dx = 2046.4 - cx

    fcx, fcy, fcz = cx + fix_dx, cy + fix_dy, cz + fix_dz

    # ============================================================
    # C-BEAM (40x80x1000 in AllC source) → 1000mm template
    # AllC source positions are authoritative — just substitute the
    # geometry with our parametric template at the source bbox.min.
    # ============================================================
    if dims == (40.0, 80.0, 1000.0):
        try:
            if abs(dz - 1000) < 1:
                template = _cbeam_rear if cy < 520 else _cbeam_front
                kind = "Zpost"
            elif abs(dy - 1000) < 1:
                if 300 < cz < 600:
                    template = _cbeam_yrail_R if cx < 1040 else _cbeam_yrail_L
                    kind = "Yrail"
                else:
                    template = _cbeam_yrail_flat
                    kind = "Yflat"
            elif abs(dx - 1000) < 1:
                if cz > 900:
                    template = _cbeam_xrail_chanYp if cy < 520 else _cbeam_xrail_chanYn
                    kind = "Xtop"
                elif 300 < cz < 600 and 400 < cy < 640:
                    # X-gantry beam (moving): mid-Y, mid-Z. Source is flat;
                    # we rotate to tall (80 mm vertical) for bending
                    # resistance — 2 m span simply-supported, 5 kg mid-load
                    # gives δ = 0.225 mm bare vs 0.727 mm flat.
                    template = _cbeam_xrail_chanYp
                    kind = "Xgantry"
                else:
                    template = _cbeam_xrail_flat
                    kind = "Xmid"
            else:
                raise RuntimeError(f"unexpected C-beam dims {dims}")
            tbb = template.val().BoundingBox()
            if kind == "Xgantry":
                # Center-align because flat source bbox (80 in Y) differs
                # from the tall template bbox (80 in Z). Corner-align would
                # offset the beam by the mismatch.
                tcx = (tbb.xmin + tbb.xmax) / 2.0
                tcy = (tbb.ymin + tbb.ymax) / 2.0
                tcz = (tbb.zmin + tbb.zmax) / 2.0
                loc_vec = (cx - tcx, cy - tcy, cz - tcz)
            else:
                loc_vec = (bb.xmin - tbb.xmin,
                           bb.ymin - tbb.ymin,
                           bb.zmin - tbb.zmin)
            assy.add(template, name=f"cbeam_{kind}_{replaced_cbeams}",
                     color=DRK, loc=Location(loc_vec))
            cbeam_bbs.append((bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
            replaced_cbeams += 1
            n[0] += 1
            continue
        except Exception as e:
            print(f"  C-beam placement failed at ({cx:.0f},{cy:.0f},{cz:.0f}): {e}")
            continue

    # ============================================================
    # L-BRACKET — REMOVED. Skip the legacy bracket signatures only.
    # All other plates (zmount, bot-mount, ymount/spacer) now flow
    # through from the source STEP — no parametric overrides.
    # ============================================================
    if dims in {(65.0, 69.0, 69.0), (44.0, 80.0, 102.0)}:
        continue

    # ============================================================
    # DEFAULT pass-through — translate by corner fixup delta only.
    # AllC source positions are otherwise authoritative.
    # ============================================================
    is_belt = dims[0] == 1.5 and dims[1] == 6.0
    color = BELT if is_belt else SIG_COLORS.get(dims, ALU)
    name_prefix = "belt" if is_belt else {
        (56.4, 56.4, 76.6):   "motor",
        (3.0, 88.0, 127.0):   "plate",
        (10.2, 23.9, 23.9):   "vwheel",
        (14.0, 15.0, 15.0):   "pulley",
        (12.7, 22.0, 22.0):   "idler",
        (20.0, 20.0, 20.0):   "splice",
    }.get(dims, "part")

    wp = cq.Workplane().add(s)
    assy.add(wp, name=f"{name_prefix}_{n[0]}", color=color,
             loc=Location((fcx - cx, fcy - cy, fcz - cz)))

    # Capture a V-wheel shape once for post-loop X-carriage cloning so
    # added wheels share the real V-profile instead of a plain cylinder.
    if dims == (10.2, 23.9, 23.9) and _vwheel_template_shape is None:
        _vwheel_template_shape = s

    # Track parts that need post-loop bracket additions (in WORLD coords
    # = source coords + fixup delta, since SXY=SZ=1).
    wbb = (bb.xmin + (fcx-cx), bb.xmax + (fcx-cx),
           bb.ymin + (fcy-cy), bb.ymax + (fcy-cy),
           bb.zmin + (fcz-cz), bb.zmax + (fcz-cz))
    if dims == (56.4, 56.4, 76.6) and fcz < 600:
        ymotor_bbs.append(wbb)
    elif dims == (12.7, 22.0, 22.0):
        idler_bbs.append(wbb)
    n[0] += 1

# ============================================================
# POST-LOOP additions: printed mount/spacer plates, corner connectors, idler brackets
# ============================================================
CONN_COLOR  = Color(0.45, 0.45, 0.50)   # steel grey
IDL_BRK_COLOR = Color(0.59, 0.84, 0.00)  # green (printed part)
FRAME_CTR = (NX_RIGHT / 2.0, (Y_POST_F + Y_POST_R) / 2.0, NZ_TOP / 2.0)

def _cbeam_axis(b):
    if (b[5] - b[4]) > 500: return 'Z'
    if (b[3] - b[2]) > 500: return 'Y'
    if (b[1] - b[0]) > 500: return 'X'
    return None

def _joint_normal(a, b):
    aa, bb_ax = _cbeam_axis(a), _cbeam_axis(b)
    if aa is None or bb_ax is None or aa == bb_ax:
        return None
    return ({'X', 'Y', 'Z'} - {aa, bb_ax}).pop()

def _joint_center(a, b):
    return (
        (max(a[0], b[0]) + min(a[1], b[1])) / 2.0,
        (max(a[2], b[2]) + min(a[3], b[3])) / 2.0,
        (max(a[4], b[4]) + min(a[5], b[5])) / 2.0,
    )

def _bbs_touch(a, b, tol=5.0):
    return (a[0] - tol <= b[1] and b[0] - tol <= a[1] and
            a[2] - tol <= b[3] and b[2] - tol <= a[3] and
            a[4] - tol <= b[5] and b[4] - tol <= a[5])

# --- Z-motor mount + bottom spacer/idler plates: NOT generated parametrically ---
# Earlier parametric generation here produced plates with hole patterns that
# didn't line up with the actual motor / idler positions. The user-authored
# source STEP (M3-2_xCar.step) carries these plates with correct geometry.
# CADCLAW's job is placement and interference checking, not part generation.
# Constants kept for downstream references (T-bracket bolt grid).
import math as _math
HERE = os.path.dirname(__file__)
PRINT_COLOR = Color(0.59, 0.84, 0.00)    # Sunnyday trademark green (matches belts)
NEMA_PCD    = 47.14
NEMA_BOLT   = 5.5
NEMA_CENTER = 23.0

# Remaining idler brackets: only the center-frame idler (not at a corner post)
# keeps its separate bracket. Corner idlers are now part of the bottom plates.
n_idlerbrk = 0
idler_brk = cq.Workplane("YZ").box(5, 30, 30)
for wbb in idler_bbs:
    cx = (wbb[0] + wbb[1]) / 2.0
    cz = (wbb[4] + wbb[5]) / 2.0
    # Skip corner idlers at bottom of Z-posts (integrated into bottom plates).
    # Corner idlers are at Z < 150 AND at the corner post X positions.
    # Mid-frame idler is at Z~370 (mid-height on Y-rail), keep it.
    if cz < 150 and (cx < 100 or cx > NX_RIGHT - 100):
        continue
    cy = (wbb[2] + wbb[3]) / 2.0
    cz = (wbb[4] + wbb[5]) / 2.0
    nx = cx + (-15 if cx < FRAME_CTR[0] else +15)
    assy.add(idler_brk, name=f"bracket_idler_{n_idlerbrk}", color=IDL_BRK_COLOR,
             loc=Location((nx, cy, cz)))
    n_idlerbrk += 1
    n[0] += 1
print(f"  {n_idlerbrk} remaining idler brackets (mid-frame)")

# --- Y-motor adapter plate / 4mm spacer ---
# Intentionally NOT generated parametrically. The user supplies the rotated
# motor (~45° about shaft axis so bolt holes align with V-slot centerlines)
# and the 4mm spacer plate via the authored M3-2_newZMM.step. Earlier
# parametric generation here clipped the motor body — placement, not
# part generation, is CADCLAW's job. Source STEP is the source of truth.
SLOT_HOLE_D = 5.5  # M5 clearance — used by the T-bracket bolt grid below

# --- Y-axis return idlers (front of each Y-rail, opposite the Y-motors) ---
# Each Y-belt loops from the rear motor pulley to a smooth return idler at
# the front of the rail. The user-supplied internal-slot mount + outer
# plate (TBD) anchors the idler axle; CADCLAW places the idler wheel so
# the belt path endpoints are visible in the assembly.
Y_IDLER_OD = 22.0  # mm (matches existing idler signature)
Y_IDLER_H  = 12.7  # mm (axial height, axis along Z)
Y_IDLER_Y  = Y_RAIL_START + 15.0  # 35 — set back from rail front edge
_y_return_idler = (cq.Workplane("XY")
                   .circle(Y_IDLER_OD / 2)
                   .extrude(Y_IDLER_H)
                   .translate((0, 0, -Y_IDLER_H / 2)))

n_y_idlers = 0
for wbb in ymotor_bbs:
    cx = (wbb[0] + wbb[1]) / 2.0
    cz = (wbb[4] + wbb[5]) / 2.0
    is_left = cx < FRAME_CTR[0]
    # Pulley sits ~24mm outboard of motor cx along X (away from frame
    # center). Mirror that offset to land on the rail centerline at the
    # opposite belt end.
    pulley_offset = -24.0 if is_left else +24.0
    idler_x = cx + pulley_offset
    assy.add(_y_return_idler, name=f"idler_y_return_{n_y_idlers}", color=IDL,
             loc=Location((idler_x, Y_IDLER_Y, cz)))
    n_y_idlers += 1
    n[0] += 1
print(f"  {n_y_idlers} Y-axis return idlers at front of rails (silver)")

# --- T-brackets at center Y-spreader / X-rail T-junctions ---
# The center Y-spreader (X=1000-1080) meets the front and rear top X-rails
# at T-junctions. A 3D-printed T-bracket straddles the junction, bolting
# to both the spreader end and the X-rail face.
# Bracket: 120mm wide (along X-rail), 80mm tall (along spreader), 4mm thick
TBRACKET_W = 280.0     # mm along X-rail (matches Fusion 280 long dim)
TBRACKET_H = 160.0     # mm along Y-spreader (matches Fusion 160 wide dim)
TBRACKET_T = 4.0
# Pentagon/trapezoid approximation of the Fusion semi-triangular gusset:
# - Long base along the X-rail (Y=0 side): full 280 mm.
# - Narrower top at the Y-spreader side (Y=TBRACKET_H): tapers to 100 mm.
# - Two angled corners chamfered to give the "home plate" pentagon profile.
# Bolt pattern simplified to a 5×3 grid; real design has more holes.
TBRACKET_TOP_W = 100.0   # narrower top edge (toward spreader)
_SX_MID = (1000.0 + 1080.0) / 2.0  # center of spreader = X=1040

# Pentagon gusset profile (isoceles trapezoid, CCW in XY plane):
#   Y=-TBRACKET_H/2 is the long base along the X-rail.
#   Y=+TBRACKET_H/2 is the short top edge along the Y-spreader.
_tb_half_base = TBRACKET_W / 2.0      # 140
_tb_half_top  = TBRACKET_TOP_W / 2.0  # 50
_tb_half_h    = TBRACKET_H / 2.0      # 80
_tb_profile = [
    (-_tb_half_base, -_tb_half_h),
    ( _tb_half_base, -_tb_half_h),
    ( _tb_half_top,   _tb_half_h),
    (-_tb_half_top,   _tb_half_h),
]
_tbracket = (cq.Workplane("XY")
             .polyline(_tb_profile).close()
             .extrude(TBRACKET_T)
             # 5x3 bolt grid: 5 along X-rail (base), 3 rows Y-ward (base, mid, top).
             # Rows scale their X-spread to stay inside the tapering polygon.
             .faces(">Z").workplane()
             .pushPoints([
                 # base row (Y = -60)
                 (-120, -60), (-60, -60), (0, -60), (60, -60), (120, -60),
                 # middle row (Y = 0)
                 (-90, 0), (-30, 0), (30, 0), (90, 0),
                 # top row (Y = 60)
                 (-30, 60), (0, 60), (30, 60),
             ])
             .hole(SLOT_HOLE_D))

# T-gussets at the top-rail / Y-spreader junctions.
# Strategy: prefer the *authored* Fusion gussets from M3-2_Assembly.step
# so we preserve the full polygon profile + real bolt-grid pattern that
# CADQuery can't economically re-author parametrically. Fall back to the
# trapezoidal approximation if the Fusion file is unavailable or missing
# the gussets (e.g. Fusion visibility-toggle bug ate them).
_FUSION_REF = os.path.join(os.path.dirname(__file__), "M3-2_Assembly.step")
_authored_gussets = []
if os.path.exists(_FUSION_REF):
    try:
        _ref_compound = cq.importers.importStep(_FUSION_REF).val()
        _ref_solids = list(_ref_compound.Solids()) + list(_ref_compound.Shells())
        _seen = set()
        for _s in _ref_solids:
            _bb = _s.BoundingBox()
            _dx = round(_bb.xmax - _bb.xmin, 1)
            _dy = round(_bb.ymax - _bb.ymin, 1)
            _dz = round(_bb.zmax - _bb.zmin, 1)
            _sig = tuple(sorted([_dx, _dy, _dz]))
            # Fusion's gusset signature: 4 mm thick, 160 × 280 envelope
            if _sig == (4.0, 160.0, 280.0):
                _cx = round((_bb.xmin + _bb.xmax) / 2.0, 1)
                _cy = round((_bb.ymin + _bb.ymax) / 2.0, 1)
                _cz = round((_bb.zmin + _bb.zmax) / 2.0, 1)
                _ckey = (_cx, _cy, _cz)
                if _ckey not in _seen:
                    _seen.add(_ckey)
                    _authored_gussets.append(_s)
    except Exception as _e:
        print(f"  [warn] could not import authored gussets: {_e}")

n_tbrackets = 0
if len(_authored_gussets) >= 2:
    # Use the real Fusion-authored gussets — full polygon + bolt grid.
    for _g in _authored_gussets:
        _wp = cq.Workplane().add(_g)
        assy.add(_wp, name=f"tbracket_{n_tbrackets}", color=PRINT_COLOR)
        n_tbrackets += 1
        n[0] += 1
    print(f"  {n_tbrackets} T-gussets imported from Fusion "
          f"(full detail, real hole pattern)")
else:
    # Fallback: parametric trapezoid at the design-intent positions.
    _t_junctions = [
        (_SX_MID, 58.0,  1002.0),
        (_SX_MID, 982.0, 1002.0),
    ]
    for tx, ty, tz in _t_junctions:
        tb = _tbracket.translate((0, 0, 0))
        assy.add(tb, name=f"tbracket_{n_tbrackets}", color=PRINT_COLOR,
                 loc=Location((tx, ty, tz)))
        n_tbrackets += 1
        n[0] += 1
    print(f"  {n_tbrackets} T-brackets at center spreader "
          f"(parametric trapezoid fallback — authored Fusion gussets not found)")

# --- X-gantry carriage: 8 V-wheels ------------------------------------
# Source AllC.step has Y-carriage wheels at the two gantry ends (X=21,
# X=2059) but lacks the 8 X-carriage wheels that ride on the gantry
# beam itself. Pattern: "same positioning rules as Y/Z carriages, just
# doubled" — 2 wheels along X (spacing) × 2 Y × 2 Z = 8 wheels.
#
# Positions taken from the Fusion M3-2_Assembly.step authored design at
# the X-carriage parked position (X~1496, mid-gantry). Shape here is a
# parametric cylinder placeholder at nominal wheel OD/thickness — exact
# V-race profile comes through when the source re-exports with wheels.
X_CARR_X  = []                  # M3-2_newZMM.step already includes X-carriage wheels
X_CARR_Y  = [508.6, 528.4]     # ±9.9 from gantry centerline Y=520
X_CARR_Z  = [325.0, 408.3]     # ±41.65 from gantry centerline Z=369.5
n_xcarr_wheels = 0
if _vwheel_template_shape is not None:
    _wbb = _vwheel_template_shape.BoundingBox()
    _wtcx = (_wbb.xmin + _wbb.xmax) / 2.0
    _wtcy = (_wbb.ymin + _wbb.ymax) / 2.0
    _wtcz = (_wbb.zmin + _wbb.zmax) / 2.0
    _wheel_wp = cq.Workplane().add(_vwheel_template_shape)
    for wx in X_CARR_X:
        for wy in X_CARR_Y:
            for wz in X_CARR_Z:
                assy.add(_wheel_wp, name=f"vwheel_xcarr_{n_xcarr_wheels}",
                         color=GRN,
                         loc=Location((wx - _wtcx, wy - _wtcy, wz - _wtcz)))
                n_xcarr_wheels += 1
                n[0] += 1
    print(f"  {n_xcarr_wheels} X-carriage V-wheels (cloned from source, green)")
else:
    # Fallback: no V-wheel in source to clone — use parametric cylinder
    _fallback_wheel = cq.Workplane("XZ").cylinder(10.2, 23.9 / 2.0)
    for wx in X_CARR_X:
        for wy in X_CARR_Y:
            for wz in X_CARR_Z:
                assy.add(_fallback_wheel, name=f"vwheel_xcarr_{n_xcarr_wheels}",
                         color=GRN, loc=Location((wx, wy, wz)))
                n_xcarr_wheels += 1
                n[0] += 1
    print(f"  {n_xcarr_wheels} X-carriage V-wheels (fallback cylinder, green)")

# --- X-carriage gantry plates (2x) ------------------------------------
# 3 mm polycarbonate plates (88 × 127) on each ±Y face of the gantry beam
# holding the X-carriage wheels. Dims + positions match Fusion authored
# design at X-carriage parked location X=1496.4.
_xcarr_plate = cq.Workplane("XZ").box(127.0, 88.0, 3.0)  # X:127 Z:88 Y:3
n_xcarr_plates = 0
for py in ():   # M3-2_newZMM.step already includes X-carriage plates
    assy.add(_xcarr_plate, name=f"plate_xcarr_{n_xcarr_plates}",
             color=PLATE, loc=Location((1496.4, py, 366.7)))
    n_xcarr_plates += 1
    n[0] += 1
print(f"  {n_xcarr_plates} X-carriage gantry plates")

print(f"\n  {n[0]} parts total")
print(f"  {replaced_cbeams} C-beams replaced with solid-fill parametric")
print(f"  {replaced_brackets} legacy L-brackets retained")
print(f"  Generation time: {time.time()-t0:.1f}s")

# Write to a distinct filename so CADQuery regen never clobbers a Fusion
# export living at CAD/M3-2_Assembly.step. Renders can point at either.
out = os.path.join(os.path.dirname(__file__), "M3-2_Assembly_cadquery.step")
print(f"\nExporting {n[0]} parts to STEP...")
t1 = time.time()
assy.save(out)
mb = os.path.getsize(out) / 1024 / 1024
print(f"  {mb:.1f} MB in {time.time()-t1:.1f}s")

print(f"\n  v3.0 Filter-and-replace ({n[0]} parts)")
