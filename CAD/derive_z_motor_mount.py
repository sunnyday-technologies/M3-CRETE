"""
Derive the M3-2 Z lead-screw motor mount (BOM id 24) from the GrokBot STEP.

This is a deliberately narrow M3-CRETE exception to CADCLAW's default
"place authored parts, do not author plates" rule, approved by Nick on
2026-10-12. It has the same shape as the ZPMM 6 mm-hole derivation in
CADCLAW examples/m3_crete/generate_zpmm_derived.py.

Source: CAD/Custom/Z_NEMA23_Leadscrew_Motor_Mount_GrokBot.step, authored by
GrokBot (2026-09-02) and kept unmodified. In its frame the screw/motor axis is
at (0, 2), the floor underside (Z=0) sits on the Z-post top, and a 6 mm tab
hangs 38.5 mm below the floor at Y[20,26]. The tab is clamped between the
post's open face and the top Y-rail end by the post-to-frame screws.

Measured against CAD/M3-2_V1.0_baseline.step, the source needs three fixes:

- the axis sits 18 mm inside the C-channel's open edge, so the 8 mm screw
  cuts ~2 mm into the channel floor; the Tr8x2 nut block (34x12x20, bore
  centred 6 mm from its face) bolted to the carriage plate needs 6 mm;
- the tab is 6 mm, but the V1.0 post-to-top-rail joint is 4 mm;
- the tab holes sit 1.47 mm above the top-rail end ports (rail Z 960-1000,
  ports at rail centre +/- 10 mm).

The derivation keeps the authored box (floor, coupler cavity, side window,
NEMA23 pilot, nut traps) unchanged. It moves the tab 12 mm toward the axis,
trims it to 4 mm, and moves its six holes to the port rows. The fillet on
the tab's post side is trimmed off, because it sat inside the post top.

Run:   python CAD/derive_z_motor_mount.py   (Python 3.11 + CadQuery 2.7)
"""
import os
import cadquery as cq

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "Custom", "Z_NEMA23_Leadscrew_Motor_Mount_GrokBot.step")
OUT_STEP = os.path.join(HERE, "Custom", "Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step")
OUT_STL = os.path.join(HERE, "Custom", "Z_NEMA23_Leadscrew_Motor_Mount_M3-2.stl")

AXIS_Y = 2.0                        # screw/motor axis in the source frame
AXIS_INSET = 6.0                    # axis -> channel open face (nut block bore centre)
TAB_Y0_SRC = 20.0                   # source tab: post-side face
TAB_T = 4.0                         # V1.0 post-to-top-rail joint thickness
TAB_Y0 = AXIS_Y + AXIS_INSET        # 8: derived tab post-side face = channel open face
TAB_SHIFT = TAB_Y0 - TAB_Y0_SRC     # -12
TAB_ZMIN = -38.5
LEG_X = (13.0, 40.0)                # tab legs at |X| in [13, 40]; centre gap clears the channel
HOLE_R = 3.1
# Asymmetric C-Beam end-port pattern: X +/-10 and +/-30 on the upper row,
# X +/-30 on the lower row (the open channel removes the middle pair).
HOLES_SRC = [(x, -8.53) for x in (-30.0, -10.0, 10.0, 30.0)] + [(x, -28.53) for x in (-30.0, 30.0)]
HOLES = [(x, -10.0) for x in (-30.0, -10.0, 10.0, 30.0)] + [(x, -30.0) for x in (-30.0, 30.0)]
BIG = 400.0


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _y_cylinders(points, r):
    """Cylinders along Y through the tab at (x, z) points."""
    out = None
    for x, z in points:
        c = cq.Solid.makeCylinder(r, TAB_T + 2.0, cq.Vector(x, TAB_Y0 - 1.0, z), cq.Vector(0, 1, 0))
        out = c if out is None else out.fuse(c)
    return out


def build_mount():
    src = cq.importers.importStep(SRC).val().Solids()[0]
    body = src.intersect(_box(-BIG, BIG, -BIG, BIG, 0.0, BIG))
    tab = src.intersect(_box(-BIG, BIG, -BIG, BIG, -BIG, 0.0))
    tab = tab.translate(cq.Vector(0, TAB_SHIFT, 0))
    tab = tab.intersect(_box(-BIG, BIG, TAB_Y0, TAB_Y0 + TAB_T, -BIG, 0.0))
    legs = (_box(LEG_X[0], LEG_X[1], TAB_Y0, TAB_Y0 + TAB_T, TAB_ZMIN, 0.0)
            .fuse(_box(-LEG_X[1], -LEG_X[0], TAB_Y0, TAB_Y0 + TAB_T, TAB_ZMIN, 0.0)))
    plugs = _y_cylinders(HOLES_SRC, HOLE_R + 0.05).intersect(legs)
    tab = tab.fuse(plugs).clean().cut(_y_cylinders(HOLES, HOLE_R)).clean()
    mount = body.fuse(tab).clean()
    solids = mount.Solids()
    if len(solids) != 1 or not solids[0].isValid():
        raise RuntimeError(f"derived mount is not one valid solid ({len(solids)} solids)")
    return solids[0]


def main():
    mount = build_mount()
    bb = mount.BoundingBox()
    print(f"derived mount: X[{bb.xmin:.2f},{bb.xmax:.2f}] Y[{bb.ymin:.2f},{bb.ymax:.2f}] "
          f"Z[{bb.zmin:.2f},{bb.zmax:.2f}]  vol {mount.Volume():.0f} mm^3")
    cq.exporters.export(cq.Workplane().add(mount), OUT_STEP)
    cq.exporters.export(cq.Workplane().add(mount), OUT_STL, tolerance=0.05, angularTolerance=0.1)
    print(f"  wrote {os.path.relpath(OUT_STEP, HERE)} and {os.path.relpath(OUT_STL, HERE)}")


if __name__ == "__main__":
    main()
