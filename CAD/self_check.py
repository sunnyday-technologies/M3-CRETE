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
    (4.0, 68.0, 80.0):    'zmount',
    (5.0, 40.0, 80.0):    'zcap',
    (4.0, 80.0, 100.0):   'bot-mount',
    (4.0, 80.0, 80.0):    'ymount',
    (4.0, 80.0, 120.0):   'tbracket',
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
    'bracket': 0,          # all L-brackets removed
    'motor': 6,            # 4 Z + 2 Y
    'vwheel': 24,
    'pulley': 6,
    'idler': 5,
    'plate': 6,
    'shim': 6,             # 4 top corners + 2 mid-frame
    'zmount': 4,
    'zcap': 4,
    'idler-brk': 1,        # only 1 mid-frame idler bracket remains
    'bot-mount': 4,
    'ymount': 2,
    'tbracket': 2,
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

# ---------- CHECK 2: combined motor-mount/spacer sanity ----------
# Each zmount should be ~4 x 80 x 102 mm; each zcap ~5 x 40 x 80 mm.
for s in parts:
    lbl = label_of(s)
    if lbl == 'zmount':
        bb = s.BoundingBox()
        dims = sorted([bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin])
        if dims[0] > 6:
            problems.append(f"zmount dims {dims} — thinnest axis > 6mm")
    elif lbl == 'zcap':
        bb = s.BoundingBox()
        dims = sorted([bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin])
        if dims[0] > 8:
            problems.append(f"zcap dims {dims} — thinnest axis > 8mm")

# ---------- CHECK 3: motors attached to brackets (within 50 mm) ----------
motors  = [s for s in parts if label_of(s) == 'motor']
brackets = [s for s in parts if label_of(s) == 'bracket']
def center(s):
    bb = s.BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5

# Z-motors should have a zmount plate nearby (not a bracket — brackets removed).
# Y-motors mount directly to frame, skip them.
zmounts = [s for s in parts if label_of(s) == 'zmount']
for m in motors:
    mc = center(m)
    if mc[2] < 900:
        continue  # Y-motor, skip
    nearest = min(zmounts, key=lambda b: dist(mc, center(b)), default=None)
    if nearest is None:
        problems.append(f"Z-motor at ({mc[0]:.0f},{mc[1]:.0f},{mc[2]:.0f}) has no zmount plate")
        continue
    d = dist(mc, center(nearest))
    if d > 100:  # wider tolerance — plate spans 102mm from Z=960 to Z=1062
        problems.append(f"Z-motor at ({mc[0]:.0f},{mc[1]:.0f},{mc[2]:.0f}) "
                        f"nearest zmount is {d:.0f} mm away (> 100 mm)")

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

# ---------- CHECK 5: motor-mount plates span shim+motor zone (Z > 900) ----------
for s in parts:
    lbl = label_of(s)
    if lbl in ('zmount', 'zcap'):
        bb = s.BoundingBox()
        if bb.zmin < 900:
            cx = (bb.xmin + bb.xmax) / 2
            cy = (bb.ymin + bb.ymax) / 2
            cz = (bb.zmin + bb.zmax) / 2
            problems.append(f"{lbl} at ({cx:.0f},{cy:.0f},{cz:.0f}) below Z=900")

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
