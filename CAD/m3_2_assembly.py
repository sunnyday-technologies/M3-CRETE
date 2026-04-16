"""
M3-CRETE M3-2 Assembly — v3 (filter-and-replace from Fusion export)

Loads all parts from M3-2_Assembly_user.v21.step, then:
  - Replaces C-beams (40x80x1000) with solid-fill parametric versions
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

USER_STEP = os.path.join(os.path.dirname(__file__), "M3-2_AllC.step")

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
        # Top Y flat rails (sides + middle): 4 corner shims + 2 mid shims
        ("top_L_front",   0.0,      _SY_F, _SZ_T, shim_4080_flat),
        ("top_R_front",   NX_RIGHT, _SY_F, _SZ_T, shim_4080_flat),
        ("top_L_rear",    0.0,      _SY_R, _SZ_T, shim_4080_flat),
        ("top_R_rear",    NX_RIGHT, _SY_R, _SZ_T, shim_4080_flat),
        ("topmid_front",  _SX_TM,   _SY_F, _SZ_T, shim_4080_flat),
        ("topmid_rear",   _SX_TM,   _SY_R, _SZ_T, shim_4080_flat),
        # Bottom Y skids (4 corners)
        ("bot_L_front",   0.0,      _SY_F, _SZ_B, shim_4080_flat),
        ("bot_R_front",   NX_RIGHT, _SY_F, _SZ_B, shim_4080_flat),
        ("bot_L_rear",    0.0,      _SY_R, _SZ_B, shim_4080_flat),
        ("bot_R_rear",    NX_RIGHT, _SY_R, _SZ_B, shim_4080_flat),
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

    # 1. Z-motor + bracket corner stack (top of frame)
    if cz > 900 and dims in {(56.4, 56.4, 76.6), (65.0, 69.0, 69.0)}:
        is_left  = cx < 1040
        is_front = cy < 520
        is_RR    = (not is_left) and (not is_front)
        if not is_RR:                                 # RR already in source
            sign_x = -1.0 if is_left  else +1.0
            sign_y = +1.0 if is_front else -1.0
            fix_dx = 4.25 * sign_x
            fix_dy = 12.0 * sign_y
            if dims == (56.4, 56.4, 76.6):
                fix_dz = 6.75

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
        elif 400 < cy < 600:                          # mid X-carriage plate
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
                else:
                    template = _cbeam_xrail_flat
                    kind = "Xmid"
            else:
                raise RuntimeError(f"unexpected C-beam dims {dims}")
            tbb = template.val().BoundingBox()
            assy.add(template, name=f"cbeam_{kind}_{replaced_cbeams}",
                     color=DRK,
                     loc=Location((bb.xmin - tbb.xmin,
                                    bb.ymin - tbb.ymin,
                                    bb.zmin - tbb.zmin)))
            cbeam_bbs.append((bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
            replaced_cbeams += 1
            n[0] += 1
            continue
        except Exception as e:
            print(f"  C-beam placement failed at ({cx:.0f},{cy:.0f},{cz:.0f}): {e}")
            continue

    # ============================================================
    # L-BRACKET — generic NEMA23 / T-slot bracket (replaces vendor IP).
    # AllC source already has bracket positions correct (bottom-anchored
    # at Z=NZ_TOP, Y push-out applied), so just translate by the corner
    # fixup deltas in fcx/fcy/fcz.
    # ============================================================
    if dims == (65.0, 69.0, 69.0):
        wp = cq.Workplane().add(s)
        assy.add(wp, name=f"bracket_{replaced_brackets}", color=BRK2,
                 loc=Location((fcx - cx, fcy - cy, fcz - cz)))
        replaced_brackets += 1
        n[0] += 1
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
# POST-LOOP additions: corner connectors, Y-motor brackets, idler brackets
# ============================================================
CONN_COLOR  = Color(0.45, 0.45, 0.50)   # steel grey
IDL_BRK_COLOR = Color(0.45, 0.45, 0.50)
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

# --- 3D-printed Z-motor enclosures (replace metal L-corner plates) ---
# Each enclosure caps a Z-post top and grabs adjacent Y+X rails for
# 3-axis registration. Includes NEMA23 motor mount and belt routing.
# Metal L-plates removed — frame joints rely on printed enclosures at
# the 4 corners plus T-nut bolting at mid-span junctions.
HERE = os.path.dirname(__file__)
ENCL_COLOR = Color(0.2, 0.2, 0.2)  # dark grey (printed part)

_ENCL_FL_RAW = cq.importers.importStep(
    os.path.join(HERE, "Custom", "Z_Motor_Enclosure_FL.step"))
_ebb = _ENCL_FL_RAW.val().BoundingBox()
_ENCL_FL = _ENCL_FL_RAW.translate((
    -(_ebb.xmin + _ebb.xmax) / 2.0,
    -(_ebb.ymin + _ebb.ymax) / 2.0,
    -(_ebb.zmin + _ebb.zmax) / 2.0,
))

_ENCL_FR_RAW = cq.importers.importStep(
    os.path.join(HERE, "Custom", "Z_Motor_Enclosure_FR.step"))
_ebb2 = _ENCL_FR_RAW.val().BoundingBox()
_ENCL_FR = _ENCL_FR_RAW.translate((
    -(_ebb2.xmin + _ebb2.xmax) / 2.0,
    -(_ebb2.ymin + _ebb2.ymax) / 2.0,
    -(_ebb2.zmin + _ebb2.zmax) / 2.0,
))

# Place enclosures at the 4 Z-post tops.
# Z-post centers (X,Y) from frame constants; Z = NZ_TOP (post top face)
CB_D = 40.0  # narrow face of 4080
z_corners = [
    ("FL", 0.0,       Y_POST_F + CB_D/2, _ENCL_FL),   # front-left
    ("FR", NX_RIGHT,  Y_POST_F + CB_D/2, _ENCL_FR),   # front-right
    ("RL", 0.0,       Y_POST_R - CB_D/2, _ENCL_FL),   # rear-left
    ("RR", NX_RIGHT,  Y_POST_R - CB_D/2, _ENCL_FR),   # rear-right
]

n_enclosures = 0
for label, px, py, encl_template in z_corners:
    encl = encl_template.translate((0, 0, 0))
    # Rear corners need 180-degree rotation about Z to flip the Y-wing direction
    if "R" in label[0:2] and label[1] == "L":
        encl = encl.rotate((0, 0, 0), (0, 0, 1), 180)
    elif "R" in label[0:2] and label[1] == "R":
        encl = encl.rotate((0, 0, 0), (0, 0, 1), 180)
    assy.add(encl, name=f"z_enclosure_{label}", color=ENCL_COLOR,
             loc=Location((px, py, NZ_TOP)))
    n_enclosures += 1
    n[0] += 1
print(f"  {n_enclosures} Z-motor enclosures (3D printed)")

# --- Y-motor brackets (re-use generic NEMA23 L-bracket template) ---
# Y-motors have their long axis in X (motor cross-section is 56.4 x 56.4
# in Y-Z, and the 76.6mm shaft direction is X). The bracket sits flush to
# the motor's NEMA face on the +X or -X side, depending on which side of
# frame center the motor is.
n_ybrackets = 0
for wbb in ymotor_bbs:
    cx = (wbb[0] + wbb[1]) / 2.0
    cy = (wbb[2] + wbb[3]) / 2.0
    cz = (wbb[4] + wbb[5]) / 2.0
    is_left = cx < FRAME_CTR[0]
    bracket = _make_generic_bracket("X")          # 65mm axis along X
    bbb = bracket.val().BoundingBox()
    bracket_dx = (bbb.xmax - bbb.xmin)
    new_cx = cx + (-bracket_dx/2 - 1 if is_left else +bracket_dx/2 + 1)
    bcx = (bbb.xmin + bbb.xmax) / 2.0
    bcy = (bbb.ymin + bbb.ymax) / 2.0
    bcz = (bbb.zmin + bbb.zmax) / 2.0
    assy.add(bracket, name=f"bracket_Y_{n_ybrackets}", color=BRK2,
             loc=Location((new_cx - bcx, cy - bcy, cz - bcz)))
    n_ybrackets += 1
    n[0] += 1
print(f"  {n_ybrackets} Y-motor brackets")

# --- Idler axle support brackets (small flat plate behind each idler) ---
# Each idler gets a 30 x 5 x 30 plate behind it (anchored to the C-beam face
# the idler bolts to). For simplicity, plate is in Y-Z plane (X-thick).
n_idlerbrk = 0
idler_brk = cq.Workplane("YZ").box(5, 30, 30)
for wbb in idler_bbs:
    cx = (wbb[0] + wbb[1]) / 2.0
    cy = (wbb[2] + wbb[3]) / 2.0
    cz = (wbb[4] + wbb[5]) / 2.0
    # Push outward in X (left or right edge of frame)
    nx = cx + (-15 if cx < FRAME_CTR[0] else +15)
    assy.add(idler_brk, name=f"bracket_idler_{n_idlerbrk}", color=IDL_BRK_COLOR,
             loc=Location((nx, cy, cz)))
    n_idlerbrk += 1
    n[0] += 1
print(f"  {n_idlerbrk} idler axle brackets")

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
