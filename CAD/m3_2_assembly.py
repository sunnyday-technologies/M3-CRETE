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
from OCP.gp import gp_GTrsf, gp_Mat, gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform, BRepBuilderAPI_Transform
import os, time, math

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")

# ============================================================
# Helpers
# ============================================================
def load(relpath, base=STEP_DIR):
    return cq.importers.importStep(os.path.join(base, relpath))

def sao(step_file, length, rx=0, ry=0, rz=0):
    """Scale-And-Orient: stretch 1000mm stock to exact length, then bake rotation."""
    stock = cq.importers.importStep(os.path.join(STEP_DIR, "V-Slot", step_file))
    s = stock.val().wrapped
    gt = gp_GTrsf()
    gt.SetVectorialPart(gp_Mat(1,0,0, 0,1,0, 0,0,length/1000.0))
    s = BRepBuilderAPI_GTransform(s, gt, True).Shape()
    for angle, axis in [(rz,(0,0,1)), (ry,(0,1,0)), (rx,(1,0,0))]:
        if angle:
            t = gp_Trsf()
            t.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(*axis)), math.radians(angle))
            s = BRepBuilderAPI_Transform(s, t, True).Shape()
    return cq.Workplane().add(cq.Shape(s))

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

# Corner brackets + gantry plates + motion
cast_corner = load("Brackets/Cast Corner Bracket.step")
cube_con    = load("Brackets/Cube Corner Connector.step")
plate_20_80 = load("Plates/V-Slot Gantry Plate 20-80mm.step")   # 127(X) x 3(Y) x 88(Z)
vwheel      = load("Wheels/Solid V Wheel.step")                 # 10.2(X) x 23.9 x 23.9, axle in X

# ============================================================
# Colors
# ============================================================
ALU = Color(0.78, 0.78, 0.80)   # Frame aluminum (light silver)
BLK = Color(0.15, 0.15, 0.15)   # Gantry beam
DRK = Color(0.55, 0.55, 0.58)   # Z-platform rails
BRK = Color(0.45, 0.45, 0.48)   # Corner brackets (cast)

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
# Real cubes sit INSIDE the T-slot cavities at X-rail butt joints (X=1240).
# Our solid STEP rails have no T-slot channels, so adding cubes creates false clips.
# They remain in the BOM as hidden hardware — rendered only for assembly docs.

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
# 2) Y-RAILS (2x) — custom 1190mm, butt-joint both ends into corner plates
# ------------------------------------------------------------
e_zpyrail = sao(S80, YRAIL_LEN, rx=-90)       # X[-10,10] Y[0,1190] Z[-40,40]
add(e_zpyrail, "zpY_L", DRK, L(ZPY_L_X, YRAIL_TY, ZP))
add(e_zpyrail, "zpY_R", DRK, L(ZPY_R_X, YRAIL_TY, ZP))

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
WHL = Color(0.90, 0.90, 0.82)     # delrin white
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

print(f"  Phase B - Gantry: {n[0]} parts")

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
motor_n23    = load("Electronics/Nema 23 Stepper Motor.step")     # 56.4 x 56.4 x 76.6
gt2_20t      = load("Pulleys/GT2 Timing Pulley 20 Tooth.step")    # 14(X) x 15 x 15
idler_sm     = load("Pulleys/Smooth Idler Pulley Wheel.step")     # 12.7(X) x 22 x 22
# OMC StepperOnline ST-M2 NEMA 23 L-bracket (alloy steel).
# Vendor-provided CAD — see CAD/Vendor/StepperOnline/README.md for license note.
n23_lbracket = cq.importers.importStep(os.path.join(
    os.path.dirname(__file__), "Vendor", "StepperOnline", "N23_angled_mount.STEP"))

MTR = Color(0.20, 0.20, 0.22)   # motor black
BRK2 = Color(0.35, 0.55, 0.80)  # L-bracket blue (matches Nick's color-coding)
PUL = Color(0.85, 0.70, 0.15)   # GT2 pulley brass/gold
IDL = Color(0.92, 0.92, 0.92)   # smooth idler white/polished

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
Z_MOTOR_CZ = 1165          # motor + bracket center Z (body inside frame Z<1200)

# Per-post config:
#   bkt_tx, bkt_ry, bkt_rx — bracket Location rotations
#   mot_tx, mot_ry          — motor  Location rotations (rx always 0)
#   pul_tx                   — pulley X translation (pulley center - 7)
Z_MOTOR_CFG = [
    # name, bkt_tx, bkt_ry, bkt_rx, mot_tx, mot_ry, pul_tx, ty
    ("FL",    129,    -90,      0,   63.2,    -90,    45.9, Z_BELT_Y_F),
    ("FR",   2351,     90,      0, 2416.8,     90,  2420.1, Z_BELT_Y_F),
    ("RL",     60,    -90,    180,   63.2,    -90,    45.9, Z_BELT_Y_R),
    ("RR",   2420,     90,    180, 2416.8,     90,  2420.1, Z_BELT_Y_R),
]

for post_nm, btx, bry, brx, mtx, mry, pltx, ty in Z_MOTOR_CFG:
    add(n23_lbracket, f"z_bracket_{post_nm}", BRK2,
        L(btx, ty, Z_MOTOR_CZ, ry=bry, rx=brx))
    add(motor_n23,    f"z_motor_{post_nm}",   MTR,
        L(mtx, ty, Z_MOTOR_CZ, ry=mry))
    add(gt2_20t,      f"z_pulley_{post_nm}",  PUL,
        L(pltx, ty, Z_MOTOR_CZ))

print(f"  Phase C.1 Z-motors: {n[0]} parts")

# ============================================================
# C.2 — Z-IDLERS at post bottoms (4x smooth idlers)
# ============================================================
# Each Z-belt loop runs from the motor pulley at the top of the post down
# to a smooth idler at the bottom and back up. The idler rotation axis is
# parallel to X (matches motor) and the idler sits directly below its motor
# pulley so both belt strands are vertical.
#
# Mounting: M5 shoulder bolt through the post's inner X-face T-slot.
#   - Bolt head inside the frame, shoulder extends inward to carry the
#     idler pulley bore at X = pulley_center.
#   - No dedicated idler mount plate — T-slot mount is sufficient for a
#     12.7 mm smooth idler wheel. Shoulder bolt hardware is in the BOM.
#
# Placement: idler X,Y = motor pulley X,Y so belt strands are parallel to Z.
# Idler Z = 60 mm (clear of bottom skids at Z[0,40], leaves room for belt
# wrap and Z-carriage lower travel).
#
# Idler native: 12.7(X, axle) x 22(Y) x 22(Z)
IDLER_Z = 60
# (name, idler_cx, idler_cy)
Z_IDLER_CFG = [
    ("FL",   52.9,   Z_BELT_Y_F),
    ("FR", 2427.1,   Z_BELT_Y_F),
    ("RL",   52.9,   Z_BELT_Y_R),
    ("RR", 2427.1,   Z_BELT_Y_R),
]
for nm, ix, iy in Z_IDLER_CFG:
    add(idler_sm, f"z_idler_{nm}", IDL, L(ix, iy, IDLER_Z))

print(f"  Phase C.2 Z-idlers: {n[0]} parts")

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
        ("z_motor_",  "z_bracket_"),# Z-motor body sits inside L-bracket envelope
        ("z_motor_",  "z_pulley_"), # Z-pulley mounted on motor shaft
        ("z_bracket_","topX_"),     # Bracket flange rests on top X-rail
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
