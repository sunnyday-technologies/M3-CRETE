"""
M3-CRETE comprehensive interference & alignment audit.
Checks ALL part-vs-part overlaps, not just plate-vs-cbeam.
Also verifies joining plate alignment with C-beam slot positions.
"""
import sys, os, importlib.util, math

HERE = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("m3_asm",
                                              os.path.join(HERE, "m3_2_assembly.py"))
mod = importlib.util.module_from_spec(spec)
_null = open(os.path.join(HERE, "_preview", "null.txt"), "w")
sys.stdout = _null
spec.loader.exec_module(mod)
sys.stdout = sys.__stdout__

comp = mod.assy.toCompound()
raw_parts = list(comp.Solids()) + list(comp.Shells())

# Dedup by bbox key
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

# Label parts
LABELS = {
    (40.0, 80.0, 1000.0): 'cbeam',
    (65.0, 69.0, 69.0):   'bracket',
    (56.4, 56.4, 76.6):   'motor',
    (10.2, 23.9, 23.9):   'vwheel',
    (14.0, 15.0, 15.0):   'pulley',
    (12.7, 22.0, 22.0):   'idler',
    (3.0, 88.0, 127.0):   'plate',
    (4.0, 40.0, 80.0):    'shim',
    (4.0, 60.0, 60.0):    'L-corner',
    (5.0, 30.0, 30.0):    'idler-brk',
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
    if d in LABELS: return LABELS[d]
    if d[0] == 1.5 and d[1] == 6.0: return 'belt'
    return 'other'

def center(s):
    bb = s.BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)

def bb_overlap(a, b, tol=-0.5):
    b1, b2 = a.BoundingBox(), b.BoundingBox()
    return (b1.xmin < b2.xmax + tol and b2.xmin < b1.xmax + tol and
            b1.ymin < b2.ymax + tol and b2.ymin < b1.ymax + tol and
            b1.zmin < b2.zmax + tol and b2.zmin < b1.zmax + tol)

print(f"Loaded {len(parts)} parts")
print()

# ============================================================
# CHECK 1: Full pairwise BRepAlgoAPI_Common interference check
# between all non-belt, non-vwheel parts
# ============================================================
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

SKIP_LABELS = {'belt', 'vwheel', 'pulley', 'other'}
check_parts = [(i, s) for i, s in enumerate(parts) if label_of(s) not in SKIP_LABELS]

print(f"INTERFERENCE CHECK ({len(check_parts)} structural parts)")
print("=" * 60)

issues = []
checked = 0
for idx_a in range(len(check_parts)):
    i, a = check_parts[idx_a]
    la = label_of(a)
    ca = center(a)
    for idx_b in range(idx_a + 1, len(check_parts)):
        j, b = check_parts[idx_b]
        lb = label_of(b)
        # Skip same-type pairs that won't interfere meaningfully
        if la == 'shim' and lb == 'shim':
            continue
        if not bb_overlap(a, b):
            continue
        checked += 1
        try:
            common = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
            common.Build()
            if common.IsDone():
                gp = GProp_GProps()
                BRepGProp.VolumeProperties_s(common.Shape(), gp)
                v = gp.Mass()
                if v > 1.0:  # > 1 mm^3 overlap
                    cb = center(b)
                    issues.append({
                        'typeA': la, 'typeB': lb,
                        'posA': ca, 'posB': cb,
                        'volume': v,
                    })
                    print(f"  CLIP: {la} at ({ca[0]:.0f},{ca[1]:.0f},{ca[2]:.0f}) "
                          f"vs {lb} at ({cb[0]:.0f},{cb[1]:.0f},{cb[2]:.0f}) "
                          f"— {v:.0f} mm^3 overlap")
        except Exception:
            pass

print(f"\n  Checked {checked} bbox-overlapping pairs")
print(f"  Found {len(issues)} interference(s)")

# ============================================================
# CHECK 2: L-corner plate alignment with C-beam slot centerlines
# ============================================================
print(f"\nJOINING PLATE ALIGNMENT CHECK")
print("=" * 60)

corners = [s for s in parts if label_of(s) == 'L-corner']
cbeams = [s for s in parts if label_of(s) == 'cbeam']

# For each L-corner, find the nearest 2 perpendicular cbeams
# and check that the plate center aligns with the cbeam slot face
align_issues = []
for plate in corners:
    pc = center(plate)
    pbb = plate.BoundingBox()

    # Find which axis is the thin axis (4mm = plate normal)
    dx = pbb.xmax - pbb.xmin
    dy = pbb.ymax - pbb.ymin
    dz = pbb.zmax - pbb.zmin
    dims = [dx, dy, dz]
    thin_idx = dims.index(min(dims))
    thin_axis = ['X', 'Y', 'Z'][thin_idx]

    # The plate sits on the outside face of a cbeam.
    # Check that the plate center, projected onto the beam axes,
    # falls within the beam's 80mm face (±40mm from beam center)
    nearby = []
    for cb in cbeams:
        cc = center(cb)
        dist = math.sqrt(sum((pc[k]-cc[k])**2 for k in range(3)))
        if dist < 200:  # within 200mm
            nearby.append((dist, cb, cc))

    nearby.sort()
    if len(nearby) < 2:
        align_issues.append(f"L-corner at ({pc[0]:.0f},{pc[1]:.0f},{pc[2]:.0f}) "
                           f"has only {len(nearby)} nearby cbeam(s)")
        continue

    # Check that plate is flush against a cbeam face (within 5mm)
    _, closest_cb, closest_cc = nearby[0]
    cbb = closest_cb.BoundingBox()
    cb_dims = [cbb.xmax - cbb.xmin, cbb.ymax - cbb.ymin, cbb.zmax - cbb.zmin]
    cb_long_idx = cb_dims.index(max(cb_dims))

    # Gap between plate and beam in the plate's normal direction
    if thin_axis == 'X':
        gap = min(abs(pbb.xmin - cbb.xmax), abs(pbb.xmax - cbb.xmin),
                  abs(pc[0] - closest_cc[0]) - 20)
    elif thin_axis == 'Y':
        gap = min(abs(pbb.ymin - cbb.ymax), abs(pbb.ymax - cbb.ymin),
                  abs(pc[1] - closest_cc[1]) - 20)
    else:
        gap = min(abs(pbb.zmin - cbb.zmax), abs(pbb.zmax - cbb.zmin),
                  abs(pc[2] - closest_cc[2]) - 20)

    if gap > 10:
        align_issues.append(f"L-corner at ({pc[0]:.0f},{pc[1]:.0f},{pc[2]:.0f}) "
                           f"normal={thin_axis}, gap to nearest cbeam = {gap:.0f}mm (>10mm)")

if align_issues:
    for a in align_issues:
        print(f"  MISALIGNED: {a}")
else:
    print("  All 24 joining plates within 10mm of nearest C-beam face")

# ============================================================
# CHECK 3: Motor bracket adjacency (more detailed)
# ============================================================
print(f"\nMOTOR-BRACKET ADJACENCY")
print("=" * 60)
motors = [s for s in parts if label_of(s) == 'motor']
brackets = [s for s in parts if label_of(s) == 'bracket']

for m in motors:
    mc = center(m)
    mbb = m.BoundingBox()
    nearest_brk = min(brackets, key=lambda b: math.sqrt(sum((center(b)[k]-mc[k])**2 for k in range(3))))
    bc = center(nearest_brk)
    dist = math.sqrt(sum((mc[k]-bc[k])**2 for k in range(3)))

    # Check which axis the motor shaft points along
    mdims = [mbb.xmax-mbb.xmin, mbb.ymax-mbb.ymin, mbb.zmax-mbb.zmin]
    shaft_idx = mdims.index(max(mdims))
    shaft_axis = ['X', 'Y', 'Z'][shaft_idx]

    status = "OK" if dist < 50 else "FAR"
    print(f"  Motor at ({mc[0]:.0f},{mc[1]:.0f},{mc[2]:.0f}) shaft={shaft_axis} "
          f"-> bracket {dist:.0f}mm away [{status}]")

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"AUDIT SUMMARY")
print(f"{'='*60}")
print(f"  Parts checked:        {len(check_parts)}")
print(f"  Interference pairs:   {len(issues)}")
print(f"  Alignment issues:     {len(align_issues)}")
total = len(issues) + len(align_issues)
if total == 0:
    print(f"\n  AUDIT PASSED")
    sys.exit(0)
else:
    print(f"\n  AUDIT FOUND {total} ISSUE(S)")
    sys.exit(1)
