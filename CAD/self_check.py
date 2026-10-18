"""
M3-CRETE self-check — runs after m3_2_assembly.py to catch regressions
before a visual review. Fails fast on parts at obviously wrong positions
(cbeam-adjacency errors, corner connectors that are too thick, motors far
from any Z-post, etc.). Also runs a bbox-overlap interference pre-filter
and a BRepAlgoAPI_Common check on suspicious pairs, and checks the lead-screw
Z stack (BOM v2.9.0) against the measured carriage travel and the firmware.

Run:
  python CAD/self_check.py [candidate.step]  (Python 3.11 + CadQuery 2.7)

Exit code 0 if clean, 1 if any issue found.
"""
import sys, os, re, importlib.util
from collections import Counter

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, "_preview"), exist_ok=True)
spec = importlib.util.spec_from_file_location("m3_asm",
                                              os.path.join(HERE, "m3_2_assembly.py"))
mod = importlib.util.module_from_spec(spec)
_null = open(os.path.join(HERE, "_preview", "null.txt"), "w")
sys.stdout = _null
spec.loader.exec_module(mod)
sys.stdout = sys.__stdout__

import cadquery as cq
import z_travel

# With a path, check the saved/reimported artifact using the same design
# parameters. Without one, check the generator's in-memory candidate.
if len(sys.argv) > 1:
    mod.assy = cq.Assembly.importStep(sys.argv[1])

comp = mod.assy.toCompound()
raw_parts = list(comp.Solids()) + list(comp.Shells())

# Dedup by bbox key (solids and their outer shells both appear)
seen = set()
parts = []
for s in raw_parts:
    bb = s.BoundingBox()
    k = (round(bb.xmin, 1), round(bb.ymin, 1), round(bb.zmin, 1),
         round(bb.xmax, 1), round(bb.ymax, 1), round(bb.zmax, 1))
    if k in seen:
        continue
    seen.add(k)
    parts.append(s)

# Signature-to-label map
LABELS = {
    (40.0, 80.0, 1000.0): 'cbeam',
    (65.0, 69.0, 69.0):   'bracket',
    (56.4, 56.4, 76.6):   'motor',
    (69.3, 69.3, 76.6):   'motor',          # Y motor, turned ~19 deg on its rail face (2026-10-12)
    (10.2, 23.9, 23.9):   'vwheel',
    (14.0, 15.0, 15.0):   'pulley',
    (14.2, 18.0, 18.0):   'idler',      # id 93 Y return idler envelope (20T toothless, 10 mm belt)
    (3.0, 88.0, 127.0):   'plate',
    (6.0, 40.0, 80.0):    'shim',       # center-spreader shims, 6 mm since 2026-10-12
    (4.0, 80.0, 97.0):    'zmount',     # id 75 printed plate, now at the 2 Y-motor positions only
    (6.0, 80.0, 100.0):   'z-bottom-plate',  # id 79, 6 mm post-to-bottom-rail spacer (belt era: bot_spacer_idler, 4 mm)
    (4.0, 160.0, 280.0):  'tbracket',
    (5.0, 30.0, 30.0):    'idler-brk',        # v3 placeholder idler brackets (replaced by the id 66 plate)
    (3.0, 34.0, 36.0):    'idler-plate',      # id 66 printed Y idler plate on the channel floor (2026-10-13)
    # X-carriage authored hardware (M3-2_nudge.step)
    (5.0, 16.0, 16.0):    'xcarr_bolt',     # M5 SHCS heads (carriage hardware)
    (9.0, 9.0, 31.5):     'xcarr_axle',     # V-wheel axle / shoulder bolt
    (1.0, 10.0, 10.0):    'xcarr_washer',   # thin washer
    (3.2, 10.0, 10.0):    'xcarr_spacer',   # 6mm spacer (sorted dims as 3.2x10x10 due to import)
    # 2040 V-slot reinforcement inserts (2026-04-29; B+b pattern)
    (20.0, 40.0, 1000.0): '2040_insert',    # 1m centered in each X-direction 4080 (3 total)
    # Lead-screw Z (2026-10-12; BOM v2.9.0)
    (68.0, 80.0, 86.5):   'z-motor-mount',  # id 24, derived GrokBot mount
    (8.0, 8.0, 1000.0):   'leadscrew',      # id 87
    (12.0, 20.0, 34.0):   'nut-block',      # id 87
    (19.0, 19.0, 20.0):   'coupler',        # id 88 envelope
    (7.0, 14.0, 14.0):    'collar',         # id 90
    (7.0, 22.0, 22.0):    'bearing-608',    # id 89 envelope
    (28.1, 34.0, 45.0):   'z-bottom-holder',  # id 91 (axis 5 mm inside the open face)
}

def sig(s):
    bb = s.BoundingBox()
    return tuple(sorted([
        round(bb.xmax - bb.xmin, 1),
        round(bb.ymax - bb.ymin, 1),
        round(bb.zmax - bb.zmin, 1),
    ]))

def label_of(s):
    d = sig(s)
    # The 8x16x5 thrust-bearing envelope (id 92) shares its bbox with the
    # X-carriage bolt heads; the thrust bearings are the ones on the post tops.
    if d == (5.0, 16.0, 16.0) and s.BoundingBox().zmin > 900:
        return 'thrust-brg'
    if d in LABELS: return LABELS[d]
    if d[0] == 1.5 and d[1] == 6.0: return 'belt'
    return 'other'

# ---------- CHECK 1: inventory counts match expectation ----------
inv = Counter(label_of(s) for s in parts)
EXPECTED = {
    'cbeam': 17,
    'bracket': 0,
    'motor': 7,            # 4 Z (shaft down on the mounts) + 1 X at (56.4, 56.4, 76.6); 2 Y turned ~19 deg at (69.3, 69.3, 76.6)
    'vwheel': 32,          # all authored in M3-2_V1.0 (16 Z + 8 Y + 8 X)
    'pulley': 3,           # 2 Y + 1 X (Z is lead-screw driven)
    'idler': 2,            # one Y return idler per Y rail, inside its channel
    'plate': 8,
    'shim': 2,
    'zmount': 0,           # id 75 Y-motor plates dropped: Y motors bolt straight to the rail face
    'zcap': 0,
    'idler-brk': 0,        # v3 placeholders, replaced by the id 66 idler plates
    'idler-plate': 2,      # id 66, one per Y idler on the channel floor
    'z-bottom-plate': 4,   # id 79: bottom only; the top plates became the id 24 mounts
    'ymount': 0,           # subsumed by z_motor_mount at Y-motor positions
    'tbracket': 2,
    'belt': 4,             # 2 left-Y + 2 right-Y (the 8 Z runs are gone)
    'xcarr_bolt': 8,       # M5 SHCS at X-carriage
    'xcarr_axle': 4,       # V-wheel axles (one carriage side modeled)
    'xcarr_washer': 4,
    'xcarr_spacer': 4,     # 6mm wheel spacers (one side)
    '2040_insert': 3,      # 1m 2040 V-slot inserts (B+b pattern, all authored in V1.0)
    'other': 12,           # remaining X-carriage hardware + X-belt strand
    'z-motor-mount': 4,
    'leadscrew': 4,
    'nut-block': 4,
    'coupler': 4,
    'collar': 8,           # above and below each mount floor
    'thrust-brg': 8,       # id 92, with the collars
    'bearing-608': 4,
    'z-bottom-holder': 4,
}
problems = []
notes = []
print(f"Total parts: {len(parts)}")
print()
print("Inventory:")
for k in sorted(set(list(inv.keys()) + list(EXPECTED.keys()))):
    got, want = inv.get(k, 0), EXPECTED.get(k, 0)
    marker = ' ' if got == want else 'X'
    print(f"  [{marker}] {k:15s} {got:4d} (expected {want})")
    if got != want:
        problems.append(f"inventory: {k} got {got}, expected {want}")

# ---------- CHECK 2: combined motor-mount/spacer sanity ----------
# Each zmount should be ~4 x 80 x 97 mm.
for s in parts:
    lbl = label_of(s)
    if lbl == 'zmount':
        bb = s.BoundingBox()
        dims = sorted([bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin])
        if dims[0] > 6:
            problems.append(f"zmount dims {dims} — thinnest axis > 6mm")
        if not (78 <= dims[1] <= 82 and 95 <= dims[2] <= 99):
            problems.append(f"zmount dims {dims} - expected roughly 4 x 80 x 97")
    elif lbl == 'zcap':
        bb = s.BoundingBox()
        dims = sorted([bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin])
        if dims[0] > 8:
            problems.append(f"zcap dims {dims} — thinnest axis > 8mm")

    # ymount dimension check disabled while user re-authors the Y-motor spacers

# ---------- CHECK 3: Z-motors seated on their mounts, coaxial with a screw ----------
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

def center(s):
    bb = s.BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5
def dist_xy(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
def common_volume(a, b):
    c = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    c.Build()
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(c.Shape(), g)
    return g.Mass()
def gap(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()

motors  = [s for s in parts if label_of(s) == 'motor']
mounts  = [s for s in parts if label_of(s) == 'z-motor-mount']
screws  = [s for s in parts if label_of(s) == 'leadscrew']
for m in motors:
    mc = center(m)
    if mc[2] < 900:
        continue  # Y-motors and the X-motor sit at gantry height
    mount = min(mounts, key=lambda b: dist_xy(mc, center(b)), default=None)
    screw = min(screws, key=lambda b: dist_xy(mc, center(b)), default=None)
    if mount is None or screw is None:
        problems.append(f"Z-motor at ({mc[0]:.0f},{mc[1]:.0f},{mc[2]:.0f}) has no mount or lead screw")
        continue
    if dist_xy(mc, center(screw)) > 0.5:
        problems.append(f"Z-motor at ({mc[0]:.0f},{mc[1]:.0f}) is {dist_xy(mc, center(screw)):.1f} mm off its lead-screw axis")
    if gap(m, mount) > 0.05 or common_volume(m, mount) > 1.0:
        problems.append(f"Z-motor at ({mc[0]:.0f},{mc[1]:.0f}) is not seated on its mount "
                        f"(gap {gap(m, mount):.2f} mm, overlap {common_volume(m, mount):.1f} mm^3)")

# ---------- CHECK 4: plate vs cbeam interference (catches clipping) ----------
def bb_overlap(a, b, tol=-0.01):
    b1, b2 = a.BoundingBox(), b.BoundingBox()
    return (b1.xmin < b2.xmax + tol and b2.xmin < b1.xmax + tol and
            b1.ymin < b2.ymax + tol and b2.ymin < b1.ymax + tol and
            b1.zmin < b2.zmax + tol and b2.zmin < b1.zmax + tol)

# Check actual geometry. Rebuilding shells here used to hide missing cavity
# walls and end faces, so reject them instead of testing a filled proxy.
invalid = [s for s in parts if s.ShapeType() != "Solid" or not s.isValid()]
if invalid:
    print(f"SELF-CHECK FAILED — {len(invalid)} non-solid or invalid operands; no reconstruction")
    sys.exit(1)
solids = [(label_of(s), s) for s in parts]
for la, a in solids:
    if la != 'plate':
        continue
    for lb, b in solids:
        if lb != 'cbeam' or not bb_overlap(a, b):
            continue
        v = common_volume(a, b)
        if v > 0.5:
            ac, bc = center(a), center(b)
            problems.append(
                f"plate at ({ac[0]:.0f},{ac[1]:.0f},{ac[2]:.0f}) "
                f"clips cbeam at ({bc[0]:.0f},{bc[1]:.0f},{bc[2]:.0f}) by {v:.0f} mm^3")

# ---------- CHECK 5: motor-mount plates span shim+motor zone (Z > 900) ----------
# The authored bracket is cloned to both Z-motor corners (Z>900) AND Y-motor
# positions (Z~370). Only enforce the Z>900 rule on plates near a Z-post
# corner (cx ≈ 0 or NX_RIGHT and |cy - 18| < 10 or |cy - 1022| < 10).
for s in parts:
    lbl = label_of(s)
    if lbl in ('zmount', 'zcap'):
        bb = s.BoundingBox()
        cx = (bb.xmin + bb.xmax) / 2
        cy = (bb.ymin + bb.ymax) / 2
        cz = (bb.zmin + bb.zmax) / 2
        is_z_corner = (cx < 50 or cx > 2030) and (cy < 30 or cy > 1010)
        if is_z_corner and bb.zmin < 900:
            problems.append(f"{lbl} at ({cx:.0f},{cy:.0f},{cz:.0f}) below Z=900")

# ---------- CHECK 6: lead screw on the C-channel centreline, AXIS_INSET inside the open face ----------
# The posts' C opens toward the frame interior: +Y on the front posts, -Y on the rear.
posts = [s for s in parts if label_of(s) == 'cbeam' and s.BoundingBox().zlen > 900]
frame_cy = sum(center(p)[1] for p in posts) / max(len(posts), 1)
for p in posts:
    pb, pc = p.BoundingBox(), center(p)
    screw = min(screws, key=lambda s: dist_xy(pc, center(s)), default=None)
    if screw is None or dist_xy(pc, center(screw)) > 40:
        problems.append(f"Z-post at ({pc[0]:.0f},{pc[1]:.0f}) has no lead screw")
        continue
    sc = center(screw)
    inset = (pb.ymax - sc[1]) if pc[1] < frame_cy else (sc[1] - pb.ymin)
    if abs(sc[0] - pc[0]) > 0.1 or abs(inset - mod.AXIS_INSET) > 0.1:
        problems.append(f"lead screw at ({sc[0]:.1f},{sc[1]:.1f}) is {sc[0]-pc[0]:+.1f} mm off the post "
                        f"centre and {inset:.1f} mm inside the open face (want 0 and {mod.AXIS_INSET})")

# ---------- CHECK 7: lead-screw stack interference (true solids) ----------
# Uses the same actual `solids` list as CHECK 4, including supplier cavities.
STACK = ('z-motor-mount', 'leadscrew', 'nut-block', 'coupler', 'collar', 'thrust-brg',
         'bearing-608', 'z-bottom-holder')
KNOWN = {}   # owner-tracked overlaps reported but not failed (none open)
for i, (la, a) in enumerate(solids):
    if la not in STACK:
        continue
    for j, (lb, b) in enumerate(solids):
        if j == i or (lb in STACK and j < i) or not bb_overlap(a, b):
            continue
        v = common_volume(a, b)
        if v <= 1.0:
            continue
        ac = center(a)
        msg = f"{la} at ({ac[0]:.0f},{ac[1]:.0f},{ac[2]:.0f}) overlaps {lb} by {v:.0f} mm^3"
        if lb in KNOWN:
            notes.append(f"{msg} — {KNOWN[lb]}")
        else:
            problems.append(msg)

# ---------- CHECK 9: one Y return idler per Y rail, fully inside its open channel ----------
# Owner rule (2026-10-12): the idler envelope sits fully inside the Y-gantry
# rail's open C-channel, a few mm behind the Z carriage plate that caps the end.
IDLER_PLATE_CLEARANCE = 2.0
yrails = [(s, sol) for (l, sol), s in zip(solids, parts)
          if l == 'cbeam' and s.BoundingBox().ylen > 900 and 300 < center(s)[2] < 600]
idlers = [s for s in parts if label_of(s) == 'idler']
zplates = [s for s in parts if label_of(s) == 'plate' and s.BoundingBox().ylen < 3.5]
for rail, rail_solid in yrails:
    rb = rail.BoundingBox()
    left, x0, x1, z0, z1 = mod.channel_of(rb)
    at_rail = [s for s in idlers if abs(center(s)[0] - (rb.xmin + rb.xmax) / 2) < 40]
    if len(at_rail) != 1:
        problems.append(f"Y rail at X={center(rail)[0]:.0f}: {len(at_rail)} return idlers, expected 1")
        continue
    ib = at_rail[0].BoundingBox()
    if not mod.in_channel(ib, rb):
        problems.append(f"Y idler at ({center(at_rail[0])[0]:.0f},{center(at_rail[0])[1]:.0f}) is not fully "
                        f"inside its rail channel X[{x0:.1f},{x1:.1f}] Z[{z0:.1f},{z1:.1f}]")
    if common_volume(at_rail[0], rail_solid) > 1.0:
        problems.append(f"Y idler at X={center(at_rail[0])[0]:.0f} overlaps its rail")
    cap = min((p for p in zplates if abs(center(p)[0] - center(at_rail[0])[0]) < 70),
              key=lambda p: abs(center(p)[1] - center(at_rail[0])[1]), default=None)
    if cap is not None:
        cb = cap.BoundingBox()
        clear = ib.ymin - cb.ymax if center(cap)[1] < center(at_rail[0])[1] else cb.ymin - ib.ymax
        print(f"Y idler X={center(at_rail[0])[0]:.0f}: inside rail channel, {clear:.1f} mm behind the carriage plate")
        if clear < IDLER_PLATE_CLEARANCE:
            problems.append(f"Y idler at X={center(at_rail[0])[0]:.0f} is {clear:.1f} mm from the carriage plate "
                            f"(want >= {IDLER_PLATE_CLEARANCE})")
    # Its id 66 plate (owner, 2026-10-13): flat on the channel floor under the
    # idler, axle hole on the idler axis, the 2 T-nut holes on the floor slots,
    # clear of the idler and touching nothing else.
    ic = center(at_rail[0])
    plates66 = [(s, sol) for (l, sol), s in zip(solids, parts) if l == 'idler-plate'
                and abs(center(s)[0] - (rb.xmin + rb.xmax) / 2) < 40]
    if len(plates66) != 1:
        problems.append(f"Y rail at X={center(rail)[0]:.0f}: {len(plates66)} id 66 idler plates, expected 1")
        continue
    pl, pl_solid = plates66[0]
    pb = pl.BoundingBox()
    floor_x = x0 if left else x1
    on_floor = abs((pb.xmin if left else pb.xmax) - floor_x) <= 0.05
    gap_to_idler = (ib.xmin - pb.xmax) if left else (pb.xmin - ib.xmax)
    hole_c = [e.Center() for e in pl.Edges() if e.geomType() == "CIRCLE" and 2.0 < e.radius() < 3.5]
    axle = [h for h in hole_c if abs(h.y - ic[1]) <= 0.1 and abs(h.z - ic[2]) <= 0.1]
    rail_cz = (rb.zmin + rb.zmax) / 2
    slot_z = {round(h.z - rail_cz, 1) for h in hole_c if abs(abs(h.z - rail_cz) - mod.yip.SLOT_Z) <= 0.1}
    print(f"Y idler plate X={center(pl)[0]:.0f}: on the channel floor {on_floor}, {gap_to_idler:.2f} mm under the "
          f"idler, axle hole on the idler axis {bool(axle)}, slot holes at Z {sorted(slot_z)}")
    if not on_floor or not mod.in_channel(pb, rb):
        problems.append(f"Y idler plate at X={center(pl)[0]:.0f} is not flat on its channel floor inside the channel")
    if gap_to_idler <= 0:
        problems.append(f"Y idler plate at X={center(pl)[0]:.0f} touches its idler ({gap_to_idler:.2f} mm)")
    if not axle or len(slot_z) != 2:
        problems.append(f"Y idler plate at X={center(pl)[0]:.0f}: axle hole off the idler axis or slot holes "
                        f"not on both floor slots ({sorted(slot_z)})")
    for s0, (lb, b) in zip(parts, solids):
        if s0 is pl or not bb_overlap(pl, b):
            continue
        v = common_volume(pl_solid, b)
        if v > 0.5:
            problems.append(f"Y idler plate at X={center(pl)[0]:.0f} overlaps {lb} by {v:.0f} mm^3")

# ---------- CHECK 10: 6 mm post-to-end-beam frame joints ----------
# Measured on SN 001 (2026-10-12). Each Z post's open face sits FRAME_SPACER
# from the ends of the 1 m top and bottom Y rails beside it.
yflat = [s for s in parts if label_of(s) == 'cbeam' and s.BoundingBox().ylen > 900
         and not 300 < center(s)[2] < 600]
for p in posts:
    pb, pc = p.BoundingBox(), center(p)
    front = pc[1] < frame_cy
    for r in yflat:
        rb = r.BoundingBox()
        if not (rb.xmin < pc[0] < rb.xmax):
            continue
        g = (rb.ymin - pb.ymax) if front else (pb.ymin - rb.ymax)
        if abs(g - mod.FRAME_SPACER) > 0.1:
            problems.append(f"Z-post at ({pc[0]:.0f},{pc[1]:.0f}) is {g:.1f} mm from the Y rail end at "
                            f"Z={center(r)[2]:.0f} (want {mod.FRAME_SPACER})")

# ---------- CHECK 11: Z carriage plate running gap to the post's open face ----------
# SN 001 runs each Z carriage plate ~1 mm off its post's open face (owner,
# 2026-10-12). The nut block is bolted flush to the plate, so the gap also
# sets the screw axis (CHECK 6).
Z_PLATE_GAP_TOL = 0.1
nut_blocks = [s for s in parts if label_of(s) == 'nut-block']
for p in posts:
    pb, pc = p.BoundingBox(), center(p)
    front = pc[1] < frame_cy
    open_y = pb.ymax if front else pb.ymin
    plate = min((z for z in zplates if abs(center(z)[0] - pc[0]) < 70),
                key=lambda z: abs(center(z)[1] - open_y), default=None)
    if plate is None:
        problems.append(f"Z-post at ({pc[0]:.0f},{pc[1]:.0f}) has no carriage plate")
        continue
    zb = plate.BoundingBox()
    g = (zb.ymin - open_y) if front else (open_y - zb.ymax)
    print(f"Z plate at ({pc[0]:.0f},{pc[1]:.0f}): {g:.2f} mm running gap to the post open face")
    if abs(g - mod.Z_PLATE_GAP) > Z_PLATE_GAP_TOL:
        problems.append(f"Z carriage plate at ({center(plate)[0]:.0f},{center(plate)[1]:.0f}) runs {g:.2f} mm off "
                        f"its post's open face (want {mod.Z_PLATE_GAP} +/- {Z_PLATE_GAP_TOL})")
    nb = min(nut_blocks, key=lambda s: dist_xy(pc, center(s)), default=None)
    if nb is None or gap(nb, plate) > 0.05:
        problems.append(f"Z nut block at post ({pc[0]:.0f},{pc[1]:.0f}) is not flush on its carriage plate")

# ---------- CHECK 12: Y motors straight on the Y-rail face, no plate ----------
# Owner, 2026-10-12: no id 75 plate. Each Y motor's flange sits on its rail's
# open face, 2 M5 into T-nuts in the two face slots, turned so one diagonal
# hole pair is on the slot centrelines, which centres it on the channel. Its
# shaft tip reaches past the channel floor; SN 001 drills a clearance hole
# there (Nick), so that overlap is a note, not a failure.
Y_MOTOR_PLATE_CLEAR = 1.0
SHAFT_TIP_MAX = 40.0          # mm^3: the 8 mm shaft 0.6 mm into the channel floor is ~30
pulleys = [s for s in parts if label_of(s) == 'pulley']
ymotors = [m for m in motors if center(m)[2] < 900 and m.BoundingBox().xlen > 70]
if len(ymotors) != 2:
    problems.append(f"expected 2 Y motors, found {len(ymotors)}")
for m in ymotors:
    mc = center(m)
    rail, rail_solid = min(yrails, key=lambda rs: abs(center(rs[0])[0] - mc[0]))
    rb, rc = rail.BoundingBox(), center(rail)
    left = rc[0] < mc[0]
    face_x = rb.xmax if left else rb.xmin
    flange = max((f for f in m.Faces() if f.geomType() == "PLANE" and f.normalAt().x * (-1 if left else 1) > 0.99),
                 key=lambda f: f.Area())
    fb = flange.BoundingBox()
    ay, az = (fb.ymin + fb.ymax) / 2, (fb.zmin + fb.zmax) / 2
    tag = f"Y motor at X={mc[0]:.0f}"
    if abs(flange.Center().x - face_x) > 0.05:
        problems.append(f"{tag}: flange {abs(flange.Center().x - face_x):.2f} mm off the rail's open face")
    if abs(az - rc[2]) > 0.1:
        problems.append(f"{tag}: axis {az - rc[2]:+.2f} mm off the channel centre")
    pul = min(pulleys, key=lambda s: dist_xy((mc[0], ay), (center(s)[0], center(s)[1])) + abs(center(s)[2] - az))
    if abs(center(pul)[1] - ay) > 0.1 or abs(center(pul)[2] - az) > 0.1:
        problems.append(f"{tag}: not coaxial with its drive pulley")
    holes = [e.Center() for e in flange.Edges() if e.geomType() == "CIRCLE" and 2.0 < e.radius() < 3.5]
    on_slots = [h for h in holes if abs(abs(h.z - rc[2]) - mod.FACE_SLOT_OFFSET) <= 0.1]
    if len(on_slots) != 2 or abs(on_slots[0].z - on_slots[1].z) < 1.0:
        problems.append(f"{tag}: {len(on_slots)} flange holes on the face-slot centrelines (want one in each slot)")
    cap = min((z for z in zplates if abs(center(z)[0] - mc[0]) < 70), key=lambda z: abs(center(z)[1] - ay))
    clear = gap(m, cap)
    print(f"{tag}: on the rail face, centred, coaxial with its pulley; holes on both face slots; "
          f"{clear:.2f} mm to the Z carriage plate")
    if clear < Y_MOTOR_PLATE_CLEAR:
        problems.append(f"{tag}: {clear:.2f} mm from the Z carriage plate (want >= {Y_MOTOR_PLATE_CLEAR})")
    for s0, (lb, b) in zip(parts, solids):
        if s0 is m or s0 is pul or not bb_overlap(m, b):
            continue
        v = common_volume(m, b)
        if v <= 1.0:
            continue
        if b is rail_solid and v <= SHAFT_TIP_MAX:
            notes.append(f"{tag}: shaft tip {v:.0f} mm^3 into the channel floor — SN 001 drills a clearance hole")
        else:
            problems.append(f"{tag} overlaps {lb} at ({center(b)[0]:.0f},{center(b)[1]:.0f},{center(b)[2]:.0f}) "
                            f"by {v:.0f} mm^3")

# ---------- CHECK 8: firmware position_max inside the measured Z travel ----------
travel = z_travel.measure(z_travel.assembly_shapes(mod.assy))
print()
z_travel.report(travel)
cfg = open(os.path.join(HERE, "..", "firmware", "steppers.cfg"), encoding="utf-8").read()
zsec = cfg.split("[stepper_z]", 1)[1].split("\n[", 1)[0]
pmax = float(re.search(r"^position_max:\s*([-\d.]+)", zsec, re.M).group(1))
pend = float(re.search(r"^position_endstop:\s*([-\d.]+)", zsec, re.M).group(1))
if pmax - pend > travel["stroke"] - z_travel.MARGIN:
    problems.append(f"firmware [stepper_z] position_max {pmax:g} - position_endstop {pend:g} = "
                    f"{pmax - pend:g} mm exceeds the measured stroke {travel['stroke']:.1f} mm "
                    f"minus the {z_travel.MARGIN:g} mm margin")

# ---------- REPORT ----------
print()
for n in notes:
    print(f"NOTE (known, not failing): {n}")
if problems:
    print(f"SELF-CHECK FAILED — {len(problems)} issue(s):")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
else:
    print("SELF-CHECK PASSED")
    sys.exit(0)
