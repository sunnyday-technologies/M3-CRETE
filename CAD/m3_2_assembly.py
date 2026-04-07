#!/usr/bin/env python3
"""
M3-CRETE M3-2 Assembly — v0.2.0
Full CAD assembly: frame + Z-platform + gantry + motors + V-wheels + pulleys
+ idlers + belt paths + splice connectors + drag chain mounts.
AI-generated from OpenBuilds STEP library + parametric extrusions.

Version history:
  v0.1.0 — Frame structure, Z-platform, gantry beam, motors, plates (40 parts)
  v0.2.0 — V-wheel carriages, GT2 pulleys, idler pulleys, belt paths,
            splice connectors, drag chain mounts (~91 parts)
"""
import cadquery as cq
from cadquery import Assembly, Color, Location
from OCP.gp import gp_GTrsf, gp_Mat, gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform, BRepBuilderAPI_Transform
import os, time, math

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")
ADV_DIR  = os.path.join(os.path.dirname(__file__), "Advanced")

def load(relpath, base=STEP_DIR):
    return cq.importers.importStep(os.path.join(base, relpath))

def sao(step_file, length, rx=0, ry=0, rz=0):
    """Scale-And-Orient: stretch 1000mm STEP to exact length, then bake rotation."""
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

# ============================================================
# Dimensions (mm)
# ============================================================
W=2400; D=1200; H=1200       # External frame envelope
ZP = 440                      # Z-platform representative height
PX=40; PY=20; PT=3            # Post profile (rotated 2040)
S40 = "V-Slot 20x40x1000 Linear Rail.step"
S80 = "V-Slot 20x80x1000 Linear Rail.step"

# V-wheel dimensions (from probe: 10.2 x 23.9 x 23.9, centered at origin)
VW_DIA = 23.9
VW_THK = 10.2
# GT2 pulley: 14.0 x 15.0 x 15.0 (center at 7,0,0 — shaft along X)
# Smooth idler: 12.7 x 22.0 x 22.0 (centered at origin)
# Eccentric spacer: 11.5 x 8.5 x 10.0

print("M3-CRETE M3-2 Assembly v0.2.0")
print("=" * 50)
print("Generating parts...")
t0 = time.time()

# ============================================================
# Load STEP parts — ALL STANDARD 1200mm LENGTHS (no trimming)
# ============================================================
e_post   = sao(S40, 1200, rz=90)           # 40x20x1200 vertical post
e_xrail  = sao(S80, 1200, ry=90, rz=90)    # 1200x20x80 X-running rail
e_ybrace = sao(S40, 1200, rx=-90)           # 20x1200x40 Y-running brace
e_yrail  = sao(S80, 1200, rx=-90)           # 20x1200x80 Y-running rail
e_gbeam  = sao(S80, 1200, ry=90, rz=90)    # 1200x20x80 gantry beam segment

plate    = load("Plates/V-Slot Gantry Plate 20-80mm.step")
motor    = load("Electronics/Nema 23 Stepper Motor.step")
mmount   = load("Plates/Motor Mount Plate Nema 23.step")
vwheel   = load("Wheels/Solid V Wheel.step")
gt2pul   = load("Pulleys/GT2 Timing Pulley 20 Tooth.step")
idler    = load("Pulleys/Smooth Idler Pulley Wheel.step")
eccspacer= load("Hardware/Eccentric Spacer 6mm.step")
idlerpl  = load("Plates/Idler Pulley Plate.step")
cube_con = load("Brackets/Cube Corner Connector.step")

# ============================================================
# Colors
# ============================================================
ALU = Color(0.75,0.75,0.75)   # Frame aluminum
DRK = Color(0.55,0.55,0.55)   # Z-platform rails
BLK = Color(0.20,0.20,0.20)   # Gantry beam
MOT = Color(0.12,0.12,0.12)   # Motors
PLT = Color(0.65,0.68,0.65)   # Gantry plates
MNT = Color(0.60,0.62,0.60)   # Motor mounts
WHL = Color(0.85,0.85,0.80)   # V-wheels (delrin white)
PUL = Color(0.30,0.30,0.30)   # Pulleys (dark metal)
IDL = Color(0.40,0.40,0.45)   # Idlers
GRN = Color(0.59,0.84,0.00)   # Belt (M3-CRETE lime green)
CUB = Color(0.50,0.50,0.50)   # Cube connectors
DRG = Color(0.15,0.15,0.15)   # Drag chain (black nylon)

assy = Assembly("M3-2_Assembly")
n = [0]
def add(s, nm, c, l):
    assy.add(s, name=nm, color=c, loc=l); n[0] += 1

# ============================================================
# FRAME — Stacked/layered corners, ALL standard 1200mm lengths
# ============================================================
# CORNER CONVENTION: Posts define corner positions. X-rails stack
# behind/in-front of posts in Y. Y-braces stack above X-rails in Z.
# Full 1200mm pieces extend through the corner zone for max rigidity.
#
# Post (2040 rz=90): 40mm(X) x 20mm(Y) x 1200mm(Z)
#   At origin: X[-20,20] Y[-10,10] Z[0,1200]
# X-rail (2080): 1200mm(X) x 20mm(Y) x 80mm(Z)
#   At origin: X[0,1200] Y[-10,10] Z[-40,40]
# Y-brace (2040): 20mm(X) x 1200mm(Y) x 40mm(Z)
#   At origin: X[-10,10] Y[0,1200] Z[-20,20]
#
# Post positions (centers):
#   FL: (20, 10)   FR: (2380, 10)
#   RL: (20, 1190) RR: (2380, 1190)
#
# X-rails stacked behind front posts (Y=30) and in-front of rear posts (Y=1170)
# This gives each member its own volume at corners.

# Posts: 4x 2040, full height
add(e_post, "post_FL", ALU, L(20, 10))
add(e_post, "post_FR", ALU, L(2380, 10))
add(e_post, "post_RL", ALU, L(20, 1190))
add(e_post, "post_RR", ALU, L(2380, 1190))

# Top X-rails: 4x 2080, full 1200mm, stacked behind front posts / in-front of rear
# Front pair: Y=30 → Y[20,40] (behind front posts Y[0,20])
# Rear pair: Y=1170 → Y[1160,1180] (in front of rear posts Y[1180,1200])
# Z center at 1140 → Z[1100,1180]
TOP_Z = 1140  # top rail center Z
add(e_xrail, "topX_F1", ALU, L(0, 30, TOP_Z))
add(e_xrail, "topX_F2", ALU, L(1200, 30, TOP_Z))
add(e_xrail, "topX_B1", ALU, L(0, 1170, TOP_Z))
add(e_xrail, "topX_B2", ALU, L(1200, 1170, TOP_Z))

# Top Y-braces: 3x 2040, full 1200mm, at post X positions
# Brace center Z = TOP_Z + 40 + 20 = 1200 (stacked above X-rail top face)
# Actually let's put them AT the X-rail level but at the post X positions
# Brace at X=20 (left post), X=1200 (center splice), X=2380 (right post)
# Z center = TOP_Z → Z[1120,1160] — sits inside the 80mm X-rail Z-envelope
BRACE_Z = TOP_Z
add(e_ybrace, "topY_L", ALU, L(20, 0, BRACE_Z))
add(e_ybrace, "topY_C", ALU, L(1200, 0, BRACE_Z))
add(e_ybrace, "topY_R", ALU, L(2380, 0, BRACE_Z))

# Bottom Y-braces: 2x 2040, full 1200mm (open front/back)
BOT_Z = 0  # bottom brace center at Z=0
add(e_ybrace, "botY_L", ALU, L(20, 0, BOT_Z))
add(e_ybrace, "botY_R", ALU, L(2380, 0, BOT_Z))

print(f"  Frame: {n[0]} parts")

# ============================================================
# SPLICE CONNECTORS — at X=1200 rail junctions
# ============================================================
# Cube connectors (20x20x20) placed inside X-rail splice joints.
# 4 top X-rails, each spliced at X=1200. 2 connectors per splice
# (top and bottom of the 80mm rail cavity).
splice_x = 1200  # Junction point
for s, yr in [("F", 30), ("B", 1170)]:  # X-rails at Y=30 and Y=1170
    add(cube_con, f"splice_{s}_top", CUB, L(splice_x, yr, TOP_Z + 30))
    add(cube_con, f"splice_{s}_bot", CUB, L(splice_x, yr, TOP_Z - 30))

print(f"  + Splice connectors: {n[0]} parts")

# ============================================================
# Z-PLATFORM (moves up/down on posts) — full 1200mm pieces
# ============================================================
# Y-rails: 2x 2080, full 1200mm, left and right sides
# Stacked inside posts: left at X=50 (post X[0,40] + 10mm gap)
# Y-rail at origin: X[-10,10] Y[0,1200] Z[-40,40]
# Placed at X=50: X[40,60] Y[0,1200] Z[ZP-40, ZP+40]
add(e_yrail, "zpY_L", DRK, L(50, 0, ZP))
add(e_yrail, "zpY_R", DRK, L(2350, 0, ZP))

# Gantry beam: 2x 1200mm segments spliced at center for full 2400mm X span
# Beam at Y=600 (frame center), rides along Y on the Z-platform
# Beam center Z = ZP → Z[ZP-40, ZP+40]
add(e_gbeam, "gantry_1", BLK, L(0, 600, ZP))
add(e_gbeam, "gantry_2", BLK, L(1200, 600, ZP))

print(f"  + Z-platform + gantry: {n[0]} parts")

# ============================================================
# PLATES — Z-carriages, Y-gantry, X-carriage
# ============================================================
# Gantry plate (20-80): 127(X) x 3(Y) x 88(Z), with ry=90 → 88(X) x 3(Y) x 127(Z)
# Plate thickness = 3mm (PT)
#
# Z-CARRIAGE PLATES: sandwich each post, ride vertically
# Front plate: Y = post_front_face - PT = post_Y - 10 - 3 = post_Y - 13
# Back plate:  Y = post_back_face = post_Y + 10
# Post FL center: (20, 10). Front face Y=0, back face Y=20.
for nm, cx, py in [("FL",20,10), ("FR",2380,10), ("RL",20,1190), ("RR",2380,1190)]:
    pf = py - 10          # post front Y-face
    pb = py + 10          # post back Y-face
    add(plate, f"zpl_{nm}_f", PLT, L(cx, pf - 1.5, ZP, ry=90))   # front plate
    add(plate, f"zpl_{nm}_b", PLT, L(cx, pb + 1.5, ZP, ry=90))   # back plate

# Y-GANTRY PLATES: ride Y-rails, carry gantry beam ends
# Adjacent to Z-carriage back plates with 1mm running gap.
# Z-carriage back plate (front posts): Y = 10 + 10 + 1.5 = 21.5 → back face at Y=23
# Y-gantry plate: Y = 23 + 1mm gap + 1.5mm half-plate = 25.5
# For rear posts: Z-carriage front plate at Y = 1190-10-1.5 = 1178.5 → front face at 1177
# Y-gantry plate: Y = 1177 - 1mm gap - 1.5mm = 1174.5
GAP = 1  # running clearance mm
for nm, cx, py in [("L",50,10), ("R",2350,10)]:
    zpl_back_face = py + 10 + PT  # Z-carriage back plate outer face
    ypl_y = zpl_back_face + GAP + PT/2  # Y-gantry plate center
    add(plate, f"ypl_{nm}", PLT, L(cx, ypl_y, ZP, ry=90))

# X-CARRIAGE PLATES: sandwich the gantry beam, ride along X
# Beam at Y=600 center. Beam is 20mm in Y → Y[590,610].
# Front plate: Y = 590 - 1.5 = 588.5
# Back plate:  Y = 610 + 1.5 = 611.5
add(plate, "xcar_f", PLT, L(1200, 588.5, ZP, ry=90))
add(plate, "xcar_b", PLT, L(1200, 611.5, ZP, ry=90))

print(f"  + Plates: {n[0]} parts")

# ============================================================
# V-WHEEL CARRIAGES
# ============================================================
# Each carriage = 4 V-wheels (2 fixed + 2 eccentric) riding a V-slot rail.
# Wheel is 23.9mm dia, 10.2mm thick, centered at origin.
# Native orientation: axle along X. Placed at plate bolt-hole offsets.

# Gantry plate bolt pattern for V-wheels (20-80 plate, 127x88mm):
# Approx hole positions from plate center: ±45mm Z, ±25mm Z (inner pair)
# Wheels sit on the V-groove faces of the rail.

def add_vwheel_quad(prefix, cx, cy, cz, axis="Z"):
    """Add 4 V-wheels around a plate center for a given rail axis.
    V-wheel native: 23.9mm dia, 10.2mm thick, axle along X, centered at origin.
    Axle must be perpendicular to the rail face the wheel rides on.
    """
    if axis == "Z":
        # Post is 40mm(X) x 20mm(Y), vertical. V-grooves on the 40mm X-faces.
        # Wheels ride the X-faces → axle along Y (rz=90 rotates axle X→Y).
        # 2 wheels on each side of post (offset in Z from carriage center).
        for i, (dx, dz) in enumerate([(-25,-30), (-25,30), (25,-30), (25,30)]):
            add(vwheel, f"vw_{prefix}_{i}", WHL, L(cx+dx, cy, cz+dz, rz=90))
    elif axis == "Y":
        # Y-rail is 2080: 80mm in Z, 20mm in X. V-grooves on the Z-faces.
        # Wheels ride the Z-faces → axle along X (native, no rotation needed).
        # 2 wheels on each side (offset in Y from carriage center).
        for i, (dy, dz) in enumerate([(-30,-25), (-30,25), (30,-25), (30,25)]):
            add(vwheel, f"vw_{prefix}_{i}", WHL, L(cx, cy+dy, cz+dz))
    elif axis == "X":
        # X-beam is 2080: 80mm in Z, 20mm in Y. V-grooves on the Z-faces.
        # Wheels ride the Z-faces → axle along Y (rz=90).
        # 2 wheels on each side (offset in X from carriage center).
        for i, (dx, dz) in enumerate([(-30,-25), (-30,25), (30,-25), (30,25)]):
            add(vwheel, f"vw_{prefix}_{i}", WHL, L(cx+dx, cy, cz+dz, rz=90))

# Z-CARRIAGE V-WHEELS (4 carriages x 4 wheels = 16 wheels)
# Each rides its respective post vertically.
for nm, cx, cy in [("FL",20,10), ("FR",2380,10), ("RL",20,1190), ("RR",2380,1190)]:
    add_vwheel_quad(f"zc_{nm}", cx, cy, ZP, axis="Z")

# Y-CARRIAGE V-WHEELS (2 carriages x 4 wheels = 8 wheels)
# Ride the Y-rails at gantry beam end positions.
# Y-rails at X=50 and X=2350, beam at Y=600
for nm, cx in [("L", 50), ("R", 2350)]:
    add_vwheel_quad(f"yc_{nm}", cx, 600, ZP, axis="Y")

# X-CARRIAGE V-WHEELS (1 carriage x 4 wheels = 4 wheels)
# Printhead carriage rides gantry beam along X. Beam at Y=600.
add_vwheel_quad("xc", 1200, 600, ZP, axis="X")

print(f"  + V-wheels (28): {n[0]} parts")

# ============================================================
# MOTORS + MOTOR MOUNTS
# ============================================================
# Z motors: STRADDLE the top Y-brace (Z=1140).
# Motor body ABOVE brace (Z>1160), shaft points DOWN through/beside brace.
# Shaft hub/disk at the brace level routes belt over the brace and down.
# Top brace center Z=1140, brace is 40mm tall in Z → Z[1120,1160].
# Motor mount plate sits on top of brace at Z=1160.
# Motor body extends upward from Z=1160 (shaft at Z=1160, body to Z=1160+56=1216).
BRACE_TOP = 1160  # top face of the Y-brace

for nm, cx, cy, sx in [("FL",20,10,1), ("FR",2380,10,-1),
                        ("RL",20,1190,1), ("RR",2380,1190,-1)]:
    # Motor straddles top brace. Mount on brace top face.
    mx = cx + sx * 30  # offset inward toward frame center
    add(mmount, f"mmz_{nm}", MNT, L(mx, cy, BRACE_Z + 20))  # on top of brace
    add(motor,  f"mz_{nm}",  MOT, L(mx, cy, BRACE_Z + 23, rx=180))  # shaft down
    # Hub disk below brace — belt wraps around this
    hub_disk = cq.Workplane("XY").cylinder(10, 15)
    add(hub_disk, f"hub_z{nm}", PUL, L(mx, cy, BRACE_Z - 30))

# Y motors: inside frame, at back end of Y-rails
# Y-rails run Y[0,1200]. Motor at back end (Y≈1150), shaft along -Y
add(motor, "my_L", MOT, L(50, 1150, ZP, rx=-90))
add(motor, "my_R", MOT, L(2350, 1150, ZP, rx=-90))

# X motor: on X-carriage, above gantry beam. Beam at Y=600.
add(motor, "mx", MOT, L(1200, 620, ZP+47, rx=-90))

print(f"  + Motors: {n[0]} parts")

# ============================================================
# GT2 PULLEYS — Y and X motor shafts
# ============================================================
# (Z-axis pulleys already placed above with motors)

# Y motor pulleys: on shaft tip
add(gt2pul, "pul_yL", PUL, L(50, 1130, ZP, rx=-90))
add(gt2pul, "pul_yR", PUL, L(2350, 1130, ZP, rx=-90))

# X motor pulley
add(gt2pul, "pul_x", PUL, L(1200, 600, ZP+47, rx=-90))

print(f"  + GT2 pulleys: {n[0]} parts")

# ============================================================
# IDLER PULLEYS — belt return points
# ============================================================
# Smooth idler: 22mm dia, 12.7mm thick. Native axle along X.
# For Z-axis: idler axle must be along Y (perpendicular to belt vertical run)
# For Y-axis: idler axle must be along X (perpendicular to Y belt run)
# For X-axis: idler axle must be along Y (perpendicular to X belt run)

# Z-axis idlers: at BOTTOM of each post. Axle along Y (ry=90 not needed,
# but we need rz=90 to rotate axle from X to Y direction... actually
# the idler is symmetric, we just need the axle perpendicular to the
# belt travel direction. Belt travels in Z, so axle in Y.)
for nm, cx, cy, sx in [("FL",20,10,1), ("FR",2380,10,-1),
                        ("RL",20,1190,1), ("RR",2380,1190,-1)]:
    ix = cx + sx * 30  # same X offset as motor hub disk
    add(idler, f"idl_z{nm}", IDL, L(ix, cy, 20, rz=90))
    add(idlerpl, f"idlpl_z{nm}", MNT, L(ix, cy, 20))

# Y-axis idlers: at front end of Y-rails (Y≈50). Axle along X.
add(idler, "idl_yL", IDL, L(50, 50, ZP))
add(idler, "idl_yR", IDL, L(2350, 50, ZP))

# X-axis idlers: at each end of gantry beam. Beam at Y=600. Axle along Y.
add(idler, "idl_xL", IDL, L(50, 600, ZP+47, rz=90))
add(idler, "idl_xR", IDL, L(2350, 600, ZP+47, rz=90))

print(f"  + Idler pulleys: {n[0]} parts")

# ============================================================
# GT2 BELT PATHS — represented as thin boxes (10mm wide belt)
# ============================================================
# Belts are 10mm wide GT2. Modeled as thin rectangular solids
# for visualization. Color: M3-CRETE lime green.
BELT_W = 10   # belt width
BELT_T = 2    # belt thickness for visualization

def make_belt_segment(length, width=BELT_W, thickness=BELT_T):
    """Create a belt segment as a thin box."""
    return cq.Workplane("XY").box(length, thickness, width)

# Z-AXIS BELTS (4x): from hub disk (Z≈BRACE_Z-30) to bottom idler (Z=20)
z_belt_len = BRACE_Z - 30 - 20  # ≈1090mm
z_belt = make_belt_segment(z_belt_len)
for nm, cx, cy, sx in [("FL",20,10,1), ("FR",2380,10,-1),
                        ("RL",20,1190,1), ("RR",2380,1190,-1)]:
    bx = cx + sx * 30
    belt_center_z = (BRACE_Z - 30 + 20) / 2
    add(z_belt, f"belt_z{nm}", GRN, L(bx, cy, belt_center_z, ry=90))

# Y-AXIS BELTS (2x): full 1200mm along Y-rails
y_belt_len = 1100  # motor pulley to idler span
y_belt = make_belt_segment(y_belt_len)
for nm, cx in [("L", 50), ("R", 2350)]:
    add(y_belt, f"belt_y{nm}", GRN, L(cx, 600, ZP+15, rz=90))

# X-AXIS BELT (1x): full span along gantry beam (2300mm usable)
x_belt_len = 2300
x_belt = make_belt_segment(x_belt_len)
add(x_belt, "belt_x", GRN, L(1200, 600, ZP+47))

print(f"  + Belt paths: {n[0]} parts")

# ============================================================
# DRAG CHAIN MOUNTS — cable management
# ============================================================
# Drag chains modeled as simple box representations.
# Real chains are ~25mm wide x 25mm tall, flexible links.
DC_W = 30    # drag chain outer width
DC_H = 20    # drag chain height
DC_T = 15    # drag chain depth (profile)

def make_drag_chain(length):
    """Simple box representing a drag chain run."""
    return cq.Workplane("XY").box(length, DC_T, DC_H)

# X-axis drag chain: runs along gantry beam top, from fixed end to X-carriage
# Fixed end at left side of beam, moving end follows printhead
x_dc_len = 900  # half-span representative (chain folds)
x_dc = make_drag_chain(x_dc_len)
add(x_dc, "dc_x", DRG, L(520, 600, ZP+80))

# Y-axis drag chain: runs along one Y-rail, from fixed frame to gantry
y_dc_len = 500
y_dc = make_drag_chain(y_dc_len)
add(y_dc, "dc_y", DRG, L(50, 750, ZP+60, rz=90))  # alongside left Y-rail

# Z-axis drag chain: runs vertically along one post, from fixed top to Z-platform
z_dc_len = 400
z_dc = make_drag_chain(z_dc_len)
add(z_dc, "dc_z", DRG, L(-15, 10, 800, ry=90))

print(f"  + Drag chains: {n[0]} parts")

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
print(f"\n  v0.2.0: {total} parts | Frame + V-wheels + Pulleys + Belts + Drag chains")
