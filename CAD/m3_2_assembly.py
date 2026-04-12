#!/usr/bin/env python3
"""
M3-CRETE M3-2 Assembly — v0.3.0 (CLEAN REWRITE)

Architecture follows the official render on m3-crete.com:
  - Wider-than-deep cuboidal frame (2480 x 1240 x 1200mm outer)
  - Top ring: closed rectangle of 2080 rails (4 X-rails spliced + 2 Y-rails)
  - Bottom: 2 Y-skids only (open front/rear for print-over)
  - 4 posts (2040) at corners
  - Z-motors at BOTTOM of posts
  - Gantry = rectangular sub-frame riding 4 Z-posts:
      * 4 corner gantry plates (one per post, ride vertically)
      * 2 Y-rails (2080) span front-to-back on left + right sides
      * 1 X-beam (2080, 2x 1200mm spliced) spans between Y-rails via end plates

Extrusions: ALL 1200mm standard stock. X uses splicing.
Corner convention: rails butt at inside post faces (standard V-slot practice).
                   Rails and posts occupy disjoint volumes at every corner.

Build phases (commented sections):
  Phase A — Frame (posts + top ring + bottom skids + corner brackets)
  Phase B — Z-platform gantry (plates + Y-rails + X-beam)
  Phase C — Motion (V-wheels + motors + pulleys + idlers + belts)

Rebuild:  cad_venv/Scripts/python.exe CAD/m3_2_assembly.py
Preview:  cad_venv/Scripts/cq-editor.exe CAD/m3_2_assembly.py
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

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")
USER_STEP = os.path.join(os.path.dirname(__file__), "M3-2_Assembly_user.step")

# ============================================================
# Helpers
# ============================================================
def load(relpath, base=STEP_DIR):
    return cq.importers.importStep(os.path.join(base, relpath))

# Cache for expensive STEP imports (don't re-read the user file N times)
_STEP_CACHE = {}
def _cached_solids(step_path):
    if step_path not in _STEP_CACHE:
        _STEP_CACHE[step_path] = cq.importers.importStep(step_path).val().Solids()
    return _STEP_CACHE[step_path]

def load_solids_by_size(step_path, size_target, tol=0.5):
    """Return list of (center, workplane) for every solid whose sorted bbox
    dimensions match size_target within tol."""
    tgt = sorted(size_target)
    out = []
    for s in _cached_solids(step_path):
        bb = s.BoundingBox()
        dims = sorted([bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin])
        if all(abs(d-t) < tol for d, t in zip(dims, tgt)):
            cx=(bb.xmax+bb.xmin)/2; cy=(bb.ymax+bb.ymin)/2; cz=(bb.zmax+bb.zmin)/2
            out.append(((cx, cy, cz), cq.Workplane().add(cq.Shape(s.wrapped))))
    return out

def assign_by_nearest(solids, labeled_centers):
    """Match each label in labeled_centers dict to the nearest-unassigned solid
    from `solids`. Returns dict label -> (actual_center, workplane).
    Used when we know roughly where each labeled part should be and want to
    tolerate any manual drift in the user-edited source file."""
    remaining = list(solids)
    assigned = {}
    for label, target in labeled_centers.items():
        if not remaining:
            raise RuntimeError(f"Ran out of solids while assigning '{label}'")
        best_i = min(range(len(remaining)),
                     key=lambda i: sum((remaining[i][0][j]-target[j])**2 for j in range(3)))
        assigned[label] = remaining.pop(best_i)
    return assigned

_profile_cache = {}

def _discretize_wire(wire, deflection=1.0):
    """Convert a wire's curves to straight-line segments for compact STEP output."""
    pts = []
    for edge in cq.Wire(wire).Edges():
        adaptor = BRepAdaptor_Curve(edge.wrapped)
        disc = GCPnts_TangentialDeflection(adaptor, deflection, 0.1)
        for i in range(1, disc.NbPoints() + 1):
            p = disc.Value(i)
            pts.append((p.X(), p.Y(), p.Z()))
    # Deduplicate consecutive coincident points
    clean = [pts[0]]
    for p in pts[1:]:
        if any(abs(p[j] - clean[-1][j]) > 1e-6 for j in range(3)):
            clean.append(p)
    # Build polyline wire
    wb = BRepBuilderAPI_MakeWire()
    for i in range(len(clean)):
        p1 = gp_Pnt(*clean[i])
        p2 = gp_Pnt(*clean[(i + 1) % len(clean)])
        wb.Add(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
    return wb.Wire()

def sao(step_file, length, rx=0, ry=0, rz=0):
    """V2: extract OUTER profile wire from stock STEP end face, discretize
    curves to line segments, fill solid (no internal cavities), extrude.
    Full V-groove/T-slot opening detail at ~30 faces per extrusion."""
    if step_file not in _profile_cache:
        stock = cq.importers.importStep(os.path.join(STEP_DIR, "V-Slot", step_file))
        end_face = stock.faces("<Z").val()
        outer_wire = _discretize_wire(end_face.outerWire().wrapped)
        solid_face = BRepBuilderAPI_MakeFace(outer_wire).Face()
        _profile_cache[step_file] = solid_face
    face = _profile_cache[step_file]
    prism = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, length))
    result = cq.Workplane().add(cq.Shape(prism.Shape()))
    return rotate_shape(result, rx=rx, ry=ry, rz=rz)

def L(x=0, y=0, z=0, rx=0, ry=0, rz=0):
    l = Location((x, y, z))
    if rz: l = l * Location((0,0,0),(0,0,1),rz)
    if ry: l = l * Location((0,0,0),(0,1,0),ry)
    if rx: l = l * Location((0,0,0),(1,0,0),rx)
    return l

def rotate_shape(shape, rx=0, ry=0, rz=0):
    """Bake rotations into a shape at origin (rotation order: rz, then ry, then rx).
    Use this when a two-axis rotation is needed and L()'s rx-first order is wrong."""
    s = shape.val().wrapped if hasattr(shape, 'val') else shape.wrapped
    for angle, axis in [(rz,(0,0,1)), (ry,(0,1,0)), (rx,(1,0,0))]:
        if angle:
            t = gp_Trsf()
            t.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(*axis)), math.radians(angle))
            s = BRepBuilderAPI_Transform(s, t, True).Shape()
    return cq.Workplane().add(cq.Shape(s))

# ============================================================
# Dimensions (mm) — from 1200mm stock
# ============================================================
# Posts: 2040 rotated rz=90 → 40mm(X) x 20mm(Y) x 1200mm(Z)
# Top rails: 2080 → 20mm in narrow, 80mm in tall direction
POST_X = 40   # post profile X dimension (rotated 2040)
POST_Y = 20   # post profile Y dimension
RAIL_W = 20   # 2080 narrow dimension
RAIL_H = 80   # 2080 tall dimension

# X-rails: 2x 1200mm butt-spliced → rail run = 2400mm between inside post faces
# Frame outer X = 2400 + 2*POST_X = 2480mm
X_RAIL_LEN = 1200
X_INNER = 2 * X_RAIL_LEN        # 2400 — between inside post X-faces
W = X_INNER + 2 * POST_X        # 2480 — outer X

# Y-rails: 1x 1200mm → rail run = 1200mm between inside post faces
# Frame outer Y = 1200 + 2*POST_Y = 1240mm
Y_RAIL_LEN = 1200
Y_INNER = Y_RAIL_LEN            # 1200 — between inside post Y-faces
D = Y_INNER + 2 * POST_Y        # 1240 — outer Y

# Posts: 1200mm vertical
POST_LEN = 1200
H = POST_LEN                    # 1200 — outer Z

# Post center coordinates (each post at its outside corner, inset by half profile)
# Post profile X=40, Y=20 → center at (POST_X/2, POST_Y/2) from the outside corner
FL = (POST_X/2,          POST_Y/2)           # ( 20,   10)
FR = (W - POST_X/2,      POST_Y/2)           # (2460,  10)
RL = (POST_X/2,          D - POST_Y/2)       # ( 20, 1230)
RR = (W - POST_X/2,      D - POST_Y/2)       # (2460, 1230)
POSTS = [("FL",FL),("FR",FR),("RL",RL),("RR",RR)]

# Top ring Z: rails flush with top of posts (rail top face at Z=H=1200)
# Rail 80mm tall, so rail Z center = H - RAIL_H/2 = 1160
TOP_Z = H - RAIL_H/2            # 1160

# Bottom skids: 2040 rails along Y on left + right sides
# Bottom face at floor (Z=0). 2040 is 40mm in Z when lying flat → center Z = 20
BOT_Z = POST_X/2                # 20

# Gantry sub-frame Z (Phase B). Representative.
ZP = 440                        # Z-platform representative height

print("M3-CRETE M3-2 Assembly v0.3.0")
print(f"Frame envelope: {W} x {D} x {H} mm")
print(f"Print volume (hopeful): {X_INNER-80} x {Y_INNER-200} x {H-200} mm")
print("=" * 60)
t0 = time.time()

# ============================================================
# Load stock shapes
# ============================================================
S40 = "V-Slot 20x40x1000 Linear Rail.step"
S80 = "V-Slot 20x80x1000 Linear Rail.step"

# Post: 2040, upright (native Z-oriented), rz=90 so 40mm is in X
# Native: X[-10,10] Y[-20,20] Z[0,1000]. After rz=90: X[-20,20] Y[-10,10] Z[0,1000]
# After scaling Z to POST_LEN: X[-20,20] Y[-10,10] Z[0,POST_LEN]
e_post = sao(S40, POST_LEN, rz=90)

# Top X-rail: 2080, lying along X, 80mm tall (in Z)
# Native: X[-10,10] Y[-40,40] Z[0,1200]. ry=90: X[0,1200] Y[-40,40] Z[-10,10]
# Then rz=90: X[0,1200] Y[-10,10] Z[-40,40]. 20mm in Y, 80mm in Z. ✓
e_xrail = sao(S80, X_RAIL_LEN, ry=90, rz=90)

# Top Y-rail: 2080, lying along Y, 80mm tall (in Z)
# Native: X[-10,10] Y[-40,40] Z[0,1200]. rx=-90: X[-10,10] Y[0,1200] Z[-40,40]
# 20mm in X, 80mm in Z. ✓
e_yrail = sao(S80, Y_RAIL_LEN, rx=-90)

# Bottom skid: 2040, lying along Y, 40mm tall (in Z)
# Native: X[-10,10] Y[-20,20] Z[0,1200]. rx=-90: X[-10,10] Y[0,1200] Z[-20,20]
# 20mm in X, 40mm in Z. ✓
e_skid = sao(S40, Y_RAIL_LEN, rx=-90)

# V-wheel: revolved V-groove profile matching V-slot rail geometry.
# Cross-section in XZ plane (X = axle direction, Z = radial distance).
vwheel = (cq.Workplane("XZ")
    .moveTo(-5.1, 9.8)      # outer left edge (angled)
    .lineTo(-3.0, 11.95)    # join outer rim
    .lineTo( 3.0, 11.95)    # outer rim
    .lineTo( 5.1, 9.8)      # outer right edge (angled)
    .lineTo( 5.1, 8.0)      # inner right flange
    .lineTo( 0.5, 8.0)      # step to bore
    .lineTo( 0.5, 7.0)      # bore right
    .lineTo(-0.5, 7.0)      # bore left
    .lineTo(-0.5, 8.0)      # step from bore
    .lineTo(-5.1, 8.0)      # inner left flange
    .close()
    .revolve(360, (0, 0, 0), (1, 0, 0)))

# Gantry plate: 127x3x88 box with all mounting holes drilled through.
# Hole positions extracted from Components/Plates/V-Slot Gantry Plate 20-80mm.step.
# Gantry plate: 127x3x88 with filleted corners + key alignment holes.
def _make_gantry_plate():
    plate = (cq.Workplane("XZ")
             .rect(127, 88)
             .extrude(3)
             .edges("|Y").fillet(3))         # 3mm corner radius
    for diam, coords in [
        (7.10, [(-49.85,-30.32),(-49.85,30.32),(-29.91,-30.32),(-29.91,30.32)]),
        (6.00, [(-62.41,-42.91),(-62.41,42.91),(62.41,-42.91),(62.41,42.91)]),
        (5.00, [(-11.59,-30.32),(-11.59,30.32),(11.59,-30.32),(11.59,30.32)]),
        (3.00, [(-24.20,-38),(-24.20,38),(-15.80,-38),(-15.80,38),
                (-4.20,-38),(-4.20,38),(4.20,-38),(4.20,38),
                (15.80,-38),(15.80,38),(24.20,-38),(24.20,38)]),
    ]:
        plate = (plate.faces(">Y").workplane(centerOption="CenterOfBoundBox")
                 .pushPoints(coords)
                 .hole(diam, 3))
    return plate

plate_20_80 = _make_gantry_plate()

# ============================================================
# Colors
# ============================================================
# Brand color scheme — black anodized frame, lime green accent
ALU = Color(0.10, 0.10, 0.12)   # Black anodized frame rails
BLK = Color(0.08, 0.08, 0.10)   # Gantry beam (darkest)
DRK = Color(0.20, 0.20, 0.22)   # C-beam Y-rails (dark charcoal)
BRK = Color(0.35, 0.35, 0.38)   # Corner brackets
GRN = Color(0.40, 0.85, 0.10)   # Lime green V-wheels (brand accent)
PH  = Color(0.25, 0.75, 0.90)   # Printhead placeholder (cyan callout)

assy = Assembly("M3-2_Assembly")
n = [0]
def add(s, nm, c, l):
    assy.add(s, name=nm, color=c, loc=l); n[0] += 1

# ============================================================
# PHASE A — FRAME
# ============================================================
# 4 posts at corners
for nm, (cx, cy) in POSTS:
    add(e_post, f"post_{nm}", ALU, L(cx, cy, 0))

# Top X-rails: front pair at Y=POST_Y/2=10, rear pair at Y=D-POST_Y/2=1230
# Spliced at X=1200 (middle). Each rail segment = 1200mm, placed at X=40 and X=1240
# so the pair spans X[40, 2440] — inside post X-faces.
for side, cy in [("F", FL[1]), ("B", RL[1])]:
    add(e_xrail, f"topX_{side}1", ALU, L(POST_X,                cy, TOP_Z))
    add(e_xrail, f"topX_{side}2", ALU, L(POST_X + X_RAIL_LEN,   cy, TOP_Z))

# Top Y-rails: left at X=10, right at X=2470. Single 1200mm each.
# Span Y[POST_Y, POST_Y + 1200] = Y[20, 1220] — inside post Y-faces.
for side, cx in [("L", FL[0]), ("R", FR[0])]:
    add(e_yrail, f"topY_{side}", ALU, L(cx, POST_Y, TOP_Z))

# Bottom Y-skids: left + right. Only these — no front/rear bottom rail (open for printing)
for side, cx in [("L", FL[0]), ("R", FR[0])]:
    add(e_skid, f"botY_{side}", ALU, L(cx, POST_Y, BOT_Z))

# Splice cube connectors: omitted from visualization.
# Splice cube connectors at X-rail butt joints (X=1240, where 2x1200mm meet).
# 20x20x20mm aluminum cubes, 4 total (front-top, front-bottom, rear-top, rear-bottom).
CUBE = Color(0.65, 0.65, 0.68)
cube_con = cq.Workplane("XY").box(20, 20, 20)
SPLICE_X = POST_X + X_RAIL_LEN   # 1240
for side, cy in [("F", FL[1]), ("B", RL[1])]:
    add(cube_con, f"splice_{side}", CUBE, L(SPLICE_X, cy, TOP_Z))

print(f"  Phase A - Frame: {n[0]} parts")

# ============================================================
# PHASE B — Z-PLATFORM GANTRY (butt-joint convention, per Mini V actuator ref)
# ============================================================
# Architecture: rigid rectangular sub-frame that rides vertically on 4 posts.
#   - 4 Z-corner plates: ride each post via wheels on post narrow faces
#                        (modeled without wheels in Phase B; wheels in Phase C)
#   - 2 Y-rails (2080, custom-cut 1190mm): butt-joint front/rear into
#                                          Z-corner plates' Y-inward face
#   - 2 X-beam carriage plates: ride each Y-rail (single-sided, per reference)
#   - 1 X-beam (2080, 2x 1200mm spliced): butt-joint into X-beam carriage plates
#
# Butt-joint convention: the moving extrusion's END FACE touches the plate
# face; screws go through the plate into the extrusion end tap. A 2mm
# plate-to-rail clearance is used where plates slide along a rail (per
# reference Mini V actuator plate X[136.7,139.7] vs rail X[141.7,161.7]).
#
# V-wheel geometry follows the Mini V Belt and Pinion Actuator 500mm
# reference exactly:
#   - Wheel X center = rail X center (wheel centered on rail width in thickness)
#   - Wheel pair spans perpendicular to plate thickness direction with
#     V-groove engaging rail slot face ~2mm deep
#   - Wheel pair spacing along travel axis = 66mm (±33mm from plate center)
#
# Mid-gantry representative position: ZP=440, BEAM_Y=620 (mid-travel).

# --- Geometry constants ---
PLATE_GAP    = 2           # mm — plate ↔ rail running clearance (ref: 2mm)
YRAIL_INSET  = 5           # mm — Y-rail inboard of post centerline
                           # (picks up the 10mm Phase C Y-rail ↔ carriage budget
                           #  AND lets the X-beam hit exactly 2 x 1200mm)
YRAIL_LEN    = D - 2*POST_Y - 2*(PLATE_GAP + 3)  # 1190 mm custom cut

# Y-rail X centerlines (5 mm inboard of post X centers)
ZPY_L_X = POST_X/2 + YRAIL_INSET              # 25
ZPY_R_X = W - POST_X/2 - YRAIL_INSET          # 2455

# Front/rear Z-corner plate Y translation (ty). Native Y[0,3]; after ry=90
# the 3mm thickness stays in Y. Plates seat 2mm off the post inside face.
#   FL/FR plates seat on post +Y (inside) face at Y=POST_Y → Y[22,25]
#   RL/RR plates seat on post -Y (inside) face at Y=D-POST_Y → Y[1215,1218]
ZCPLT_TY_F = POST_Y + PLATE_GAP               # 22
ZCPLT_TY_R = D - POST_Y - PLATE_GAP - 3       # 1215

# Y-rail butt-joint Y coordinates — rail end faces touch Z-corner plate faces
YRAIL_TY = ZCPLT_TY_F + 3                     # 25 (front end at rear face of front plate)

# X-beam Z (beam centered on gantry plate center — beam fits inside 88mm plate Z envelope)
BEAM_Z = ZP
BEAM_Y = D / 2                                # 620 — mid-Y travel

# ------------------------------------------------------------
# 1) Z-CORNER PLATES (4x) — ride posts, host Y-rails via butt-joint
# ------------------------------------------------------------
# Native plate: 127(X) x 3(Y) x 88(Z)
# After ry=90:  88(X)  x 3(Y) x 127(Z)   — 88 along 40mm post face ✓
for nm, (cx, _) in POSTS:
    ty = ZCPLT_TY_F if nm.startswith("F") else ZCPLT_TY_R
    add(plate_20_80, f"zpl_{nm}", DRK, L(cx, ty, ZP, ry=90))

# ------------------------------------------------------------
# 2) Y-RAILS (2x) — parametric C-Beam 40x80x1200 with channel cutout
# ------------------------------------------------------------
# OpenBuilds C-Beam profile: 40mm wide (X) x 80mm tall (Z) with a central
# channel 20mm wide x 40mm deep on one face. The Y-axis belt routes inside
# this channel. Parametrized here as a simple box + rectangular cut rather
# than loading the detailed NURBS geometry from Fusion (~20 MB per beam saved).
# C-Beam Y-rails: extract end-face profile from _user.step C-beam, then
# extrude to 1200mm. This gives full channel/slot detail without importing
# the heavy Fusion BREP.
CBEAM_L = 1200

def _extract_cbeam_profile():
    """Find the C-beam solid in _user.step, extract its front end face's OUTER
    wire, discretize to line segments, build a solid face, return it."""
    solids = load_solids_by_size(USER_STEP, (40, 80, 1200))
    if not solids:
        raise RuntimeError("No C-beam (40x80x1200) found in USER_STEP")
    _, sh = solids[0]
    end_face = sh.faces("<Y").val()
    outer_wire = _discretize_wire(end_face.outerWire().wrapped)
    return BRepBuilderAPI_MakeFace(outer_wire).Face()

_cbeam_face = _extract_cbeam_profile()
_cbeam_prism = BRepPrimAPI_MakePrism(_cbeam_face, gp_Vec(0, CBEAM_L, 0))
e_cbeam = cq.Workplane().add(cq.Shape(_cbeam_prism.Shape()))

# Left rail: C-beam front face at Y=20 (post inner face), centered XZ at rail pos.
# The extracted profile's origin is at the loaded C-beam's front face position.
# We need to translate so the beam sits at canonical (X=15ctr, Y[20,1220], Z[400,480]).
_cb_bb = e_cbeam.val().BoundingBox()
_cb_dx = (ZPY_L_X - 10) - _cb_bb.xmin    # shift X so xmin = -5 (center=15, half-width=20)
_cb_dy = POST_Y - _cb_bb.ymin             # shift Y so ymin = 20
_cb_dz = (ZP - 40) - _cb_bb.zmin          # shift Z so zmin = 400

add(e_cbeam, "zpY_L", DRK, L(_cb_dx, _cb_dy, _cb_dz))

# Right rail: mirror across X center of frame (X = W/2 = 1240)
e_cbeam_r = e_cbeam.mirror("YZ")
_cbr_bb = e_cbeam_r.val().BoundingBox()
_cbr_dx = (ZPY_R_X + 10) - _cbr_bb.xmax + 40  # shift X so center = 2465
_cbr_dy = _cb_dy
_cbr_dz = _cb_dz
add(e_cbeam_r, "zpY_R", DRK, L(_cbr_dx, _cbr_dy, _cbr_dz))

# ------------------------------------------------------------
# 3) X-BEAM CARRIAGE PLATES (2x) — single-sided on Y-rail inner X face
# ------------------------------------------------------------
# After rz=90: native 127(X) x 3(Y) x 88(Z) → X[-3,0] Y[-63.5,63.5] Z[-44,44]
# Translation tx sets plate X_max. L_plate X[tx-3, tx]; R_plate X[tx-3, tx].
#
# Left rail X[ZPY_L_X - 10, ZPY_L_X + 10] = [15, 35]
#   Plate on +X (inner) side: rail-facing face -X at 35 + gap = 37, so tx = 40
#     → plate X[37, 40], plate +X face at 40 ← X-beam butt joint here
# Right rail X[2445, 2465]
#   Plate on -X (inner) side: rail-facing face +X at 2445 - gap = 2443, so tx = 2443
#     → plate X[2440, 2443], plate -X face at 2440 ← X-beam butt joint here
XCAR_L_TX = ZPY_L_X + RAIL_W/2 + PLATE_GAP + 3    # 40
XCAR_R_TX = ZPY_R_X - RAIL_W/2 - PLATE_GAP        # 2443
# Plate orientation: 127mm in Z (spans 80mm Y-rail + wheel clearance),
# 88mm in Y (travel direction), 3mm in X (thickness, parallel to rail X-face).
# Applied via rotate_shape() because L() can't do rz-then-rx in that order.
xcar_plate = rotate_shape(plate_20_80, rz=90, rx=90)  # X[-3,0] Y[-44,44] Z[-63.5,63.5]
add(xcar_plate, "xcar_L", DRK, L(XCAR_L_TX, BEAM_Y, ZP))
add(xcar_plate, "xcar_R", DRK, L(XCAR_R_TX, BEAM_Y, ZP))

# ------------------------------------------------------------
# 4) X-BEAM (2x 1200mm spliced) — butt-joints both carriage plates
# ------------------------------------------------------------
# Beam X range [40, 2440] = exactly 2400mm = 2 x 1200mm ✓
# Cross-section (ry=90, rz=90): X[0,L] Y[-10,10] Z[-40,40] — 20 wide Y, 80 tall Z
# Beam Y[BEAM_Y-10, BEAM_Y+10] = [610, 630] (inside plate Y[556.5, 683.5])
# Beam Z[BEAM_Z-40, BEAM_Z+40] = [400, 480] (inside plate Z[396, 484])
e_gbeam = sao(S80, X_RAIL_LEN, ry=90, rz=90)
add(e_gbeam, "gantry_1", BLK, L(XCAR_L_TX,               BEAM_Y, BEAM_Z))
add(e_gbeam, "gantry_2", BLK, L(XCAR_L_TX + X_RAIL_LEN,  BEAM_Y, BEAM_Z))

# ------------------------------------------------------------
# 5) V-WHEELS on X-beam Y-carriages (8x: 4 per rail)
# ------------------------------------------------------------
# Per Mini V Belt and Pinion Actuator 500mm reference:
#   - Wheel X center = rail X center (wheel thickness centered on rail width)
#   - Wheels straddle the 80mm face in Z (pair at rail Z_center ± 50)
#     → wheel Z center 10mm past rail 80mm face edge, engages face V-slot
#     → reference Mini V uses 40mm face with ±30 offset; we scale to 80mm → ±50
#   - Wheel pair spacing along travel axis Y = 66mm (±33mm from BEAM_Y)
#
# Wheel native: 10.2(X) x 23.9(Y) x 23.9(Z), axle in X. Rolls in Y ✓
WHL = GRN                          # lime green V-wheels (brand accent)
WHEEL_DZ = 50                     # offset from rail Z center (80mm face + 10mm past edge)
WHEEL_DY = 33                     # half of 66mm pair spacing along travel

for side, rx in [("L", ZPY_L_X), ("R", ZPY_R_X)]:
    for dy_name, dy in [("fr", -WHEEL_DY), ("rr", +WHEEL_DY)]:
        for dz_name, dz in [("top", +WHEEL_DZ), ("bot", -WHEEL_DZ)]:
            add(vwheel, f"vw_xc_{side}_{dy_name}_{dz_name}",
                WHL, L(rx, BEAM_Y + dy, ZP + dz))

# ------------------------------------------------------------
# 6) V-WHEELS on Z-corner carriages (16x: 4 per post)
# ------------------------------------------------------------
# Each Z-corner plate rides its post by gripping the two narrow 20mm X-faces
# (X=cx-20 and X=cx+20). 4 wheels per plate in a 2x2 (X-side x Z-level) pattern.
#
# Wheel orientation: rz=90 puts axle in Y → wheel rolls along post Z axis,
# V-groove engages X-normal V-slot on the post's narrow face.
#   Native:        X[-5.1, 5.1]    Y[-11.95, 11.95] Z[-11.95, 11.95]
#   After rz=90:   X[-11.95, 11.95] Y[-5.1, 5.1]    Z[-11.95, 11.95]
#
# Wheel center X = post_cx ± 30  → 10mm past post narrow-face V-slot
# Wheel center Y = plate mid-Y    → wheel hub centered on 3mm plate thickness
# Wheel center Z = ZP ± 33        → standard 66mm pair spacing along travel
WHEEL_ZC_DX = 30                 # offset from post X center (post 20mm + 10mm clearance)
WHEEL_ZC_DZ = 33                 # half of 66mm Z-pair spacing
# Wheel Y = POST Y-center so the V-groove engages the V-rail running along the
# post's narrow X-face (slot centered on post Y mid-line). Prior placement at
# the plate mid-thickness was wrong — confirmed in M3-2_Assembly_user.step edit.
ZC_WHEEL_Y_F = POST_Y / 2          # 10   — front posts Y center
ZC_WHEEL_Y_R = D - POST_Y / 2      # 1230 — rear posts Y center

for nm, (cx, _) in POSTS:
    wy = ZC_WHEEL_Y_F if nm.startswith("F") else ZC_WHEEL_Y_R
    for xside, dx in [("lt", -WHEEL_ZC_DX), ("rt", +WHEEL_ZC_DX)]:
        for zside, dz in [("top", +WHEEL_ZC_DZ), ("bot", -WHEEL_ZC_DZ)]:
            add(vwheel, f"vw_zc_{nm}_{xside}_{zside}",
                WHL, L(cx + dx, wy, ZP + dz, rz=90))

# ------------------------------------------------------------
# 7) HARDWARE — eccentric spacers, bolts, nuts at each V-wheel
# ------------------------------------------------------------
BRASS = Color(0.80, 0.65, 0.20)    # eccentric spacer brass
STEEL = Color(0.55, 0.55, 0.58)    # bolt/nut steel
SPACER_OD  = 7.1                   # eccentric spacer outer diameter
SPACER_H   = 6.0                   # spacer height
BOLT_D     = 5.0                   # M5 bolt shaft diameter
BOLT_HEAD  = 8.5                   # M5 button head diameter
BOLT_HEAD_H = 2.8                  # M5 button head height
NUT_D      = 8.0                   # M5 nylon lock nut (across flats ≈ 8)
NUT_H      = 5.0                   # M5 lock nut height

# Eccentric spacer: small hex-ish cylinder at each wheel bore
spacer = cq.Workplane("YZ").cylinder(SPACER_H, SPACER_OD / 2)

# X-carriage wheels (axle in X, spacer between plate and wheel)
for side, rx in [("L", ZPY_L_X), ("R", ZPY_R_X)]:
    for dy_name, dy in [("fr", -WHEEL_DY), ("rr", +WHEEL_DY)]:
        for dz_name, dz in [("top", +WHEEL_DZ), ("bot", -WHEEL_DZ)]:
            wn = f"hw_xc_{side}_{dy_name}_{dz_name}"
            add(spacer, f"{wn}_spc", BRASS, L(rx, BEAM_Y + dy, ZP + dz))

# Z-carriage wheels (axle in Y after rz=90)
spacer_y = cq.Workplane("XZ").cylinder(SPACER_H, SPACER_OD / 2)
for nm, (cx, _) in POSTS:
    wy = ZC_WHEEL_Y_F if nm.startswith("F") else ZC_WHEEL_Y_R
    for xside, dx in [("lt", -WHEEL_ZC_DX), ("rt", +WHEEL_ZC_DX)]:
        for zside, dz in [("top", +WHEEL_ZC_DZ), ("bot", -WHEEL_ZC_DZ)]:
            wn = f"hw_zc_{nm}_{xside}_{zside}"
            add(spacer_y, f"{wn}_spc", BRASS, L(cx + dx, wy, ZP + dz))

# No limit switches — M3-CRETE uses TMC5160 StallGuard for sensorless homing.

print(f"  Phase B - Gantry + hardware: {n[0]} parts")

# ============================================================
# PHASE C — MOTION
# ============================================================
# Nick's constraints (2026-04-10 review):
#   - Z-motors TOP of posts, idlers BOTTOM — mud protection.
#   - All motor & idler rotation axes parallel to X-axis.
#   - ALL motion hardware inside the frame envelope (X[0,2480] Y[0,1240] Z[0,1200])
#     to prevent damage at construction sites.
#   - Y-motors at REAR of Y-rails.
#   - Stock NEMA23 mount plate used directly; belt-to-carriage via 3D-printed L-tabs.

# --- Load motion components ---
# motor_n23 and gt2_20t are not used in lite — motors + pulleys are parametric boxes
idler_sm     = cq.Workplane("YZ").cylinder(12.7, 22 / 2)   # axle X, OD 22
# OMC StepperOnline ST-M2 NEMA 23 L-bracket (alloy steel).
# Vendor-provided CAD — see CAD/Vendor/StepperOnline/README.md for license note.
n23_lbracket = cq.importers.importStep(os.path.join(
    os.path.dirname(__file__), "Vendor", "StepperOnline", "N23_angled_mount.STEP"))

MTR = Color(0.15, 0.15, 0.18)   # motor black
BRK2 = Color(0.30, 0.50, 0.75)  # L-bracket blue (brand secondary)
PUL = Color(0.90, 0.75, 0.10)   # GT2 pulley brass/gold
IDL = Color(0.85, 0.85, 0.88)   # smooth idler polished steel

# ============================================================
# C.1 — Z-MOTORS + ANGLED L-BRACKETS + PULLEYS (4x each, 12 parts)
# ============================================================
# Per Nick's 2026-04-11 update:
#   - Stock NEMA23 mount plate REJECTED — could not clamp to frame corner
#   - Replaced by N23_angled_mount.STEP: 65(X) x 69(Y) x 69(Z) L-bracket
#   - Bracket sits ON TOP of the frame, flange against front/rear top X-rail
#   - Motor body mostly inside the bracket envelope, shaft points TOWARD post
#   - Motor + bracket entirely below Z=1200 (top of frame), so the whole
#     mechanism stays inside the frame envelope as required for transport.
#
# Bracket geometry (native):
#   X[-32.5, 32.5] — bilaterally symmetric in local X (width axis)
#   Y[-40, 29]     — asymmetric: flange extends toward Y=-40, wall rises at Y>0
#   Z[0, 69]       — flange at Z=0, motor mount face at top of 69mm rise
#
# Front posts: ry=±90 only. Flange native Y=-40 → world Y near post front rail.
# Rear posts: ry=±90 + rx=180. rx=180 flips native Y→-Y and Z→-Z, which swaps
#   the flange direction so it touches the REAR top X-rail instead of front.
#
# Motor: ry=90 (right, shaft toward +X post) or ry=-90 (left, shaft toward -X post).
# Motor Y-symmetric so no rx needed at rear, just Y translation.
#
# Pulley: native X[0,14], axis = X direction (14mm along shaft). Placed with
# tx = shaft_center - 7 so the pulley is centered on the shaft.

Z_BELT_Y_F = 60            # belt strand Y at front posts (matches Nick's bracket Y center)
Z_BELT_Y_R = D - 60        # = 1180 at rear posts
Z_MOTOR_CZ = 1170          # motor + bracket center Z (all 4 now outboard; bracket top = 1202.5)

# Z-motion parts (brackets + motors + pulleys) are loaded pre-positioned from
# M3-2_Assembly_user.step rather than placed parametrically. Rationale:
#   (1) Nick's Fusion edits rotate parts around their own centers, which can't
#       be cleanly reproduced via L()'s rx-ry-rz-then-translate order.
#   (2) As of 2026-04-11, Nick moved the RL Z-motor ASSEMBLY outside the frame
#       envelope to make room for the Y-motors coming in Phase C.4. Loading
#       from the user file means future manual moves propagate automatically.
# The rough label centers below are used only to map each loaded solid to its
# corner post label; exact positions come from the user file.
# USER_STEP defined at top of file (line 36)

# Combined Z+Y bracket/motor/pulley labels — all 6 share the same sorted
# dimension signatures, so assign_by_nearest needs every expected center
# present as a candidate label, otherwise a Y solid could be mis-mapped into
# a Z slot. Label prefix "Z" vs "Y" routes the loaded solid to the right
# naming + downstream code.
BRACKET_LABELS = {
    "ZFL": (  94.4,  54.5,  Z_MOTOR_CZ),
    "ZFR": (2385.6,  54.5,  Z_MOTOR_CZ),
    "ZRL": (  94.5, 1185.5, Z_MOTOR_CZ),
    "ZRR": (2385.5, 1185.5, Z_MOTOR_CZ),
    "YL":  (  69.7, 1180.3, 441.8),        # Y-motor bracket, rear-left (inside C-beam L)
    "YR":  (2410.5, 1180.5, 445.0),        # Y-motor bracket, rear-right (inside C-beam R)
}
MOTOR_LABELS = {
    "ZFL": (  80.9,   60,   Z_MOTOR_CZ),
    "ZFR": (2399.1,   60,   Z_MOTOR_CZ),
    "ZRL": (  80.9, 1180,   Z_MOTOR_CZ),
    "ZRR": (2399.1, 1180,   Z_MOTOR_CZ),
    "YL":  (  56.1, 1178.8, 441.8),
    "YR":  (2424.1, 1175.0, 445.0),
}
PULLEY_LABELS = {
    "ZFL": (  52.9,   60,   Z_MOTOR_CZ),
    "ZFR": (2427.1,   60,   Z_MOTOR_CZ),
    "ZRL": (  52.9, 1180,   Z_MOTOR_CZ),
    "ZRR": (2427.1, 1180,   Z_MOTOR_CZ),
    "YL":  (  28.1, 1178.8, 441.8),         # inside C-beam L channel
    "YR":  (2452.1, 1175.0, 445.0),         # inside C-beam R channel
}

def _part_name(kind, label):
    """ZFL -> z_<kind>_FL ; YL -> y_<kind>_L"""
    if label.startswith("Z"):
        return f"z_{kind}_{label[1:]}"
    return f"y_{kind}_{label[1:]}"

def _axle_from_bbox(bb, long_dim, tol=0.5):
    """Return 'X'/'Y'/'Z' — whichever bbox dim matches long_dim."""
    dx, dy, dz = bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin
    if abs(dx - long_dim) < tol: return "X"
    if abs(dy - long_dim) < tol: return "Y"
    return "Z"

def _oriented_box(short, short2, long_, axle):
    """Rectangular box with `long_` along the given axle and `short`/`short2`
    on the two perpendicular axes. Centered at origin."""
    if axle == "X":
        return cq.Workplane("XY").box(long_, short, short2)
    if axle == "Y":
        return cq.Workplane("XY").box(short, long_, short2)
    return cq.Workplane("XY").box(short, short2, long_)

def _oriented_cylinder(height, radius, axle):
    """Cylinder with axis along the given axle, centered at origin."""
    if axle == "X":
        return cq.Workplane("YZ").cylinder(height, radius)
    if axle == "Y":
        return cq.Workplane("XZ").cylinder(height, radius)
    return cq.Workplane("XY").cylinder(height, radius)

# L-brackets: parametric boxes, position from loaded _user.step.
for label, (ctr, sh) in assign_by_nearest(
        load_solids_by_size(USER_STEP, (69, 69, 65)), BRACKET_LABELS).items():
    axle = _axle_from_bbox(sh.val().BoundingBox(), 65)
    box = _oriented_box(69, 69, 65, axle)
    add(box, _part_name("bracket", label), BRK2, L(*ctr))

# Motors: 56.4mm square body (56mm deep) + 8mm shaft cylinder.
# Body is offset AWAY from the pulley so the shaft/pulley are visible.
MOTOR_BODY = 56.0      # body depth along shaft axis (76.6 total - 20.6 shaft)
MOTOR_SHAFT_D = 8.0    # shaft diameter
MOTOR_SHAFT_L = 20.6   # shaft protrusion from body face
SHAFT = Color(0.60, 0.60, 0.62)

# Load pulleys FIRST so we know which direction the shaft points for each motor.
z_pulley_info = {}
y_pulley_info = {}
_pulley_centers = {}   # label -> (cx, cy, cz, axle)
for label, (ctr, sh) in assign_by_nearest(
        load_solids_by_size(USER_STEP, (14, 15, 15)), PULLEY_LABELS).items():
    axle = _axle_from_bbox(sh.val().BoundingBox(), 14)
    cyl = _oriented_cylinder(14, 15 / 2, axle)
    add(cyl, _part_name("pulley", label), PUL, L(*ctr))
    _pulley_centers[label] = (ctr[0], ctr[1], ctr[2], axle)
    if label.startswith("Z"):
        z_pulley_info[label[1:]] = (ctr[0], ctr[1], ctr[2], axle)
    else:
        y_pulley_info[label[1:]] = (ctr[0], ctr[1], ctr[2], axle)

# Now place motor body + shaft for each motor, using pulley position to
# determine shaft direction.
for label, (ctr, sh) in assign_by_nearest(
        load_solids_by_size(USER_STEP, (56.4, 56.4, 76.6)), MOTOR_LABELS).items():
    axle = _axle_from_bbox(sh.val().BoundingBox(), 76.6)
    pctr = _pulley_centers[label]
    # Shaft points from motor center TOWARD the pulley along the axle.
    axis_idx = {"X": 0, "Y": 1, "Z": 2}[axle]
    shaft_dir = 1.0 if pctr[axis_idx] < ctr[axis_idx] else -1.0
    # shaft_dir: +1 means pulley is at lower coord end, -1 means higher end.
    # Actually we want the direction FROM motor TO pulley:
    shaft_dir = -1.0 if pctr[axis_idx] < ctr[axis_idx] else 1.0
    # Body center: shift away from pulley by half the missing length
    body_offset = (76.6 - MOTOR_BODY) / 2 * (-shaft_dir)
    body_ctr = list(ctr)
    body_ctr[axis_idx] += body_offset
    body = _oriented_box(56.4, 56.4, MOTOR_BODY, axle)
    body = body.edges().chamfer(1.5)
    # Locating boss on shaft face (38mm dia, 2mm tall)
    boss = _oriented_cylinder(2, 38 / 2, axle)
    boss_ctr = list(body_ctr)
    boss_ctr[axis_idx] += (MOTOR_BODY / 2 + 1) * shaft_dir
    add(body, _part_name("motor", label), MTR, L(*body_ctr))
    add(boss, _part_name("boss", label), MTR, L(*boss_ctr))
    # Shaft: cylinder from body face toward pulley
    shaft_start = ctr[axis_idx] + (76.6 / 2) * shaft_dir - MOTOR_BODY * shaft_dir
    # Simpler: shaft center = midpoint between body face and bbox shaft-end
    shaft_ctr = list(ctr)
    shaft_ctr[axis_idx] += (76.6 / 2 - MOTOR_SHAFT_L / 2) * shaft_dir
    shaft_cyl = _oriented_cylinder(MOTOR_SHAFT_L, MOTOR_SHAFT_D / 2, axle)
    add(shaft_cyl, _part_name("shaft", label), SHAFT, L(*shaft_ctr))

print(f"  Phase C.1 Z-motors + C.4 Y-motors: {n[0]} parts")

# ============================================================
# C.2 — Z-IDLERS at post bottoms (4x smooth idlers)
# ============================================================
# Parametric: one idler directly under each motor pulley, with rotation axis
# matching the pulley's axis. For FL/FR/RR the pulley axis is X (native); for
# the relocated RL corner the pulley axis is Y (Nick rotated motor 90° around
# Z to get shaft-along-Y when moving the motor outside the frame envelope).
#
# Idler native: 12.7(X, axle) x 22(Y) x 22(Z)
IDLER_Z  = 22     # center Z — idler bottom at 11, top at 33 (flush with frame floor)
PULLEY_R = 6      # GT2 20T pulley effective tangent radius (belt pitch circle)
IDLER_R  = 11     # smooth idler radius

for label, (px, py, pz, axis) in z_pulley_info.items():
    if   axis == "X": idler_shape = idler_sm
    elif axis == "Y": idler_shape = rotate_shape(idler_sm, rz=90)
    else:             idler_shape = rotate_shape(idler_sm, ry=90)
    add(idler_shape, f"z_idler_{label}", IDL, L(px, py, IDLER_Z))

print(f"  Phase C.2 Z-idlers: {n[0]} parts")

# ============================================================
# C.3 — Z-BELTS + L-TABS (4 belt loops + 4 L-tabs)
# ============================================================
# Each Z-axis belt: a GT2 6mm loop running vertically between motor pulley
# (Z=Z_MOTOR_CZ) and bottom idler (Z=IDLER_Z), pinned to the Z-corner plate
# via an L-tab that bridges from the plate face (Y=22/1218) out to the
# belt strand (Y=Z_BELT_Y_F/R = 60/1180). The L-tab is a 3D-printed part.
#
# Belt visualization: 2 strands (front + back of the loop), each modeled as
# a thin 6 x 2 x height rectangular prism. No belt tooth geometry — this is
# purely for clash-detection, CG, and visual clarity, not for FEA. The two
# strands are offset in the belt's own tangent direction (here: ±7mm in X
# centered on the pulley X).
#
# L-tab: 60 x 6 x 30 printed bracket. The 60mm long axis spans the gap from
# plate face (Y ~ 22) to belt strand (Y ~ 60), a 38mm run. The tab bolts to
# the Z-corner plate via two M3 holes and clamps the belt end via a simple
# pin (per Nick's "we will just use a pin attachment for modeling").
# Tab Z thickness = 30mm. Tab mid-Z follows the current ZP=440 representative
# gantry height.

BELT = Color(0.59, 0.84, 0.00)     # M3-CRETE lime green
TAB  = Color(0.70, 0.70, 0.75)     # printed nylon

# Z-belt strands are generated parametrically from the loaded pulley data so
# the ±6.5mm widened gap (matching pulley pitch circle) applies uniformly, and
# the relocated RL strand positions follow the moved RL pulley automatically.
# Belt box orientation matches pulley axis: the 6mm belt width runs along the
# pulley rotation axis, and the 1.5mm thickness is radial.
BELT_W  = 6                        # belt width along pulley rotation axis
BELT_T  = 1.5                      # belt thickness radial from pulley
BELT_Z0 = IDLER_Z + IDLER_R        # 71 (strand bottom tangent to idler)
BELT_Z1 = Z_MOTOR_CZ - PULLEY_R    # 1159 (strand top tangent to pulley)
BELT_H  = BELT_Z1 - BELT_Z0        # 1088

STRAND_HALF_GAP = 6.5               # half of 13mm strand spacing (pulley width)

for label, (px, py, pz, axis) in z_pulley_info.items():
    if axis == "X":
        # Strands separated in Y (tangent to pulley in Y-Z plane)
        # Box: 6(X, along pulley axis) x 1.5(Y, radial) x BELT_H(Z)
        strand = cq.Workplane("XY").box(BELT_W, BELT_T, BELT_H,
                                        centered=(True, True, False))
        offsets = [(0, -STRAND_HALF_GAP), (0, +STRAND_HALF_GAP)]
    elif axis == "Y":
        # Strands separated in X (tangent to pulley in X-Z plane)
        # Box: 1.5(X, radial) x 6(Y, along pulley axis) x BELT_H(Z)
        strand = cq.Workplane("XY").box(BELT_T, BELT_W, BELT_H,
                                        centered=(True, True, False))
        offsets = [(-STRAND_HALF_GAP, 0), (+STRAND_HALF_GAP, 0)]
    else:
        continue  # Z-axis pulley not applicable for Z-motor belts
    for tag, (dx, dy) in zip(("fr", "bk"), offsets):
        add(strand, f"z_belt_{label}_{tag}", BELT,
            L(px + dx, py + dy, BELT_Z0))

# L-tabs removed 2026-04-11: with all 4 Z-motors now outboard, the belt strands
# pass through the Z-corner plates directly, so belt attachment is a clip/clamp
# that bolts through the plate — no separate printed tab needed.

print(f"  Phase C.3 Z-belts: {n[0]} parts")

# ============================================================
# C.4 — Y-AXIS MOTION (2 idlers + 2 belt loops)
# ============================================================
# Y-motor subassemblies (bracket + motor + pulley) are pre-placed in
# _userY.step by Nick, with shaft-along-Z (axle=Z) pointing down and the
# pulley at Z~429 inside the Z-platform Y-rail envelope. From those loaded
# pulley positions we parametrically derive:
#   - 2 Y-idlers at the front end of each rail (Y~20), same X as the
#     pulley, same Z, rotation axis = Z.
#   - 2 horizontal Y-belt loops, each with 2 strands running along Y from
#     rear pulley to front idler, offset ±6.5 mm in X (strand spacing =
#     pulley pitch width).
# Belt length per rail ≈ 2 × (Y_pulley - Y_idler) ≈ 2 × 1160 = 2320 mm.
# Each belt loop is cut by the X-beam carriage plate (intentional clamp
# site — covered by an EXCLUDE_PAIRS entry added below).

Y_IDLER_Y = 32             # inset from front-end by 12mm to clear the front post
Y_BELT_ZC = None           # derived per-rail from pulley center Z

for label, (px, py, pz, axis) in y_pulley_info.items():
    # Expect axis == "Z" (shaft down); guard against accidental re-orientation
    if axis != "Z":
        continue
    # --- Y-idler: 12.7 (Z, axle) x 22 (X) x 22 (Y) ---
    # Start from native idler_sm (axle along X) and rotate 90° around Y
    # to put axle along Z.
    idler_shape = rotate_shape(idler_sm, ry=90)
    add(idler_shape, f"y_idler_{label}", IDL, L(px, Y_IDLER_Y, pz))

    # --- Y-belt strands: 2 parallel horizontal strands along Y ---
    # Axis = Z → strands separated in X, belt width 6mm along Z (axle),
    # radial thickness 1.5mm in X, length in Y.
    belt_len = py - Y_IDLER_Y - PULLEY_R - IDLER_R   # tangent-to-tangent
    strand = cq.Workplane("XY").box(BELT_T, belt_len, BELT_W,
                                    centered=(True, False, True))
    y_start = Y_IDLER_Y + IDLER_R  # front strand end tangent to idler
    for tag, dx in (("lt", -STRAND_HALF_GAP), ("rt", +STRAND_HALF_GAP)):
        add(strand, f"y_belt_{label}_{tag}", BELT,
            L(px + dx, y_start, pz))

print(f"  Phase C.4 Y-motion: {n[0]} parts")

# ============================================================
# C.8 — X-AXIS MOTION (belt-pinion: fixed belt, motor rides along)
# ============================================================
# The X-axis uses a pinion-style drive: a single GT2 belt is fixed at both
# ends of the gantry beam (X-beam). A motor+pulley carriage rides along the
# beam on V-wheels, pushing the pulley against the fixed belt. The motor
# drives itself along the belt, carrying the printhead.
#
# Gantry beam (2080): X[40, 2440], Y[610, 630], Z[400, 480]
# Belt runs along the beam top face (Z=480) at Y=620 (beam center).

X_MOTOR_X    = 2380     # motor position along beam (representative, near RR end)
X_BEAM_Y     = D / 2    # 620 — beam center Y
X_BELT_Z     = ZP + 43  # 483 — just above gantry top face (Z=480)
X_BELT_X0    = 80       # belt start (inset from beam end)
X_BELT_X1    = 2400     # belt end
X_PH_X       = 1240     # printhead placeholder X (mid-beam)

# X-belt: single straight strand (fixed, not a loop)
x_belt_len = X_BELT_X1 - X_BELT_X0
x_belt = cq.Workplane("XY").box(x_belt_len, BELT_W, BELT_T,
                                centered=(False, True, True))
add(x_belt, "x_belt", BELT, L(X_BELT_X0, X_BEAM_Y, X_BELT_Z))

# X-motor: NEMA23 body + boss + shaft + pulley, shaft pointing down (-Z)
x_motor_z = X_BELT_Z + MOTOR_SHAFT_L + MOTOR_BODY / 2
x_motor_body = _oriented_box(56.4, 56.4, MOTOR_BODY, "Z").edges().chamfer(1.5)
add(x_motor_body, "x_motor", MTR, L(X_MOTOR_X, X_BEAM_Y, x_motor_z))
x_boss = _oriented_cylinder(2, 38 / 2, "Z")
add(x_boss, "x_boss", MTR, L(X_MOTOR_X, X_BEAM_Y, X_BELT_Z + MOTOR_SHAFT_L + 1))

x_shaft_z = X_BELT_Z + MOTOR_SHAFT_L / 2
x_shaft = _oriented_cylinder(MOTOR_SHAFT_L, MOTOR_SHAFT_D / 2, "Z")
add(x_shaft, "x_shaft", SHAFT, L(X_MOTOR_X, X_BEAM_Y, x_shaft_z))

x_pulley_z = X_BELT_Z
x_pulley = _oriented_cylinder(14, 15 / 2, "Z")
add(x_pulley, "x_pulley", PUL, L(X_MOTOR_X, X_BEAM_Y, x_pulley_z))

# X-idler at far end of belt
x_idler = rotate_shape(idler_sm, ry=90)
add(x_idler, "x_idler", IDL, L(X_BELT_X0, X_BEAM_Y, X_BELT_Z))

# X-carriage: double-plate anti-racking design (2 plates straddling the gantry beam)
# Plate oriented in YZ plane, riding on gantry beam V-slots.
x_car_plate = rotate_shape(plate_20_80, rz=90, rx=90)
add(x_car_plate, "xcar_x_fr", DRK, L(X_PH_X, X_BEAM_Y - 33, ZP))
add(x_car_plate, "xcar_x_rr", DRK, L(X_PH_X, X_BEAM_Y + 33, ZP))

# 4 V-wheels on X-carriage (2 per plate, riding gantry beam 80mm faces)
for pn, py_off in [("fr", -33), ("rr", +33)]:
    for dz_name, dz in [("top", +WHEEL_DZ), ("bot", -WHEEL_DZ)]:
        add(vwheel, f"vw_x_{pn}_{dz_name}", GRN,
            L(X_PH_X, X_BEAM_Y + py_off, ZP + dz, rz=90))

# Printhead carriage placeholder
ph_box = cq.Workplane("XY").box(80, 80, 30)
add(ph_box, "printhead", PH, L(X_PH_X, X_BEAM_Y, X_BELT_Z + 20))

print(f"  Phase C.8 X-motion: {n[0]} parts")

# ============================================================
# SUMMARY + EXPORT
# ============================================================
total = n[0]
print(f"\n  TOTAL: {total} parts")
print(f"  Generation time: {time.time()-t0:.1f}s")

out = os.path.join(os.path.dirname(__file__), "M3-2_Assembly.step")
print(f"\nExporting {total} parts to STEP...")
t1 = time.time()
assy.save(out)
mb = os.path.getsize(out) / 1024 / 1024
print(f"  {mb:.1f} MB in {time.time()-t1:.1f}s")

# For CQ-Editor live preview: expose the assembly as `result`
result = assy

# ============================================================
# INTERFERENCE CHECK (solid intersection, not just bbox)
# ============================================================
# Only run if invoked as __main__ (skipped in CQ-Editor to keep preview fast).
if __name__ == "__main__":
    print("\nRunning solid interference check...")
    tc = time.time()
    # Flatten assembly into (name, shape_with_location_baked) pairs
    def bake(child, parent_loc=Location()):
        loc = parent_loc * child.loc if child.loc else parent_loc
        results = []
        if child.obj is not None:
            sh = child.obj
            if hasattr(sh, 'val'):
                sh = sh.val()
            try:
                moved = sh.moved(loc)
                results.append((child.name, moved))
            except Exception:
                pass
        for ch in child.children:
            results.extend(bake(ch, loc))
        return results

    baked = bake(assy)
    print(f"  Baked {len(baked)} solids")

    # Intentional overlaps we don't want reported as clips.
    # Each rule: (substr1, substr2) — if both names contain these, skip.
    EXCLUDE_PAIRS = [
        ("vw_xc", "zpY_"),         # X-carriage V-wheels engage Y-rail V-slot (phantom dip)
        ("vw_xc", "xcar_"),        # X-carriage V-wheels mount on carriage plates
        ("vw_zc", "post_"),        # Z-carriage V-wheels engage post V-slots (phantom dip)
        ("vw_zc", "zpl_"),         # Z-carriage V-wheels mount through Z-corner plate
        ("zpl_",  "zpY_"),         # Y-rail butt-joint end face flush with Z-corner plate
        ("xcar_", "gantry_"),      # X-beam butt-joint end face flush with carriage plate
        ("z_motor_",   "z_bracket_"),# Z-motor body sits inside L-bracket envelope
        ("z_motor_",   "z_pulley_"), # Z-pulley mounted on motor shaft
        ("z_bracket_", "topX_"),     # Bracket flange rests on top X-rail
        ("z_belt_",    "z_pulley_"), # Belt wraps pulley
        ("z_belt_",    "z_idler_"),  # Belt wraps idler
        # Parametrized motor body is a full 56.4x76.6x56.4 box, but the real
        # NEMA23 has a stepped shaft end where the belt enters the pulley.
        # The shaft-end volume is phantom; exclude so the belt can pass.
        ("z_motor_",   "z_belt_"),
        # Shaft passes through pulley (mounted on it), bracket (passes through),
        # and adjacent rail geometry.
        ("_shaft_",    "_pulley_"),
        ("_shaft_",    "_bracket_"),
        ("_boss_",     "_bracket_"),
        ("_boss_",     "_shaft_"),
        ("_boss_",     "_motor_"),
        ("_shaft_",    "zpY_"),
        # Post-to-rail/plate butt joints (frame flush contact).
        ("post_",      "zpY_"),
        ("post_",      "zpl_"),
        # X-carriage plate sits on C-beam inner face (butt-joint).
        ("xcar_",      "zpY_"),
        # X-beam (gantry) butt-joints the C-beam.
        ("gantry_",    "zpY_"),
        # Z-belt strands may graze the C-beam corner profile.
        ("z_belt_",    "zpY_"),
        # All 4 Z-motors now outboard: belt strands graze the Z-corner plates
        # at the clamp height. The small overlap is intentional — extra belt
        # length is needed to terminate/clip the belt onto the plate.
        ("z_belt_",    "zpl_"),
        # --- Phase C.4 Y-axis ---
        ("y_motor_",   "y_bracket_"),# Motor body sits inside L-bracket envelope
        ("y_motor_",   "y_pulley_"), # Pulley mounted on motor shaft
        ("y_belt_",    "y_pulley_"), # Belt wraps pulley
        ("y_belt_",    "y_idler_"),  # Belt wraps idler
        ("y_bracket_", "zpY_"),      # Y-bracket bolts to inside face of Z-platform Y-rail
        ("y_motor_",   "zpY_"),      # Y-motor body sits adjacent to the rail
        ("y_pulley_",  "zpY_"),      # Y-pulley sits inside the rail envelope
        # Y-belt runs inside the C-beam channel along the full rail length —
        # intentional routing (the whole point of the C-beam upgrade).
        ("y_belt_",    "zpY_"),
        # Y-idler sits inside the front end of the C-beam channel.
        ("y_idler_",   "zpY_"),
        # Y-pulley sits inside the rear end of the C-beam channel.
        ("y_pulley_",  "zpY_"),
        # Y-motor body is adjacent to / partially inside the C-beam envelope.
        ("y_motor_",   "zpY_"),
        # Y-bracket bolts to the C-beam inside face.
        ("y_bracket_", "zpY_"),
        # Parametric bracket box overlaps adjacent Z-corner plate where the
        # real L-bracket has cutouts. Phantom in lite build.
        ("y_bracket_", "zpl_"),
        # Y-belt crosses under the X-carriage plate clamp site.
        ("y_belt_",    "xcar_"),
        # --- Phase C.8 X-axis ---
        ("x_motor",    "x_shaft"),
        ("x_motor",    "x_pulley"),
        ("x_shaft",    "x_pulley"),
        ("x_belt",     "x_shaft"),
        ("x_belt",     "x_pulley"),
        ("x_belt",     "x_idler"),
        ("x_belt",     "gantry_"),
        ("x_pulley",   "gantry_"),
        ("x_idler",    "gantry_"),
        ("x_shaft",    "gantry_"),
        ("printhead",  "x_belt"),
        ("printhead",  "gantry_"),
        ("printhead",  "xcar_x_"),
        ("xcar_x_",    "gantry_"),
        ("xcar_x_",    "vw_x_"),
        ("xcar_x_",    "x_belt"),
        ("xcar_x_",    "printhead"),
        ("xcar_x_",    "xcar_x_"),
        ("vw_x_",      "gantry_"),
        ("vw_x_",      "printhead"),
        ("_boss_",     "zpY_"),
        ("x_boss",     "x_shaft"),
        ("x_boss",     "x_motor"),
        # Hardware — spacers sit inside wheel bores, bolts through wheels+plates
        ("hw_",        "vw_"),
        ("hw_",        "zpl_"),
        ("hw_",        "xcar_"),
        ("hw_",        "zpY_"),
        ("hw_",        "post_"),
        # Splice cubes sit inside rail T-slot cavities
        ("splice_",    "topX_"),
        ("splice_",    "topY_"),
        # Limit switches mount on rail faces
        ("limit_",     "post_"),
        ("limit_",     "zpY_"),
        ("limit_",     "topX_"),
        ("limit_",     "gantry_"),
    ]
    def excluded(a, b):
        for s1, s2 in EXCLUDE_PAIRS:
            if (s1 in a and s2 in b) or (s1 in b and s2 in a):
                return True
        return False

    clips = []
    excluded_count = 0
    for i in range(len(baked)):
        n1, s1 = baked[i]
        for j in range(i+1, len(baked)):
            n2, s2 = baked[j]
            # Quick bbox prefilter
            b1 = s1.BoundingBox(); b2 = s2.BoundingBox()
            if (b1.xmax < b2.xmin or b2.xmax < b1.xmin or
                b1.ymax < b2.ymin or b2.ymax < b1.ymin or
                b1.zmax < b2.zmin or b2.zmax < b1.zmin):
                continue
            if excluded(n1, n2):
                excluded_count += 1
                continue
            # Real solid intersection
            try:
                inter = s1.intersect(s2)
                vol = inter.Volume()
                if vol > 1.0:   # ignore < 1mm3 numerical noise
                    clips.append((n1, n2, vol))
            except Exception as e:
                pass
    if excluded_count:
        print(f"  (skipped {excluded_count} known-intentional overlaps)")

    print(f"  Check time: {time.time()-tc:.1f}s")
    if clips:
        print(f"\n  [!] {len(clips)} solid interferences found:")
        for n1, n2, vol in sorted(clips, key=lambda c: -c[2]):
            print(f"    {n1:20s} vs {n2:20s}  vol={vol:10.0f} mm3")
    else:
        print("\n  [OK] No solid interferences - all parts occupy disjoint volumes")

print(f"\n  v0.3.0 Phase A+B: Frame + Z-gantry butt-jointed ({total} parts)")
