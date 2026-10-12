"""
Measure the M3-2 Z carriage travel (lead-screw Z) from the assembly.

Moving set: every part that rides the Z carriages, i.e. lies wholly inside
MOVING_Z_BAND in the as-modelled pose (gantry beams, carriage plates and
wheels, Y/X drive, nut blocks). Static set: everything else, except the Z
posts (the carriage wheels ride along them) and the lead screws (the nut
blocks run on them).

For every moving/static pair whose XY footprints overlap by more than
SLIDE_TOL, with the static part wholly above (or below) the moving one, the
contact offset is found by conservative advancement: translate by the current
minimum distance (BRepExtrema) until the gap closes. A move no longer than the
minimum distance cannot pass through the other part, so the first contact is
exact to TOUCH. Parts flush on a shared vertical face (a carriage plate and
the bottom holder both sit on the post's open face) touch without blocking:
a solid-solid touch only counts once moving on would interpenetrate, else the
sweep slides on in PROBE steps and bisects to the real contact.
The stroke is the up travel plus the down travel from the modelled pose; the
down limit should be the hard-stop blocks (id 91).

A lead screw does not slip like a belt, so firmware position_max must stay
below the stroke: with Z=0 at the build surface,
    position_max <= position_endstop + stroke - MARGIN

Run:   python CAD/z_travel.py [STEP]      (default CAD/M3-2_Assembly.step)
"""
import os, sys, math
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

HERE = os.path.dirname(__file__)
MOVING_Z_BAND = (150.0, 700.0)
EXCLUDE = ("cbeam_Zpost", "leadscrew_")
TOUCH = 0.01          # mm: contact tolerance
SLIDE_TOL = 0.1       # mm: XY overlap below this is flush sliding, not a stop
PROBE = 1.0           # mm: step while sliding along a flush face
MARGIN = 10.0         # mm kept between position_max and the measured stroke


def _dist(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


def _penetrates(a, b):
    """True if two shapes share volume. Shells (the C-beams) have no volume,
    so a touch involving one always counts as contact."""
    if a.ShapeType() != "Solid" or b.ShapeType() != "Solid":
        return True
    c = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    c.Build()
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(c.Shape(), g)
    return g.Mass() > 1e-3


def _xy_overlap(a, b, tol=SLIDE_TOL):
    return (a.xmin < b.xmax - tol and b.xmin < a.xmax - tol and
            a.ymin < b.ymax - tol and b.ymin < a.ymax - tol)


def classify(named_shapes):
    """Split (name, world_shape) pairs into moving and static sets."""
    moving, static = [], []
    for name, s in named_shapes:
        if name.startswith(EXCLUDE):
            continue
        bb = s.BoundingBox()
        inside = MOVING_Z_BAND[0] < bb.zmin and bb.zmax < MOVING_Z_BAND[1]
        (moving if inside or name.startswith("nut_block_") else static).append((name, s, bb))
    return moving, static


def _contact(m, s, sign, limit):
    """Smallest Z offset (sign=+1 up, -1 down) at which m is stopped by s, or None past limit."""
    at = lambda t: m.translate(cq.Vector(0, 0, sign * t))
    t = 0.0
    while t <= limit:
        g = _dist(at(t), s)
        if g >= TOUCH:
            t += g
            continue
        if _penetrates(at(t + PROBE), s):
            lo, hi = t, t + PROBE              # touching at lo, interpenetrating at hi
            while hi - lo > TOUCH:
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if _penetrates(at(mid), s) else (mid, hi)
            return lo
        t += PROBE                             # flush graze: slide on
    return None


def _limit(moving, static, sign):
    pairs = []
    for mn, m, mb in moving:
        for sn, s, sb in static:
            if not _xy_overlap(mb, sb):
                continue
            gap = sb.zmin - mb.zmax if sign > 0 else mb.zmin - sb.zmax
            if gap >= -TOUCH:
                pairs.append((max(gap, 0.0), mn, m, sn, s))
    pairs.sort(key=lambda p: p[0])
    best, best_pair = math.inf, None
    for gap, mn, m, sn, s in pairs:
        if gap >= best:
            break
        t = _contact(m, s, sign, best)
        if t is not None and t < best:
            best, best_pair = t, (mn, sn)
    return best, best_pair


def measure(named_shapes):
    moving, static = classify(named_shapes)
    up, up_pair = _limit(moving, static, +1)
    down, down_pair = _limit(moving, static, -1)
    return dict(up=up, up_pair=up_pair, down=down, down_pair=down_pair,
                stroke=up + down, n_moving=len(moving), n_static=len(static))


def assembly_shapes(assy):
    return [(c.name, c.obj.moved(c.loc)) for c in assy.children]


def report(r):
    print(f"Z travel: {r['n_moving']} moving parts vs {r['n_static']} static parts")
    print(f"  up   {r['up']:7.2f} mm  first contact: {r['up_pair'][0]} -> {r['up_pair'][1]}")
    print(f"  down {r['down']:7.2f} mm  first contact: {r['down_pair'][0]} -> {r['down_pair'][1]}")
    print(f"  stroke {r['stroke']:7.2f} mm  ->  position_max <= position_endstop + "
          f"{math.floor(r['stroke'] - MARGIN)} (stroke - {MARGIN:.0f} mm margin)")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "M3-2_Assembly.step")
    report(measure(assembly_shapes(cq.Assembly.importStep(step))))
