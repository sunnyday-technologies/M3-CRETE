"""
Y idler plate (BOM id 66), 3D printed, one per Y rail at the front end.

Authored on Nick's request (2026-10-13): "a small plate with two holes for
t-slots and one hole for a threaded fastener that holds the idler drum". It
lies flat on the floor of the Y rail's open C-channel, under the smooth
idler (BOM id 93), and replaces the 5x30x30 placeholder brackets that passed
through the rail web. Nick chose the floor over the open face (no Y travel
lost) at 3 mm: the channel is 20 mm deep and the idler 14.2 mm wide, which
leaves 3.5 mm behind the left idler. The two floor slots sit at +/-10 mm
from the channel centre, under the idler flanges, so the slot holes are
placed along the rail clear of the idler. How the M5 axle is anchored in
the centre hole (insert, drilled web or similar) is decided at build.

Frame (left Y rail; the right rail uses it turned 180 deg about Y): plate
on the channel floor, X = 0 on the floor and +X toward the channel mouth,
the idler axle on the X axis (Y = Z = 0), +Y along the rail away from its
front end, Z across the channel (the two floor slots at Z = +/-SLOT_Z).

Run:   python CAD/y_idler_plate.py   (writes the STEP + STL below)
"""
import os
import cadquery as cq

HERE = os.path.dirname(__file__)
OUT_STEP = os.path.join(HERE, "Custom", "Y_Idler_Plate_M3-2.step")
OUT_STL = os.path.join(HERE, "Custom", "Y_Idler_Plate_M3-2.stl")

THICK = 3.0                 # owner, 2026-10-13
WIDTH = 34.0                # across the channel: 3 mm clear of the 40 mm channel walls
SLOT_Z = 10.0               # C-Beam channel-floor slot centres, +/- from the channel centre
IDLER_R = 9.0               # id 93 flange radius (18 mm OD)
HEAD_R = 4.75               # M5 button-head screw head radius (9.5 mm)
HEAD_CLEAR = 1.0
SLOT_Y = IDLER_R + HEAD_CLEAR + HEAD_R + 4.25   # 19: slot holes behind the idler, heads clear of its flanges
FRONT = 10.0                # plate edge ahead of the axle (toward the rail end)
BACK = 7.0                  # plate edge past the slot holes
HOLE_D = 5.5                # M5 clearance (slot bolts and the idler axle)
CORNER_R = 2.0


def build_plate():
    length = FRONT + SLOT_Y + BACK
    plate = (cq.Workplane("YZ").center(SLOT_Y + BACK - length / 2, 0)
             .rect(length, WIDTH).extrude(THICK)
             .edges("|X").fillet(CORNER_R))
    holes = [(0.0, 0.0), (SLOT_Y, -SLOT_Z), (SLOT_Y, SLOT_Z)]
    for y, z in holes:
        plate = plate.cut(cq.Workplane("YZ").center(y, z).circle(HOLE_D / 2).extrude(THICK))
    solid = plate.val().clean()
    if not solid.isValid():
        raise RuntimeError("idler plate solid is not valid")
    return solid


def main():
    plate = build_plate()
    bb = plate.BoundingBox()
    print(f"Y idler plate: X[{bb.xmin:.1f},{bb.xmax:.1f}] Y[{bb.ymin:.1f},{bb.ymax:.1f}] "
          f"Z[{bb.zmin:.1f},{bb.zmax:.1f}]  vol {plate.Volume() / 1000:.1f} cm^3; "
          f"slot holes {SLOT_Y:.0f} mm behind the axle at +/-{SLOT_Z:.0f} mm")
    cq.exporters.export(cq.Workplane().add(plate), OUT_STEP)
    cq.exporters.export(cq.Workplane().add(plate), OUT_STL, tolerance=0.05, angularTolerance=0.1)
    print(f"  wrote {os.path.relpath(OUT_STEP, HERE)} and {os.path.relpath(OUT_STL, HERE)}")


if __name__ == "__main__":
    main()
