"""
Z bottom bearing holder + hard stop (BOM id 91), 3D printed, one per Z post.

Generated on Nick's request (2026-10-12: "just provide a simple printed piece
we can place a bearing into"); a bought 2020 lead-screw block did not fit
inside the C-channel. Holds the 608ZZ (BOM id 89) that centres the bottom of
the Tr8x2 screw. The screw floats axially in it; the top of the screw is
fixed at the motor mount. The holder's top face is the Z hard stop: the
carriage's nut block lands on it during sensorless homing.

Frame (front post; rear posts use it turned 180 deg about Z): screw axis on
Z, C-channel open face at y = +AXIS_INSET, channel floor at y = AXIS_INSET -
CHANNEL_DEPTH, Z = 0 at the top edge of the existing bottom spacer plate
(id 79), which the holder's lip rests on.

  column  x +/-17 (3 mm off the channel walls), back face on the channel
          floor, front face flush with the open face; up to the stop face
  lip     wraps the part of the 608 that pokes past the post face
  pocket  608ZZ press fit, open at the bottom: press the bearing in before
          fitting the holder
  bolts   2x M5 x 20 SHCS into drop-in T-nuts in the channel-floor slots
          (x = +/-10); heads sit in counterbores in the front face

The stop height follows from the carriage: the carriage plate must clear the
lip by STOP_CLEARANCE. m3_2_assembly.py passes the measured values in.

Run:   python CAD/z_bottom_holder.py   (writes the STEP + STL below)
"""
import os
import cadquery as cq

HERE = os.path.dirname(__file__)
OUT_STEP = os.path.join(HERE, "Custom", "Z_Bottom_Bearing_Holder_M3-2.step")
OUT_STL = os.path.join(HERE, "Custom", "Z_Bottom_Bearing_Holder_M3-2.stl")

AXIS_INSET = 5.0            # screw axis -> channel open face (carriage plate runs 1 mm off it)
CHANNEL_DEPTH = 20.0        # C-Beam 4080 channel, open face to floor
COLUMN_W = 34.0             # 3 mm clearance to the 40 mm channel walls
BRG_OD, BRG_H = 22.0, 7.0   # 608ZZ
POCKET_D = BRG_OD + 0.2     # FDM press fit; holes print slightly small
POCKET_SHOULDER = 2.0       # material above the bearing (holds it up the screw)
LIP_WALL = 2.0
SCREW_CLEAR_D = 10.0
BOLT_X = 10.0               # channel-floor slot centres
BOLT_D, CBORE_D, CBORE_DEPTH = 5.5, 9.5, 5.5
STOP_CLEARANCE = 2.0        # carriage plate bottom above the lip at the stop
# V1.0 carriage geometry (plate 88 tall, nut block 20 tall, centred on it).
CARRIAGE_PLATE_H = 88.0
NUT_BLOCK_H = 20.0

LIP_TOP = BRG_H + POCKET_SHOULDER
STOP_TOP = LIP_TOP + STOP_CLEARANCE + (CARRIAGE_PLATE_H - NUT_BLOCK_H) / 2


def build_holder(stop_top=STOP_TOP):
    y_front, y_back = AXIS_INSET, AXIS_INSET - CHANNEL_DEPTH
    column = cq.Solid.makeBox(COLUMN_W, y_front - y_back, stop_top,
                              cq.Vector(-COLUMN_W / 2, y_back, 0))
    lip = cq.Solid.makeCylinder(POCKET_D / 2 + LIP_WALL, LIP_TOP)
    body = column.fuse(lip)
    body = body.cut(cq.Solid.makeCylinder(POCKET_D / 2, BRG_H))
    body = body.cut(cq.Solid.makeCylinder(SCREW_CLEAR_D / 2, stop_top))
    bolt_z = (LIP_TOP + stop_top) / 2
    for x in (-BOLT_X, BOLT_X):
        body = body.cut(cq.Solid.makeCylinder(BOLT_D / 2, y_front - y_back,
                                              cq.Vector(x, y_back, bolt_z), cq.Vector(0, 1, 0)))
        body = body.cut(cq.Solid.makeCylinder(CBORE_D / 2, CBORE_DEPTH,
                                              cq.Vector(x, y_front - CBORE_DEPTH, bolt_z),
                                              cq.Vector(0, 1, 0)))
    body = body.clean()
    if not body.isValid():
        raise RuntimeError("holder solid is not valid")
    return body


def main():
    holder = build_holder()
    bb = holder.BoundingBox()
    print(f"bottom holder: X[{bb.xmin:.1f},{bb.xmax:.1f}] Y[{bb.ymin:.1f},{bb.ymax:.1f}] "
          f"Z[{bb.zmin:.1f},{bb.zmax:.1f}]  vol {holder.Volume() / 1000:.1f} cm^3; "
          f"stop face {STOP_TOP:.1f} mm above the bottom plate")
    cq.exporters.export(cq.Workplane().add(holder), OUT_STEP)
    cq.exporters.export(cq.Workplane().add(holder), OUT_STL, tolerance=0.05, angularTolerance=0.1)
    print(f"  wrote {os.path.relpath(OUT_STEP, HERE)} and {os.path.relpath(OUT_STL, HERE)}")


if __name__ == "__main__":
    main()
