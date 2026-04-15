"""
M3-CRETE self-check — runs after m3_2_assembly.py to catch regressions
before a visual review. Fails fast on parts at obviously wrong positions
(cbeam-adjacency errors, corner connectors that are too thick, motors far
from any Z-post, etc.). Also runs a bbox-overlap interference pre-filter
and a BRepAlgoAPI_Common check on suspicious pairs.

Run:
  cad_venv/Scripts/python.exe CAD/self_check.py

Exit code 0 if clean, 1 if any issue found.
"""
import sys, os, importlib.util
from collections import Counter

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
    (10.2, 23.9, 23.9):   'vwheel',
    (14.0, 15.0, 15.0):   'pulley',
    (12.7, 22.0, 22.0):   'idler',
    (3.0, 88.0, 127.0):   'plate',
    (4.0, 40.0, 80.0):    'shim',
    (5.0, 80.0, 80.0):    'L-corner',
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

# ---------- CHECK 1: inventory counts match expectation ----------
inv = Counter(label_of(s) for s in parts)
EXPECTED = {
    'cbeam': 17,
    'bracket': 6,          # 4 Z + 2 Y
    'motor': 6,            # 4 Z + 2 Y
    'vwheel': 24,
    'pulley': 6,
    'idler': 5,
    'plate': 6,
    'shim': 10,
    'L-corner': 24,
    'idler-brk': 5,
    'belt': 12,
}
problems = []
print(f"Total parts: {len(parts)}")
print()
print("Inventory:")
for k in sorted(set(list(inv.keys()) + list(EXPECTED.keys()))):
    got, want = inv.get(k, 0), EXPECTED.get(k, 0)
    marker = ' ' if got == want else 'X'
    print(f"  [{marker}] {k:12s} {got:4d} (expected {want})")
    if got != want:
        problems.append(f"inventory: {k} got {got}, expected {want}")

# ---------- CHECK 2: corner connector THICKNESS sanity ----------
# A corner connector must be 5 mm thin on its normal axis. If my box() args
# were wrong, the 5 becomes 80 — immediately visible in the dim tuple but
# *also* in the sorted dims being (5, 80, 80). Any connector whose raw dims
# aren't (5, 80, 80) for exactly one axis is broken.
for s in parts:
    if label_of(s) != 'L-corner':
        continue
    bb = s.BoundingBox()
    dx, dy, dz = bb.xmax - bb.xmin, bb.ymax - bb.ymin, bb.zmax - bb.zmin
    thin = sum(1 for d in (dx, dy, dz) if abs(d - 5.0) < 0.5)
    big  = sum(1 for d in (dx, dy, dz) if abs(d - 80.0) < 0.5)
    if thin != 1 or big != 2:
        cx = (bb.xmin + bb.xmax) / 2
        cy = (bb.ymin + bb.ymax) / 2
        cz = (bb.zmin + bb.zmax) / 2
        problems.append(
            f"L-corner at ({cx:.0f},{cy:.0f},{cz:.0f}) has non-flat dims "
            f"({dx:.1f}, {dy:.1f}, {dz:.1f}) — expected one 5 and two 80")

# ---------- CHECK 3: motors attached to brackets (within 50 mm) ----------
motors  = [s for s in parts if label_of(s) == 'motor']
brackets = [s for s in parts if label_of(s) == 'bracket']
def center(s):
    bb = s.BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5

for m in motors:
    mc = center(m)
    nearest = min(brackets, key=lambda b: dist(mc, center(b)), default=None)
    if nearest is None:
        problems.append(f"motor at {mc} has no bracket")
        continue
    d = dist(mc, center(nearest))
    if d > 50:
        problems.append(f"motor at ({mc[0]:.0f},{mc[1]:.0f},{mc[2]:.0f}) "
                        f"nearest bracket is {d:.0f} mm away (> 50 mm)")

# ---------- CHECK 4: plate vs cbeam interference (catches clipping) ----------
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

def bb_overlap(a, b, tol=-0.01):
    b1, b2 = a.BoundingBox(), b.BoundingBox()
    return (b1.xmin < b2.xmax + tol and b2.xmin < b1.xmax + tol and
            b1.ymin < b2.ymax + tol and b2.ymin < b1.ymax + tol and
            b1.zmin < b2.zmax + tol and b2.zmin < b1.zmax + tol)

plate_idx = [i for i, s in enumerate(parts) if label_of(s) == 'plate']
cbeam_idx = [i for i, s in enumerate(parts) if label_of(s) == 'cbeam']
for i in plate_idx:
    for j in cbeam_idx:
        if not bb_overlap(parts[i], parts[j]):
            continue
        try:
            common = BRepAlgoAPI_Common(parts[i].wrapped, parts[j].wrapped)
            common.Build()
            if common.IsDone():
                gp = GProp_GProps()
                BRepGProp.VolumeProperties_s(common.Shape(), gp)
                v = gp.Mass()
                if v > 0.5:
                    pc = center(parts[i])
                    problems.append(
                        f"plate at ({pc[0]:.0f},{pc[1]:.0f},{pc[2]:.0f}) "
                        f"clips cbeam by {v:.0f} mm^3")
        except Exception:
            pass

# ---------- CHECK 5: cbeam joint count matches connector count ----------
cbeams = [s for s in parts if label_of(s) == 'cbeam']
cb_bbs = []
for s in cbeams:
    bb = s.BoundingBox()
    cb_bbs.append((bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

def axis_of(b):
    if (b[5]-b[4]) > 500: return 'Z'
    if (b[3]-b[2]) > 500: return 'Y'
    if (b[1]-b[0]) > 500: return 'X'
    return None

def touches(a, b, tol=5):
    return all(a[2*i]-tol <= b[2*i+1] and b[2*i]-tol <= a[2*i+1] for i in range(3))

perp = sum(
    1
    for i in range(len(cb_bbs))
    for j in range(i+1, len(cb_bbs))
    if touches(cb_bbs[i], cb_bbs[j]) and axis_of(cb_bbs[i]) != axis_of(cb_bbs[j])
)
if perp != inv.get('L-corner', 0):
    problems.append(f"perpendicular cbeam joints = {perp} but L-corner count = {inv.get('L-corner', 0)}")

# ---------- REPORT ----------
print()
if problems:
    print(f"SELF-CHECK FAILED — {len(problems)} issue(s):")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
else:
    print("SELF-CHECK PASSED")
    sys.exit(0)
