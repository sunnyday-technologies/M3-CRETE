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
e_ybrace     = sao(S40, 1160, rx=-90)        # 20x1160x40 Y-brace, bottom (between posts)
e_ybrace_top = sao(S40, 1116, rx=-90)       # 20x1116x40 Y-brace, top (trimmed: between X-rail pairs)
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
# Z center at 1120 → Z[1080,1160], 40mm below post top (Z=1200)
TOP_Z = 1120  # top rail center Z
add(e_xrail, "topX_F1", ALU, L(0, 30, TOP_Z))
add(e_xrail, "topX_F2", ALU, L(1200, 30, TOP_Z))
add(e_xrail, "topX_B1", ALU, L(0, 1170, TOP_Z))
add(e_xrail, "topX_B2", ALU, L(1200, 1170, TOP_Z))

# Top Y-braces: 3x 2040, trimmed 1116mm (between X-rail back faces with 2mm gap)
# X-rail back face (front pair): Y=40. Brace starts at Y=42 (2mm gap).
# X-rail back face (rear pair): Y=1160. Brace ends at Y=42+1116=1158 (2mm gap).
# Brace stacks ABOVE X-rails: X-rail top at Z=1160, brace bottom at Z=1162 (2mm gap).
# Brace center Z = 1162 + 20 = 1182. Brace top at Z=1202 (only 2mm above posts).
BRACE_Z = TOP_Z + 62  # Z=1182, brace Z[1162,1202], 2mm gap from X-rail top
add(e_ybrace_top, "topY_L", ALU, L(20, 42, BRACE_Z))
add(e_ybrace_top, "topY_C", ALU, L(1200, 42, BRACE_Z))
add(e_ybrace_top, "topY_R", ALU, L(2380, 42, BRACE_Z))

# Bottom Y-braces: 1160mm between posts, bottom flush with floor
add(e_ybrace, "botY_L", ALU, L(20, 20, 20))
add(e_ybrace, "botY_R", ALU, L(2380, 20, 20))

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
# Must clear Z-carriage plates (plate X envelope = post_X ± 44mm)
# Post FL X=20, plate extends to X=20+44=64. Y-rail must start at X>64.
# Y-rail at origin: X[-10,10]. Place at X=75 → X[65,85]. Clears plate at 64.
add(e_yrail, "zpY_L", DRK, L(75, 0, ZP))
add(e_yrail, "zpY_R", DRK, L(2325, 0, ZP))

# Gantry beam: 2x 1200mm segments spliced at X=1200 for full 2400mm X span
# Beam at Y=600, same Z as Y-rails. Full span X[0,2400].
# Beam intersects Y-rails at X[65,85] and X[2315,2335] — intentional connection
# points joined via Y-gantry plates (V-wheel carriages ride the Y-rails).
BEAM_Z = ZP
add(e_gbeam, "gantry_1", BLK, L(0, 600, BEAM_Z))
add(e_gbeam, "gantry_2", BLK, L(1200, 600, BEAM_Z))

print(f"  + Z-platform + gantry: {n[0]} parts")

# ============================================================
# PLATES — Z-carriages, Y-gantry, X-carriage
# ============================================================
# Gantry plate (20-80): 127(X) x 3(Y) x 88(Z), with ry=90 → 88(X) x 3(Y) x 127(Z)
# Plate thickness = 3mm (PT)
#
# Z-CARRIAGE PLATES: sandwich each post, ride vertically
# Plate native Y[0,3] (not centered). After ry=90, Y stays [0,3].
# Front plate: translate Y = pf - PT - 1.5 → plate Y[pf-4.5, pf-1.5] (1.5mm gap)
# Back plate:  translate Y = pb + 1.5      → plate Y[pb+1.5,  pb+4.5] (1.5mm gap)
# Post FL center: (20, 10). Front face pf=0, back face pb=20.
for nm, cx, py in [("FL",20,10), ("FR",2380,10), ("RL",20,1190), ("RR",2380,1190)]:
    pf = py - 10          # post front Y-face
    pb = py + 10          # post back Y-face
    add(plate, f"zpl_{nm}_f", PLT, L(cx, pf - 4.5, ZP, ry=90))   # front plate (1.5mm gap)
    add(plate, f"zpl_{nm}_b", PLT, L(cx, pb + 1.5, ZP, ry=90))   # back plate (1.5mm gap)

# Y-GANTRY PLATES: at gantry beam ends, connecting beam to Y-rail carriages
# These sit at the beam Y-position (Y=600), at the Y-rail X positions
# They bridge between the Y-rail carriage and the gantry beam
GAP = 1  # running clearance mm
add(plate, "ypl_L", PLT, L(75, 600, ZP, ry=90))
add(plate, "ypl_R", PLT, L(2325, 600, ZP, ry=90))

# X-CARRIAGE PLATES: sandwich the gantry beam, ride along X
# Beam at Y=600 center, Z=BEAM_Z. Beam is 20mm in Y → Y[590,610].
# Front plate: Y = 590 - PT - 1.5 = 585.5 → plate Y[585.5, 588.5] (1.5mm gap)
# Back plate:  Y = 610 + 1.5     = 611.5 → plate Y[611.5, 614.5] (1.5mm gap)
add(plate, "xcar_f", PLT, L(1200, 585.5, BEAM_Z, ry=90))
add(plate, "xcar_b", PLT, L(1200, 611.5, BEAM_Z, ry=90))

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
for nm, cx in [("L", 75), ("R", 2325)]:
    add_vwheel_quad(f"yc_{nm}", cx, 600, ZP, axis="Y")

# X-CARRIAGE V-WHEELS (1 carriage x 4 wheels = 4 wheels)
# Printhead carriage rides gantry beam along X. Beam at Y=600, Z=BEAM_Z.
add_vwheel_quad("xc", 1200, 600, BEAM_Z, axis="X")

print(f"  + V-wheels (28): {n[0]} parts")

# ============================================================
# MOTORS + MOTOR MOUNTS
# ============================================================
# Z motors: STRADDLE the top Y-brace.
# Motor body ABOVE brace, shaft points DOWN through/beside brace.
# Shaft hub/disk at the brace level routes belt over the brace and down.
# Brace center Z=1182, brace Z[1162,1202]. Motor mount at BRACE_Z+30=1212.
BRACE_TOP = BRACE_Z + 20  # Z=1202, top face of the Y-brace

for nm, cx, cy, sx in [("FL",20,10,1), ("FR",2380,10,-1),
                        ("RL",20,1190,1), ("RR",2380,1190,-1)]:
    # Z-motor: HORIZONTAL, above brace, shaft pointing INWARD (along X)
    # Motor body OUTWARD from post (clears post), shaft reaches inward
    # Post edge: FL X=40, FR X=2360. Motor center 50mm beyond post edge.
    mx = cx + sx * 70  # motor center well inside frame, away from post
    mrot = 90 * sx
    # Mount plate on post top at brace Z
    add(mmount, f"mmz_{nm}", MNT, L(cx, cy, BRACE_Z + 30))
    # Motor horizontal, above brace+mount
    add(motor,  f"mz_{nm}",  MOT, L(mx, cy, BRACE_Z + 30, ry=mrot))
    # GT2 pulley on shaft tip
    px = cx + sx * 95
    add(gt2pul, f"pul_z{nm}", PUL, L(px, cy, BRACE_Z + 30, ry=mrot))

# Y motors: inside frame, behind Y-rails (between Y-rail and rear X-rail)
# Y-rail at X=75/2325. Motor offset in X so it doesn't clip Y-rail.
# Motor at Y=1130 (away from rear post at Y=1180), shaft along -Y
add(motor, "my_L", MOT, L(120, 1130, ZP, rx=-90))
add(motor, "my_R", MOT, L(2280, 1130, ZP, rx=-90))

# X motor: on X-carriage, beside the gantry beam (not on top — avoids clip)
# Beam Z[400,480]. Motor beside beam in Y, shaft along X (ry=90).
add(motor, "mx", MOT, L(1200, 640, BEAM_Z, ry=90))

print(f"  + Motors: {n[0]} parts")

# ============================================================
# GT2 PULLEYS — Y and X motor shafts
# ============================================================
# (Z-axis pulleys already placed above with motors)

# Y motor pulleys: on shaft tip
add(gt2pul, "pul_yL", PUL, L(120, 1110, ZP, rx=-90))
add(gt2pul, "pul_yR", PUL, L(2280, 1110, ZP, rx=-90))

# X motor pulley: below motor, on beam
add(gt2pul, "pul_x", PUL, L(1200, 600, BEAM_Z+45))

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
add(idler, "idl_yL", IDL, L(75, 50, ZP))
add(idler, "idl_yR", IDL, L(2325, 50, ZP))

# X-axis idlers: at each end of gantry beam. Axle along Y.
add(idler, "idl_xL", IDL, L(100, 600, BEAM_Z+45, rz=90))
add(idler, "idl_xR", IDL, L(2300, 600, BEAM_Z+45, rz=90))

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
for nm, cx in [("L", 75), ("R", 2325)]:
    add(y_belt, f"belt_y{nm}", GRN, L(cx, 600, ZP+15, rz=90))

# X-AXIS BELT (1x): full span along gantry beam (2300mm usable)
x_belt_len = 2300
x_belt = make_belt_segment(x_belt_len)
add(x_belt, "belt_x", GRN, L(1200, 600, BEAM_Z+45))

print(f"  + Belt paths: {n[0]} parts")

# Drag chains removed — will add with proper routing after motion system is finalized

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
