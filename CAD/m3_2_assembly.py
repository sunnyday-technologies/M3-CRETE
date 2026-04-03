#!/usr/bin/env python3
"""
M3-CRETE M3-2 Assembly — v0.1.0
Draft CAD assembly: frame + Z-platform + gantry + motors.
40 parts. AI-generated from OpenBuilds STEP library + parametric extrusions.

Version history:
  v0.1.0 — Frame structure, Z-platform, gantry beam, motors, plates (40 parts)
"""
import cadquery as cq
from cadquery import Assembly, Color, Location
from OCP.gp import gp_GTrsf, gp_Mat, gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform, BRepBuilderAPI_Transform
import os, time, math

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")

def load(relpath):
    return cq.importers.importStep(os.path.join(STEP_DIR, relpath))

def sao(step_file, length, rx=0, ry=0, rz=0):
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

# Dimensions
W=2400; D=1200; H=1200
PX=40; PY=20; PT=3
S40 = "V-Slot 20x40x1000 Linear Rail.step"
S80 = "V-Slot 20x80x1000 Linear Rail.step"

print("Generating parts...")
t0 = time.time()

# Parts (all pre-oriented, dimensions from Assembly4)
e_post   = sao(S40, H, rz=90)              # 40x20x1200
e_xrail  = sao(S80, 1160, ry=90, rz=90)    # 1160x20x80 (top X-rails)
e_ybrace = sao(S40, 1160, rx=-90)           # 20x1160x40 (Y-braces)
e_yrail  = sao(S80, 1154, rx=-90)           # 20x1154x80 (Z-platform Y-rails)
e_gbeam  = sao(S80, 2270, ry=90, rz=90)    # 2270x20x80 (gantry beam)

plate  = load("Plates/V-Slot Gantry Plate 20-80mm.step")
motor  = load("Electronics/Nema 23 Stepper Motor.step")
mmount = load("Plates/Motor Mount Plate Nema 23.step")

# Colors
ALU = Color(0.75,0.75,0.75); DRK = Color(0.55,0.55,0.55)
BLK = Color(0.20,0.20,0.20); MOT = Color(0.12,0.12,0.12)
PLT = Color(0.65,0.68,0.65); MNT = Color(0.60,0.62,0.60)

assy = Assembly("M3-2_Assembly")
n = [0]
def add(s, nm, c, l):
    assy.add(s, name=nm, color=c, loc=l); n[0] += 1

# ── POSTS [0,8,9,10] ──
#  FL: X[0,40]     Y[0,20]     Z[0,1200]
#  FR: X[2360,2400] Y[0,20]
#  RL: X[0,40]     Y[1180,1200]
#  RR: X[2360,2400] Y[1180,1200]
add(e_post, "post_FL", ALU, L(20, 10))
add(e_post, "post_FR", ALU, L(2380, 10))
add(e_post, "post_RL", ALU, L(20, 1190))
add(e_post, "post_RR", ALU, L(2380, 1190))

# ── TOP X-RAILS [1,11,12,13] Z[1100,1180] ──
for s,yr in [("F",10),("B",1190)]:
    add(e_xrail, f"topX_{s}1", ALU, L(40, yr, 1100))
    add(e_xrail, f"topX_{s}2", ALU, L(1200, yr, 1100))

# ── TOP Y-BRACES [2,14,15] Z[1140,1180] ──
# Nick has them at Z[1140,1180] and Z[1160,1200]. Let's use 1140 (below X-rails)
add(e_ybrace, "topY_L", ALU, L(20, 20, 1140))
add(e_ybrace, "topY_C", ALU, L(1200, 20, 1140))
add(e_ybrace, "topY_R", ALU, L(2380, 20, 1140))

# ── BOTTOM Y-BRACES [16,17] Z[-20,20] ──
add(e_ybrace, "botY_L", ALU, L(20, 20, -20))
add(e_ybrace, "botY_R", ALU, L(2380, 20, -20))

# ── Y-RAILS (Z-platform) [3,18] Z[400,480] ──
add(e_yrail, "zpY_L", DRK, L(40, 23, 440))
add(e_yrail, "zpY_R", DRK, L(2340, 23, 440))

# ── GANTRY BEAM [4] X[65,2335] Y[474,494] Z[400,480] ──
add(e_gbeam, "gantry", BLK, L(65, 484, 440))

print(f"  Frame + platform: {n[0]} parts")

# ── Z-CARRIAGE PLATES (sandwich posts) [5,19-25] ──
# Z center = 440 -> plate Z[376.5,503.5]
# FL: front Y[7,10], back Y[30,33]
# FR: front Y[7,10], back Y[30,33]
# RL: front Y[1187,1190], back Y[1210,1213]
# RR: front Y[1187,1190], back Y[1210,1213]
for nm,cx,yf,yb in [("FL",20,7,30),("FR",2380,7,30),
                     ("RL",20,1187,1210),("RR",2380,1187,1210)]:
    add(plate, f"pl_{nm}_f", PLT, L(cx, yf, 440, ry=90))
    add(plate, f"pl_{nm}_b", PLT, L(cx, yb, 440, ry=90))

# ── X-CARRIAGE PLATES [26,27] sandwich beam in Y ──
# Y[481,484] and Y[504,507]. Beam Y[474,494].
# Tighten: plate flush at beam faces Y=474-PT=471 and Y=494
add(plate, "xcar_f", PLT, L(972, 471, 440, ry=90))
add(plate, "xcar_b", PLT, L(972, 494, 440, ry=90))

# ── X-END PLATES [28,29,39] on Y-rails, connect beam to carriages ──
# [28]: X[27,30] Y[420.5,547.5] Z[396,484] -> 3x127x88, plate rz=90
# [29]: X[2327,2330]
add(plate, "xend_L", PLT, L(28.5, 484, 440, rz=90))
add(plate, "xend_R", PLT, L(2328.5, 484, 440, rz=90))
# [39]: X[2349,2352] — second plate on right
add(plate, "xend_R2", PLT, L(2350.5, 484, 440, rz=90))

print(f"  Plates: {n[0]} parts")

# ── Z MOTORS + MOUNTS [6-7, 30-35] ──
# ── Z MOTORS — HORIZONTAL at post tops, shaft pointing INWARD ──
# Mounted horizontally to preserve build height and prevent knock-off.
# Motor mount plate flat on post top (Z=1200).
# Motor body extends horizontally INWARD (toward frame center).
#
# FL: shaft points +X (inward). ry=90 rotates shaft from +Z to +X.
#     Motor center at post top, body extends in +X direction.
add(mmount, "mmz_FL", MNT, L(20, 10, 1200, rx=90))
add(motor, "mz_FL", MOT, L(20+40, 10, 1180, ry=90))

# FR: shaft points -X (inward). ry=-90.
add(mmount, "mmz_FR", MNT, L(2380, 10, 1200, rx=90))
add(motor, "mz_FR", MOT, L(2380-40, 10, 1180, ry=-90))

# RL: shaft points +X (inward). ry=90.
add(mmount, "mmz_RL", MNT, L(20, 1190, 1200, rx=90))
add(motor, "mz_RL", MOT, L(20+40, 1190, 1180, ry=90))

# RR: shaft points -X (inward). ry=-90.
add(mmount, "mmz_RR", MNT, L(2380, 1190, 1200, rx=90))
add(motor, "mz_RR", MOT, L(2380-40, 1190, 1180, ry=-90))

# ── Y MOTORS — INSIDE frame, at back end of Y-rails ──
# Moved inward: motor body sits between the Y-rails, not outside frame.
# Motor at Y-rail back end but shifted inward in X toward frame center.
# Shaft points along +Y (toward back). Motor body extends toward front.
# Left motor: X = Y-rail center (50) + offset inward = 50 + 40 = 90
# Right motor: X = Y-rail center (2340) - offset inward = 2340 - 40 = 2300
add(motor, "my_L", MOT, L(90, 1200, 440, rx=90))
add(motor, "my_R", MOT, L(2310, 1200, 440, rx=90))

# ── X MOTOR [38] on carriage above beam ──
# X[944,1000] Y[463,540] Z[459,515] — shaft along +Y
add(motor, "mx", MOT, L(972, 502, 487, rx=90))

print(f"  Total: {n[0]} parts")

# ── EXPORT ──
out = os.path.join(os.path.dirname(__file__), "M3-2_Assembly.step")
print(f"\nExporting {n[0]} parts...")
t1 = time.time()
assy.save(out)
mb = os.path.getsize(out) / 1024 / 1024
print(f"  {mb:.1f} MB in {time.time()-t1:.1f}s")
print(f"\n  v12: {n[0]} parts | Matched to Assembly4.step positions")
