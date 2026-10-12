"""
M3-CRETE M3-2 Assembly — v4 (lead-screw Z on the V1.0 baseline)

Loads CAD/M3-2_V1.0_baseline.step: the 146-part V1.0 assembly (2026-04-29
freeze) that the v3 filter-and-replace pass built from Nick's Fusion export.
That export (M3-2_V1.0.step) is no longer available, so the v3 fixups
(parametric C-beams, corner fixups, bracket cloning, gusset import, FR motor
clone) are already baked into the baseline and are not repeated here.

On top of the baseline this script:
  - drops the belt-driven Z: 8 vertical belt runs, 4 Z pulleys and the FR
    shaft leftover, 4 bottom Z idlers, the 4 horizontal-shaft Z motors and
    the 4 top id 79 plates that carried them
  - drops exact duplicate placements carried over from v3 (gussets, idler
    brackets, one Y return idler)
  - keeps one Y return idler per Y-gantry rail, fully inside the rail's open
    C-channel, and drops the strays and v3-generated extras (owner 2026-10-12)
  - drops the 2 printed id 75 Y-motor plates and bolts each Y motor straight
    to its rail's open face, turned ~19 deg so one diagonal hole pair lands
    on the two face slots, centred on the channel with its pulley, belt
    strands and return idler (owner 2026-10-12)
  - moves the frame to the measured 6 mm post-to-end-beam spacers (owner
    2026-10-12; V1.0 modelled 4 mm): each post moves 2 mm out along Y with
    the parts fixed to or riding on it, and the bottom plates and spreader
    shims are rebuilt 6 mm thick
  - stands each Z carriage plate 1 mm off its post's open face, the running
    gap on SN 001 (owner 2026-10-12; V1.0 modelled the plates flush): the 4
    plates and their 16 V-wheels end up 1 mm nearer the frame interior
  - adds a lead-screw stack on every Z post (BOM v2.9.0, owner decisions
    2026-10-11/12):
      motor mount  id 24  CAD/Custom/Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step
                          (derived from the GrokBot mount, see
                          derive_z_motor_mount.py)
      motor        id 19  baseline NEMA23, turned shaft-down
      coupler      id 88  envelope
      collars      id 90  CAD/Components/Hardware/Lock Collar 8mm.step,
                          above and below the mount floor
      thrust brg   id 92  envelope, between each collar and the mount floor
      screw        id 87  Tr8x2 x 1000, plain 8 mm rod (linear stock)
      nut block    id 87  CAD/Advanced/Hardware/8mm Acme Nut Block.step body,
                          bolted to the Z carriage plate (id 23)
      bottom holder id 91 CAD/Custom/Z_Bottom_Bearing_Holder_M3-2.step
                          (z_bottom_holder.py): 608ZZ seat + hard stop, on
                          the bottom plate's top edge
      608ZZ        id 89  envelope, in the bottom holder
    Envelopes are dimensioned stand-ins for vendor parts with no local STEP
    (owner decision 2026-10-12). They carry no holes.
  - writes CAD/M3-2_Assembly.step (never the baseline)

Screw axis: centre of the post's C-channel, AXIS_INSET mm inside the open
face. The nut block (bore centred 6 mm from its face) is bolted flush to the
carriage plate, which runs Z_PLATE_GAP off the open face.
"""
import cadquery as cq
from cadquery import Assembly, Color, Location
import math, os, time
import z_bottom_holder as zbh

HERE = os.path.dirname(__file__)
BASELINE    = os.path.join(HERE, "M3-2_V1.0_baseline.step")
OUT         = os.path.join(HERE, "M3-2_Assembly.step")
MOUNT_STEP  = os.path.join(HERE, "Custom", "Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step")
HOLDER_STEP = zbh.OUT_STEP
COLLAR_STEP = os.path.join(HERE, "Components", "Hardware", "Lock Collar 8mm.step")
NUT_STEP    = os.path.join(HERE, "Advanced", "Hardware", "8mm Acme Nut Block.step")

# ============================================================
# Lead-screw stack geometry (mm)
# ============================================================
POST_TOP      = 1000.0      # Z-post top = mount floor underside
Z_PLATE_GAP   = 1.0         # Z carriage plate -> post open face, running gap (SN 001, 2026-10-12)
NUT_BORE_INSET = 6.0        # nut block bore centre -> its plate-side face
AXIS_INSET    = NUT_BORE_INSET - Z_PLATE_GAP   # 5: screw axis -> channel open face
MOUNT_AXIS_Y  = 2.0         # screw axis in the mount STEP frame
MOUNT_FLOOR   = 6.0         # mount floor thickness
MOUNT_TOP     = 48.0        # mount top face (motor face) above its floor underside
SCREW_D       = 8.0
SCREW_L       = 1000.0      # BOM id 87
SHAFT_GAP     = 1.0         # screw top end below the motor shaft tip, inside the coupler
COUPLER_D     = 19.0        # 8x8 coupler envelope; must fit the 34 mm mount cavity
COUPLER_L     = 20.0
THRUST_D      = 16.0        # 8x16x5 thrust bearing envelope (BOM id 92)
THRUST_H      = 5.0
BORE_D        = 8.0
assert AXIS_INSET == zbh.AXIS_INSET

# Frame and Y-rail geometry (mm)
FRAME_SPACER  = 6.0         # post-to-end-beam spacer, measured on SN 001 (2026-10-12)
V1_SPACER     = 4.0         # what the V1.0 baseline modelled
POST_SHIFT    = FRAME_SPACER - V1_SPACER
CHANNEL_DEPTH = 20.0        # C-Beam 4080 open channel: 20 deep x 40 wide
CHANNEL_HALF_OPEN = 20.0
GEN_BRACKET_OFFSET = 15.0   # v3 placed a 5x30x30 bracket 15 mm outboard of each idler
# Y return idler (BOM id 93, 20T toothless for the 10 mm belt): envelope of
# the reference part, axle along X. Owner rule: fully inside the Y rail's
# open channel, a few mm behind the carriage plate that caps the rail end.
IDLER_FLANGE_D, IDLER_FLANGE_T = 18.0, 1.5
IDLER_HUB_D, IDLER_TRACK = 12.1, 11.2      # 1.5 + 11.2 + 1.5 = 14.2 overall
IDLER_PLATE_GAP = 4.0
# Y motors (owner 2026-10-12): no id 75 plate. Each bolts straight to its Y
# rail's open face with 2 M5 into T-nuts in the two face slots, turned off
# parallel so one diagonal hole pair lands on the slot centrelines; that also
# centres it on the channel. Its shaft tip reaches 0.6 mm past the channel
# floor, where SN 001 drills a clearance hole.
NEMA23_HOLE_SQUARE = 47.14      # flange hole spacing
FACE_SLOT_OFFSET = 30.0         # C-Beam open-face slot centrelines, +/- from the channel centre
Y_MOTOR_TURN = math.degrees(math.asin(FACE_SLOT_OFFSET / (NEMA23_HOLE_SQUARE / math.sqrt(2)))) - 45.0  # 19.16
YMOUNT_SIG = (4.0, 80.0, 97.0)  # the dropped id 75 printed plate

# ============================================================
# Colors
# ============================================================
MTR   = Color(0.15, 0.15, 0.18)   # Motor black
SHAFT = Color(0.60, 0.60, 0.62)   # Shaft steel
IDL   = Color(0.85, 0.85, 0.88)   # Polished steel (collars)
BRASS = Color(0.80, 0.65, 0.25)   # Nut block
ENV   = Color(0.75, 0.45, 0.20)   # Vendor-part envelopes (bronze)
PRINT_COLOR = Color(0.59, 0.84, 0.00)   # Sunnyday trademark green (printed parts)


def world_bb(child):
    return child.obj.moved(child.loc).BoundingBox()


def sig_of(bb):
    return tuple(sorted(round(v, 1) for v in (bb.xlen, bb.ylen, bb.zlen)))


def bb_key(bb):
    return tuple(round(v, 1) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax))


def ring(od, idia, h):
    """Plain annulus along +Z from Z=0 (bearing / coupler envelope)."""
    return cq.Solid.makeCylinder(od / 2, h).cut(cq.Solid.makeCylinder(idia / 2, h))


def place(shape, local_axis, rot_deg, axis_xy, z):
    """Move `shape` so its local screw axis lands on the world axis at height z,
    turned rot_deg about Z (180 for rear posts, whose channel opens -Y)."""
    s = shape.translate(cq.Vector(-local_axis[0], -local_axis[1], 0))
    if rot_deg:
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rot_deg)
    return s.translate(cq.Vector(axis_xy[0], axis_xy[1], z))


print("M3-CRETE M3-2 Assembly v4.0 (lead-screw Z on V1.0 baseline)")
print(f"Loading {os.path.basename(BASELINE)}...")
t0 = time.time()
base = Assembly.importStep(BASELINE)
print(f"  {len(base.children)} children")

# ============================================================
# Classify the baseline
# ============================================================
posts = [c for c in base.children if c.name.startswith("cbeam_Zpost")]
post_bbs = [world_bb(c) for c in posts]
FRAME_CY = sum((b.ymin + b.ymax) / 2 for b in post_bbs) / len(post_bbs)


def near_post(bb, reach=60.0):
    cx, cy = (bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2
    return any(abs(cx - (p.xmin + p.xmax) / 2) < reach and abs(cy - (p.ymin + p.ymax) / 2) < reach
               for p in post_bbs)


def belt_z_role(bb):
    """Name the belt-Z role of a baseline part, or None if it stays."""
    sg = sig_of(bb)
    if sg[0] == 1.5 and sg[1] == 6.0 and bb.zlen > 900:
        return "Z belt run"
    if sg == (4.0, 80.0, 100.0) and bb.zmin > 900:
        return "top id 79 plate (belt-era motor mount)"
    if sg == (12.7, 22.0, 22.0) and bb.zmax < 150 and near_post(bb):
        return "bottom Z idler"
    if bb.zmin > 995 and near_post(bb):     # everything standing on a post top
        if sg == (56.4, 56.4, 76.6):
            return "Z motor (horizontal shaft)"
        if sg == (14.0, 15.0, 15.0):
            return "Z pulley"
        return "Z motor shaft leftover"
    return None


dropped = {}
motor_template = None
groups = {}
for c in base.children:
    bb = world_bb(c)
    role = belt_z_role(bb)
    if role:
        dropped[role] = dropped.get(role, 0) + 1
        if role.startswith("Z motor (") and motor_template is None:
            motor_template = c.obj.moved(c.loc)
        continue
    groups.setdefault((bb_key(bb), sig_of(bb)), []).append(c)

kept, n_dups = [], 0
for members in groups.values():
    # Prefer a descriptive name over the anonymous "part_N" pass-through.
    members.sort(key=lambda c: (c.name.startswith("part_"), c.name))
    kept.append(members[0])
    n_dups += len(members) - 1

# ============================================================
# Y return idlers: one per Y-gantry rail, fully inside the rail's open
# C-channel (owner, 2026-10-12). The baseline also carried a stray left idler
# in front of the carriage plate, inside the FL Z-post channel where the Z
# nut block runs, and two v3-generated idlers sticking out of the channel
# mouths. Each dropped idler takes the bracket v3 generated for it.
# ============================================================
FRAME_CX = sum((b.xmin + b.xmax) / 2 for b in post_bbs) / len(post_bbs)


def channel_of(rb):
    """X and Z limits of a Y-gantry rail's open channel (it opens toward the frame interior)."""
    left = (rb.xmin + rb.xmax) / 2 < FRAME_CX
    x0, x1 = (rb.xmax - CHANNEL_DEPTH, rb.xmax) if left else (rb.xmin, rb.xmin + CHANNEL_DEPTH)
    cz = (rb.zmin + rb.zmax) / 2
    return left, x0, x1, cz - CHANNEL_HALF_OPEN, cz + CHANNEL_HALF_OPEN


def in_channel(bb, rb, tol=0.05):
    _, x0, x1, z0, z1 = channel_of(rb)
    return (x0 - tol <= bb.xmin and bb.xmax <= x1 + tol and z0 - tol <= bb.zmin and bb.zmax <= z1 + tol
            and rb.ymin - tol <= bb.ymin and bb.ymax <= rb.ymax + tol)


ctr = lambda bb: ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
yrails = [world_bb(c) for c in kept if c.name.startswith("cbeam_Yrail")]
idlers = [c for c in kept if sig_of(world_bb(c)) == (12.7, 22.0, 22.0)]
brackets = [c for c in kept if sig_of(world_bb(c)) == (5.0, 30.0, 30.0)]
pulleys = [world_bb(c) for c in kept if sig_of(world_bb(c)) == (14.0, 15.0, 15.0)]


def gen_bracket_of(idler_bb, left):
    """The 5x30x30 bracket v3 generated for an idler (15 mm outboard, same Y/Z)."""
    ic = ctr(idler_bb)
    bx = ic[0] - GEN_BRACKET_OFFSET if left else ic[0] + GEN_BRACKET_OFFSET
    return [b for b in brackets if abs(ctr(world_bb(b))[0] - bx) < 1 and abs(ctr(world_bb(b))[1] - ic[1]) < 1
            and abs(ctr(world_bb(b))[2] - ic[2]) < 1]


stray, y_idlers = [], []
for rb in yrails:
    left = channel_of(rb)[0]
    rcx = (rb.xmin + rb.xmax) / 2
    at_rail = [c for c in idlers if abs(ctr(world_bb(c))[0] - rcx) < 40 and rb.zmin < ctr(world_bb(c))[2] < rb.zmax]
    inside = [c for c in at_rail if in_channel(world_bb(c), rb)]
    assert len(inside) == 1, f"expected one Y idler inside the rail channel at X={rcx:.0f}, found {len(inside)}"
    for c in at_rail:
        stray.append(c)
        stray += gen_bracket_of(world_bb(c), left)
    # The kept idler is re-placed below as the id 93 envelope, on the drive
    # pulley's belt line at the rail's front end, centred on the channel like
    # the Y motor (see below).
    drive = min((p for p in pulleys if abs(ctr(p)[0] - rcx) < 40), key=lambda p: -ctr(p)[1])
    bracket = gen_bracket_of(world_bb(inside[0]), left)
    y_idlers.append(dict(rail=rb, left=left, x=ctr(drive)[0], z=(rb.zmin + rb.zmax) / 2,
                         bracket=bracket[0] if bracket else None))
kept = [c for c in kept if all(c is not s for s in stray)]
n_stray_idlers = sum(1 for c in stray if c in idlers) - len(y_idlers)

# ============================================================
# Y motors straight on the Y-rail face (owner, 2026-10-12): the 2 id 75
# plates go. Each motor's flange sits on its rail's open face, coaxial with
# its drive pulley (V1.0 had the left motor 6 mm off its pulley), centred on
# the channel and turned Y_MOTOR_TURN. The pulley and the belt strands drop
# to the channel centre with it; the return idler is placed there above.
# ============================================================
ymount_plates = [c for c in kept if sig_of(world_bb(c)) == YMOUNT_SIG]
assert len(ymount_plates) == 2, f"expected the 2 id 75 Y-motor plates, found {len(ymount_plates)}"
kept = [c for c in kept if all(c is not p for p in ymount_plates)]
y_drive = {}          # id(child) -> world shape (motor) or Location (pulley, belts)
for rb in yrails:
    left = channel_of(rb)[0]
    rcx, rcz = (rb.xmin + rb.xmax) / 2, (rb.zmin + rb.zmax) / 2
    face_x = rb.xmax if left else rb.xmin
    motors_y = [c for c in kept if sig_of(world_bb(c)) == (56.4, 56.4, 76.6) and world_bb(c).zmax < 900
                and world_bb(c).xlen > 70 and abs(ctr(world_bb(c))[0] - rcx) < 100]
    assert len(motors_y) == 1, f"expected one Y motor at the rail X={rcx:.0f}, found {len(motors_y)}"
    motor = motors_y[0]
    pulley = min((c for c in kept if sig_of(world_bb(c)) == (14.0, 15.0, 15.0)
                  and abs(ctr(world_bb(c))[0] - rcx) < 40), key=lambda c: -ctr(world_bb(c))[1])
    pc = ctr(world_bb(pulley))
    belts = [c for c in kept if sig_of(world_bb(c))[:2] == (1.5, 6.0) and abs(ctr(world_bb(c))[0] - pc[0]) < 10]
    assert len(belts) == 2, f"expected 2 Y belt strands on the pulley at X={pc[0]:.0f}, found {len(belts)}"
    m = motor.obj.moved(motor.loc)
    flange = max((f for f in m.Faces() if f.geomType() == "PLANE" and f.normalAt().x * (-1 if left else 1) > 0.99),
                 key=lambda f: f.Area())
    fb = flange.BoundingBox()
    old_axis = (flange.Center().x, (fb.ymin + fb.ymax) / 2, (fb.zmin + fb.zmax) / 2)
    axis = (face_x, pc[1], rcz)
    m = m.translate(cq.Vector(*(n - o for n, o in zip(axis, old_axis))))
    m = m.rotate(cq.Vector(*axis), cq.Vector(axis[0] + 1, axis[1], axis[2]), Y_MOTOR_TURN)
    y_drive[id(motor)] = m
    dz = rcz - pc[2]
    for c in [pulley] + belts:
        y_drive[id(c)] = Location((0, 0, dz)) * c.loc
    print(f"  Y motor {'L' if left else 'R'}: flange {axis[0] - old_axis[0]:+.2f} mm onto the rail face, axis "
          f"{axis[1] - old_axis[1]:+.2f} along Y (onto its pulley) and {axis[2] - old_axis[2]:+.2f} in Z (channel "
          f"centre), turned {Y_MOTOR_TURN:.2f} deg; pulley + 2 belt strands {dz:+.2f} mm in Z")

# ============================================================
# Frame: 6 mm post-to-end-beam spacers. Each post moves POST_SHIFT out along
# Y with everything fixed to it or riding on it: the 2 m top X rails, their
# 2040 inserts, the T-gussets on them, the Z carriage plates and their
# V-wheels. The 1 m Y rails, the center spreader and the moving gantry stay,
# so the bottom plates and the spreader shims are rebuilt 6 mm thick and the
# Y-gantry rail ends sit POST_SHIFT further from the carriage plates.
# The Z carriage plates and their wheels then come Z_PLATE_GAP back toward
# the frame interior: V1.0 had the plates flush on the open face, SN 001 runs
# them ~1 mm off it. (That also brings the V1.0 wheels, 1.8 mm deeper than
# the side-face V-slot centre, to within 0.8 mm of it.)
# ============================================================
def rides_post(c, bb):
    sg = sig_of(bb)
    if c.name.startswith(("cbeam_Zpost", "cbeam_Xtop")):
        return True
    if sg == (20.0, 40.0, 1000.0) and bb.zmin > 900:        # 2040 inserts inside the top X rails
        return True
    if sg == (4.0, 160.0, 280.0):                            # T-gussets on the top X rails
        return True
    if sg == (3.0, 88.0, 127.0) and bb.ylen < 3.5:           # Z carriage plate on a post's open face
        return any(abs(bb.ymin - p.ymax) < 0.5 or abs(bb.ymax - p.ymin) < 0.5 for p in post_bbs)
    if sg == (10.2, 23.9, 23.9):                             # Z carriage wheel riding a post
        cx, cy, _ = ctr(bb)
        return any(p.ymin < cy < p.ymax and abs(cx - (p.xmin + p.xmax) / 2) < 70 for p in post_bbs)
    return False


def outward(bb):
    return -1.0 if ctr(bb)[1] < FRAME_CY else 1.0


ZCARRIAGE_SIGS = ((3.0, 88.0, 127.0), (10.2, 23.9, 23.9))  # plate, V-wheel (only those that ride a post)

assy = Assembly("M3-2_Assembly")
n_moved = n_wheels = n_zplates = 0
for c in kept:
    bb = world_bb(c)
    sg = sig_of(bb)
    if sg == (4.0, 80.0, 100.0) and bb.zmax < 150:
        # Bottom plate: re-extrude its rail-side face 6 mm toward the post.
        front = outward(bb) < 0
        rail_face = max((f for f in c.obj.moved(c.loc).Faces()
                         if f.geomType() == "PLANE" and abs(f.normalAt().y) > 0.99),
                        key=lambda f: f.Center().y if front else -f.Center().y)
        plate = cq.Solid.extrudeLinear(rail_face, cq.Vector(0, -FRAME_SPACER if front else FRAME_SPACER, 0))
        assy.add(plate, name=c.name, color=c.color)
        continue
    if c.name.startswith("shim_topmid"):
        # Spreader shim: fill from the spreader end to the moved top X rail.
        front = outward(bb) < 0
        y0 = bb.ymax - FRAME_SPACER if front else bb.ymin
        shim = cq.Solid.makeBox(bb.xlen, FRAME_SPACER, bb.zlen, cq.Vector(bb.xmin, y0, bb.zmin))
        assy.add(shim, name=c.name, color=c.color)
        continue
    if id(c) in y_drive:
        placed_y = y_drive[id(c)]
        if isinstance(placed_y, Location):
            assy.add(c.obj, name=c.name, loc=placed_y, color=c.color)
        else:
            assy.add(placed_y, name=c.name, color=c.color)
        continue
    loc = c.loc
    if rides_post(c, bb):
        shift = POST_SHIFT - Z_PLATE_GAP if sg in ZCARRIAGE_SIGS else POST_SHIFT
        loc = Location((0, outward(bb) * shift, 0)) * c.loc
        n_moved += 1
        n_wheels += sg == (10.2, 23.9, 23.9)
        n_zplates += sg == (3.0, 88.0, 127.0)
    assy.add(c.obj, name=c.name, loc=loc, color=c.color)
assert n_wheels == 16, f"expected 16 Z carriage wheels on the posts, moved {n_wheels}"
assert n_zplates == 4, f"expected 4 Z carriage plates on the posts, moved {n_zplates}"

# Y return idler envelopes (id 93): on the drive pulley's centreline, fully
# inside the rail channel, IDLER_PLATE_GAP behind the carriage plate that caps
# the rail's front end. Each takes its v3 bracket placeholder along.
IDLER_W = 2 * IDLER_FLANGE_T + IDLER_TRACK
idler_env = (cq.Solid.makeCylinder(IDLER_FLANGE_D / 2, IDLER_FLANGE_T, cq.Vector(0, 0, 0), cq.Vector(1, 0, 0))
             .fuse(cq.Solid.makeCylinder(IDLER_HUB_D / 2, IDLER_TRACK,
                                         cq.Vector(IDLER_FLANGE_T, 0, 0), cq.Vector(1, 0, 0)))
             .fuse(cq.Solid.makeCylinder(IDLER_FLANGE_D / 2, IDLER_FLANGE_T,
                                         cq.Vector(IDLER_FLANGE_T + IDLER_TRACK, 0, 0), cq.Vector(1, 0, 0)))
             .clean())
caps = [world_bb(c) for c in assy.children if sig_of(world_bb(c)) == (3.0, 88.0, 127.0) and world_bb(c).ylen < 3.5]
for yi in y_idlers:
    rb = yi["rail"]
    cap = min((p for p in caps if abs(ctr(p)[0] - yi["x"]) < 70), key=lambda p: abs(ctr(p)[1] - rb.ymin))
    yc = cap.ymax + IDLER_PLATE_GAP + IDLER_FLANGE_D / 2
    env = idler_env.translate(cq.Vector(yi["x"] - IDLER_W / 2, yc, yi["z"]))
    assert in_channel(env.BoundingBox(), rb), "Y idler envelope does not fit inside the rail channel"
    tag = "L" if yi["left"] else "R"
    assy.add(env, name=f"idler_y_return_envelope_{tag}", color=IDL)
    b = yi["bracket"]
    if b is not None:
        bc = ctr(world_bb(b))
        bx = yi["x"] - GEN_BRACKET_OFFSET if yi["left"] else yi["x"] + GEN_BRACKET_OFFSET
        assy.add(b.obj, name=b.name, color=b.color, loc=Location((bx - bc[0], yc - bc[1], yi["z"] - bc[2])) * b.loc)
    _, x0, x1, _, _ = channel_of(rb)
    eb = env.BoundingBox()
    print(f"  Y idler {tag}: envelope {IDLER_W:.1f} x {IDLER_FLANGE_D:.0f} inside the rail channel "
          f"({eb.xmin - x0:.1f} / {x1 - eb.xmax:.1f} mm margins), {IDLER_PLATE_GAP:.0f} mm behind the carriage plate")

print(f"  kept {len(kept)} baseline parts; dropped {n_dups} duplicate placements")
for role, k in sorted(dropped.items()):
    print(f"  dropped {k:2d} x {role}")
n_stray_brackets = sum(1 for c in stray if c in brackets) - sum(1 for yi in y_idlers if yi["bracket"] is not None)
print(f"  dropped {n_stray_idlers} stray Y idlers + {n_stray_brackets} of their brackets; "
      f"one id 93 idler envelope per Y rail")
print(f"  dropped {len(ymount_plates)} id 75 Y-motor plates; the Y motors bolt straight to the rail face")
print(f"  frame spacers {V1_SPACER:.0f} -> {FRAME_SPACER:.0f} mm: moved {n_moved} post-mounted parts "
      f"{POST_SHIFT:.0f} mm out along Y; bottom plates and spreader shims rebuilt {FRAME_SPACER:.0f} mm")
print(f"  Z carriage: {n_zplates} plates + {n_wheels} wheels moved {POST_SHIFT - Z_PLATE_GAP:.0f} mm out, "
      f"{Z_PLATE_GAP:.0f} mm running gap to the post open face")

post_bbs = [c.obj.moved(c.loc).BoundingBox() for c in assy.children if c.name.startswith("cbeam_Zpost")]

# ============================================================
# Lead-screw stack templates
# ============================================================
# Motor: the baseline Z motor lies with its shaft toward -Y. Find the axis
# (centre of the 56.4 mm body square), the shaft tip and the flange face
# (largest planar face looking toward the shaft; the pilot boss face in front
# of it is smaller), then stand it shaft-down with the flange face at Z=0 and
# the axis at the origin.
mbb = motor_template.BoundingBox()
m_ax, m_az = (mbb.xmin + mbb.xmax) / 2, (mbb.zmin + mbb.zmax) / 2
flange = max((f for f in motor_template.Faces()
              if f.geomType() == "PLANE" and f.normalAt().y < -0.99), key=lambda f: f.Area())
m_face_y = flange.Center().y
SHAFT_LEN = m_face_y - mbb.ymin                       # shaft tip below the flange face
motor_up = (motor_template
            .translate(cq.Vector(-m_ax, -m_face_y, -m_az))
            .rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90))

mount  = cq.importers.importStep(MOUNT_STEP).val().Solids()[0]
collar = cq.importers.importStep(COLLAR_STEP).val().Solids()[0]     # Z[0,7], axis at origin
COLLAR_H = collar.BoundingBox().zlen
nut = cq.importers.importStep(NUT_STEP).val().Solids()[0]           # X[-17,17] Y[-6,6] Z[0,20]
# The nut block's counterbored bolt face is -Y; its +Y face goes against the plate.
nbb = nut.BoundingBox()
nut = nut.translate(cq.Vector(0, 0, -(nbb.zmin + nbb.zmax) / 2))     # bore centre at Z=0
NUT_H = nbb.zlen
assert abs(nbb.ymax - NUT_BORE_INSET) < 0.05, "nut block bore is not NUT_BORE_INSET from its plate-side face"

holder = cq.importers.importStep(HOLDER_STEP).val().Solids()[0]    # Z=0 on the bottom plate top edge
assert abs(NUT_H - zbh.NUT_BLOCK_H) < 0.1, "holder stop height assumes a 20 mm nut block"

screw   = cq.Solid.makeCylinder(SCREW_D / 2, SCREW_L)
coupler = ring(COUPLER_D, BORE_D, COUPLER_L)
thrust  = ring(THRUST_D, BORE_D, THRUST_H)
brg608  = ring(zbh.BRG_OD, BORE_D, zbh.BRG_H)                       # seated at the holder bottom

# Stack heights (world Z), bottom to top at each post top.
FLOOR_TOP      = POST_TOP + MOUNT_FLOOR
MOTOR_FACE     = POST_TOP + MOUNT_TOP
SHAFT_TIP      = MOTOR_FACE - SHAFT_LEN
SCREW_TOP      = SHAFT_TIP - SHAFT_GAP
THRUST_UP_Z    = FLOOR_TOP
COLLAR_UP_Z    = THRUST_UP_Z + THRUST_H
COUPLER_Z      = COLLAR_UP_Z + COLLAR_H
THRUST_LOW_Z   = POST_TOP - THRUST_H
COLLAR_LOW_Z   = THRUST_LOW_Z - COLLAR_H
assert COUPLER_Z + COUPLER_L <= POST_TOP + 40.0, "coupler does not fit under the mount top plate"
assert COUPLER_Z <= SCREW_TOP <= COUPLER_Z + COUPLER_L, "screw top end is not inside the coupler"
assert COUPLER_Z <= SHAFT_TIP <= COUPLER_Z + COUPLER_L, "motor shaft tip is not inside the coupler"

# ============================================================
# Place one stack per Z post
# ============================================================
placed = [world_bb(c) for c in assy.children]          # frame as moved above
carriage_plates = [b for b in placed if sig_of(b) == (3.0, 88.0, 127.0)]
bottom_plates = [b for b in placed if sig_of(b) == (FRAME_SPACER, 80.0, 100.0) and b.zmax < 150]

Z_POSTS = []
for pb in post_bbs:
    pcx, pcy = (pb.xmin + pb.xmax) / 2, (pb.ymin + pb.ymax) / 2
    front = pcy < FRAME_CY
    open_y = pb.ymax if front else pb.ymin            # channel opens toward the frame interior
    axis = (pcx, open_y - AXIS_INSET if front else open_y + AXIS_INSET)
    rot = 0 if front else 180
    tag = ("F" if front else "R") + ("L" if pcx < 1000 else "R")
    # The Z carriage plate on this post's open face, and the bottom plate under it.
    plate = min(carriage_plates, key=lambda b: abs((b.xmin + b.xmax) / 2 - pcx) + abs(
        (b.ymin + b.ymax) / 2 - open_y))
    bplate = min(bottom_plates, key=lambda b: abs((b.xmin + b.xmax) / 2 - pcx) + abs(
        (b.ymin + b.ymax) / 2 - open_y))
    plate_cz = (plate.zmin + plate.zmax) / 2
    assert abs(plate.zlen - zbh.CARRIAGE_PLATE_H) < 0.1, "holder stop height assumes an 88 mm carriage plate"
    plate_face = plate.ymin if front else plate.ymax
    assert abs(abs(plate_face - axis[1]) - NUT_BORE_INSET) < 0.05, f"{tag}: nut block is not flush on its carriage plate"
    # The holder sits on the bottom plate's top edge; the nut block lands on its top face.
    stop_top = bplate.zmax + zbh.STOP_TOP

    parts = [
        (f"zmount_{tag}",         place(mount, (0, MOUNT_AXIS_Y), rot, axis, POST_TOP), PRINT_COLOR),
        (f"motor_z_{tag}",        place(motor_up, (0, 0), rot, axis, MOTOR_FACE), MTR),
        (f"coupler_envelope_{tag}", place(coupler, (0, 0), rot, axis, COUPLER_Z), ENV),
        (f"collar_upper_{tag}",   place(collar, (0, 0), rot, axis, COLLAR_UP_Z), IDL),
        (f"thrust_envelope_upper_{tag}", place(thrust, (0, 0), rot, axis, THRUST_UP_Z), ENV),
        (f"thrust_envelope_lower_{tag}", place(thrust, (0, 0), rot, axis, THRUST_LOW_Z), ENV),
        (f"collar_lower_{tag}",   place(collar, (0, 0), rot, axis, COLLAR_LOW_Z), IDL),
        (f"leadscrew_{tag}",      place(screw, (0, 0), rot, axis, SCREW_TOP - SCREW_L), SHAFT),
        (f"nut_block_{tag}",      place(nut, (0, 0), rot, axis, plate_cz), BRASS),
        (f"z_bottom_holder_{tag}", place(holder, (0, 0), rot, axis, bplate.zmax), PRINT_COLOR),
        (f"bearing_608_envelope_{tag}", place(brg608, (0, 0), rot, axis, bplate.zmax), ENV),
    ]
    for name, shape, color in parts:
        assy.add(shape, name=name, color=color)
    Z_POSTS.append(dict(tag=tag, post=pb, open_y=open_y, axis=axis, front=front,
                        carriage_plate=plate, bottom_plate=bplate, stop_top=stop_top))
    print(f"  {tag}: screw axis ({axis[0]:.1f}, {axis[1]:.1f}), {AXIS_INSET:.0f} mm inside the open face; "
          f"hard stop top Z={stop_top:.1f}")

print(f"\n  {len(assy.children)} parts total")
print(f"  Generation time: {time.time() - t0:.1f}s")

if __name__ == "__main__":
    assert os.path.abspath(OUT) != os.path.abspath(BASELINE)
    print(f"\nExporting to {os.path.basename(OUT)}...")
    t1 = time.time()
    assy.save(OUT)
    print(f"  {os.path.getsize(OUT) / 1024 / 1024:.1f} MB in {time.time() - t1:.1f}s")
