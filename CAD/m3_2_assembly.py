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
face, so the nut block (bore centred 6 mm from its face) sits flush on the
carriage plate.
"""
import cadquery as cq
from cadquery import Assembly, Color, Location
import os, time
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
AXIS_INSET    = 6.0         # screw axis -> channel open face
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

assy = Assembly("M3-2_Assembly")
for c in kept:
    assy.add(c.obj, name=c.name, loc=c.loc, color=c.color)
print(f"  kept {len(kept)} baseline parts; dropped {n_dups} duplicate placements")
for role, k in sorted(dropped.items()):
    print(f"  dropped {k:2d} x {role}")

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
carriage_plates = [world_bb(c) for c in kept if sig_of(world_bb(c)) == (3.0, 88.0, 127.0)]
bottom_plates = [world_bb(c) for c in kept
                 if sig_of(world_bb(c)) == (4.0, 80.0, 100.0) and world_bb(c).zmax < 150]

Z_POSTS = []
for pc, pb in zip(posts, post_bbs):
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
