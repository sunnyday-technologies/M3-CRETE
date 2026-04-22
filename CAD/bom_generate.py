"""
M3-CRETE BOM generator — derives a structural inventory and a hardware
fastener pack from the live m3_2_assembly.py output.

Outputs:
  CAD/bom_structural.csv  — one row per CAD part group
  CAD/bom_hardware.csv    — one row per fastener / hardware item
  CAD/BOM_README.md       — derivation rules + audit hints

Run:   cad_venv/Scripts/python.exe CAD/bom_generate.py
"""
import sys, os, csv, importlib.util
from collections import Counter, defaultdict
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

HERE = os.path.dirname(__file__)

# ---------- Load assembly via the main script ----------
spec = importlib.util.spec_from_file_location("m3_asm",
                                              os.path.join(HERE, "m3_2_assembly.py"))
mod = importlib.util.module_from_spec(spec)
_devnull = open(os.path.join(HERE, "_preview", "null.txt"), "w")
sys.stdout = _devnull
spec.loader.exec_module(mod)
sys.stdout = sys.__stdout__

import cadquery as cq

# Use toCompound() — composes locations correctly for both Solids and
# Shells (C-beams export as open shells, so we need both).
compound = mod.assy.toCompound()
top_solids = list(compound.Solids()) + list(compound.Shells())

# Assign a name based on bbox signature (top_solids only — C-beam shells
# are folded into top_solids when present, and free shells are deduped by bbox)
def name_for_dims(dims_sorted):
    if dims_sorted == (40.0, 80.0, 1000.0): return "cbeam"
    if dims_sorted == (65.0, 69.0, 69.0):    return "bracket"
    if dims_sorted == (56.4, 56.4, 76.6):    return "motor"
    if dims_sorted == (10.2, 23.9, 23.9):    return "vwheel"
    if dims_sorted == (14.0, 15.0, 15.0):    return "pulley"
    if dims_sorted == (12.7, 22.0, 22.0):    return "idler"
    if dims_sorted == (3.0, 88.0, 127.0):    return "plate"
    if dims_sorted == (20.0, 20.0, 20.0):    return "splice"
    if dims_sorted == (4.0, 40.0, 80.0):     return "shim"
    if dims_sorted == (5.0, 80.0, 80.0):     return "connector"
    if dims_sorted == (5.0, 30.0, 30.0):     return "idlerbrk"
    if dims_sorted[0] == 1.5 and dims_sorted[1] == 6.0: return "belt"
    return "part"

parts = []
seen_bb = set()
for i, s in enumerate(top_solids):
    bb = s.BoundingBox()
    key = (round(bb.xmin, 1), round(bb.ymin, 1), round(bb.zmin, 1),
           round(bb.xmax, 1), round(bb.ymax, 1), round(bb.zmax, 1))
    if key in seen_bb:
        continue
    seen_bb.add(key)
    dims = tuple(sorted([round(bb.xmax - bb.xmin, 1),
                          round(bb.ymax - bb.ymin, 1),
                          round(bb.zmax - bb.zmin, 1)]))
    nm = f"{name_for_dims(dims)}_{i}"
    parts.append((nm, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

def tag_of(name):
    for p in ("cbeam","connector","idlerbrk","bracket","motor","vwheel",
              "pulley","idler","plate","splice","belt","shim","part","rail"):
        if name.startswith(p): return p
    return "other"

inv = Counter(tag_of(p[0]) for p in parts)

# ---------- Detect C-beam joint pairs (5mm adjacency) ----------
cbeams = [p for p in parts if p[0].startswith("cbeam")]
def touches(a, b, tol=5.0):
    _, ax0, ax1, ay0, ay1, az0, az1 = a
    _, bx0, bx1, by0, by1, bz0, bz1 = b
    return (ax0 - tol <= bx1 and bx0 - tol <= ax1 and
            ay0 - tol <= by1 and by0 - tol <= ay1 and
            az0 - tol <= bz1 and bz0 - tol <= az1)
joint_pairs = []
for i in range(len(cbeams)):
    for j in range(i + 1, len(cbeams)):
        if touches(cbeams[i], cbeams[j]):
            joint_pairs.append((cbeams[i][0], cbeams[j][0]))
N_JOINTS = len(joint_pairs)

# ---------- Structural BOM ----------
STRUCTURAL = [
    # name, qty, dims_mm, material, role
    ("C-beam 4080 1m extrusion",          inv["cbeam"],       "40 x 80 x 1000", "Aluminum", "All frame members (Z-post, X-rail, Y-rail, mid braces)"),
    ("L-bracket NEMA23 / T-slot",         inv["bracket"],     "65 x 69 x 69",   "Aluminum / steel", "Motor mount: 4 Z + 2 Y"),
    ("Stepper motor NEMA23",              inv["motor"],       "56.4 x 56.4 x 76.6", "Steel", "4 Z + 2 Y; X (rack-and-pinion) TBD"),
    ("V-wheel (XL solid polycarbonate)",  inv["vwheel"],      "24 x 11",        "Polycarbonate / steel", "Gantry running on C-beam V-grooves"),
    ("GT2 timing pulley",                 inv["pulley"],      "16T 5mm bore",   "Aluminum",  "Drive pulleys"),
    ("Smooth idler pulley",               inv["idler"],       "22 x 13",        "Aluminum",  "Belt return idlers"),
    ("Idler axle bracket",                inv["idlerbrk"],    "30 x 30 x 5",    "Steel",     "Support plate for each idler axle"),
    ("Z-corner gantry plate",             inv["plate"],       "127 x 88 x 3",   "Aluminum",  "Gantry carriage plates (six corners)"),
    ("Belt clamp / belt run",             inv["belt"] + inv["part"], "GT2 6mm", "Fiber-reinforced rubber", "Z + Y belts (X TBD)"),
    ("Y-rail / Z-post 4mm shim",          inv["shim"],        "80 x 4 x 40",    "Aluminum / steel", "Spacer between flat C-beam end and Z-post"),
    ("4080 corner connector plate (L/T)", inv["connector"],   "80 x 80 x 5",    "Steel",     "5-hole bracket at every perpendicular C-beam joint"),
]
with open(os.path.join(HERE, "bom_structural.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "qty", "dims_mm", "material", "role"])
    w.writerows(STRUCTURAL)

# ---------- Hardware BOM (rule-derived) ----------
N_CBEAM_JOINTS    = N_JOINTS
# Of those joints, the perpendicular ones get L-corner plates and the
# parallel/inline ones get inline splices. The CAD model places only
# perpendicular L-plates (matching `inv["connector"]`).
N_INLINE_SPLICE   = N_JOINTS - inv["connector"]
N_VWHEEL          = inv["vwheel"]
N_VWHEEL_ECC      = N_VWHEEL // 2          # eccentric spacers — one side only
N_VWHEEL_STD      = N_VWHEEL - N_VWHEEL_ECC
N_IDLER           = inv["idler"]
N_MOTOR           = inv["motor"]
N_BRACKET         = inv["bracket"]
N_SHIM            = inv["shim"]

HARDWARE = [
    # item, qty, size, notes
    # --- C-beam joints (5 screws per corner per user) ---
    ("L-corner plate (5-hole 4080)",                   inv["connector"], "5-hole 4080 series", f"Perpendicular C-beam joints (modeled in CAD)"),
    ("Inline splice plate (5-hole 4080)",              N_INLINE_SPLICE, "5-hole 4080 series", "Parallel C-beams meeting end-to-end (e.g. top X rails at center)"),
    ("M5 button-head SHCS",                            N_CBEAM_JOINTS * 5, "M5 x 10 mm",        "C-beam joint screws (5 per joint)"),
    ("M5 drop-in T-nut",                               N_CBEAM_JOINTS * 5, "M5, 4080 series",   "Mating T-nuts in C-beam slots"),

    # --- V-wheels (M5x40 + nyloc + 2 washer + spacer) ---
    ("M5 SHCS",                                        N_VWHEEL,  "M5 x 40 mm",        "V-wheel axle bolt"),
    ("M5 nyloc nut",                                   N_VWHEEL,  "M5",                "V-wheel axle nut"),
    ("M5 flat washer",                                 N_VWHEEL * 2, "M5",             "Each side of v-wheel stack"),
    ("Eccentric spacer 6mm (1/4 \")",                  N_VWHEEL_ECC, "6 mm OAL",       "ONE side of each wheel pair (12 total)"),
    ("Standard precision spacer 6mm",                  N_VWHEEL_STD, "6 mm OAL",       "OTHER side of each wheel pair"),

    # --- Idlers ---
    ("M5 SHCS",                                        N_IDLER, "M5 x 30 mm",          "Smooth idler axle"),
    ("M5 nyloc nut",                                   N_IDLER, "M5",                  "Idler axle nut"),
    ("M5 flat washer",                                 N_IDLER * 2, "M5",              "Each side of idler"),
    # --- Idler axle brackets (1 axle bracket per idler, 2 screws into C-beam slot) ---
    ("M5 SHCS",                                        inv["idlerbrk"] * 2, "M5 x 10 mm", "Idler axle bracket to C-beam"),
    ("M5 drop-in T-nut",                               inv["idlerbrk"] * 2, "M5, 4080 series", "Mating T-nuts for idler bracket"),

    # --- Motors (NEMA23 face × 4 fasteners per motor) ---
    ("M5 SHCS",                                        N_MOTOR * 4, "M5 x 10 mm",      "NEMA23 face mounting (4 per motor)"),

    # --- L-brackets to rail (4 fasteners per bracket) ---
    ("M5 SHCS",                                        N_BRACKET * 4, "M5 x 10 mm",    "Bracket rail face"),
    ("M5 drop-in T-nut",                               N_BRACKET * 4, "M5, 4080 series", "Mating T-nuts for bracket rail face"),

    # --- Shims ---
    ("M5 SHCS",                                        N_SHIM, "M5 x 16 mm",            "Through C-beam web into shim/Z-post"),
    ("M5 drop-in T-nut",                               N_SHIM, "M5, 4080 series",       "Anchor in Z-post slot"),
]
with open(os.path.join(HERE, "bom_hardware.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "qty", "size", "notes"])
    w.writerows(HARDWARE)

# ---------- Aggregate M5 totals (across line items) ----------
m5_totals = defaultdict(int)
for item, qty, size, _ in HARDWARE:
    if item.startswith("M5") and "SHCS" in item:
        m5_totals[size] += qty
    elif item.startswith("M5 nyloc"):
        m5_totals["M5 nyloc nut"] += qty
    elif item.startswith("M5 flat washer"):
        m5_totals["M5 flat washer"] += qty
    elif item.startswith("M5 drop-in T-nut"):
        m5_totals["M5 T-nut"] += qty

# ---------- README ----------
with open(os.path.join(HERE, "BOM_README.md"), "w") as f:
    f.write("# M3-CRETE BOM\n\n")
    f.write("Auto-generated by `bom_generate.py` from the live `m3_2_assembly.py`\n")
    f.write("output. Re-run any time the assembly script changes.\n\n")
    f.write("## Structural BOM\n\n")
    f.write(f"Source: assembly traversal of `m3_2_assembly.py` (current part count: {len(parts)}).\n\n")
    f.write("See `bom_structural.csv`.\n\n")
    f.write("## Hardware BOM derivation rules\n\n")
    f.write("Hardware is **not modeled in CAD** — it's derived by rule from the\n")
    f.write("structural inventory plus a programmatic C-beam joint detector.\n\n")
    f.write(f"### C-beam joints: {N_CBEAM_JOINTS} detected\n\n")
    f.write("Detected by 5 mm bbox adjacency between any two C-beams. Each joint\n")
    f.write("uses 1× T-plate or L-plate corner connector + 5× M5×10 button-head\n")
    f.write("SHCS + 5× M5 drop-in T-nut.\n\n")
    f.write("Joint pairs:\n\n")
    for a, b in sorted(joint_pairs):
        f.write(f"- {a} <-> {b}\n")
    f.write("\n### V-wheels\n\n")
    f.write(f"{N_VWHEEL} wheels. Each: 1× M5×40 SHCS, 1× M5 nyloc, 2× M5 washer.\n")
    f.write(f"Half ({N_VWHEEL_ECC}) get eccentric spacers (one side per wheel pair),\n")
    f.write(f"the other half ({N_VWHEEL_STD}) get standard precision spacers.\n\n")
    f.write("### Motors / brackets\n\n")
    f.write(f"{N_MOTOR} motors × 4 NEMA23 face screws (M5×10) = {N_MOTOR*4} screws.\n")
    f.write(f"{N_BRACKET} brackets × 4 rail-face screws (M5×10) + T-nuts = {N_BRACKET*4} pairs.\n")
    f.write("Note: Y-motor brackets and the rack-and-pinion X-motor mounting are\n")
    f.write("not yet modeled — add them when the X-axis lands.\n\n")
    f.write("### M5 fastener totals (sum across all line items)\n\n")
    f.write("| Item | Qty |\n|---|---|\n")
    for k in sorted(m5_totals):
        f.write(f"| {k} | {m5_totals[k]} |\n")
    f.write("\n### Things NOT in this BOM (intentionally)\n\n")
    f.write("- Belt clamps (per user: will be added inline as pin joints)\n")
    f.write("- Pulley grub screws (pre-installed from supplier)\n")
    f.write("- X-axis rack-and-pinion drivetrain (not yet modeled)\n")
    f.write("- Cable management (covered by drag chain + sleeving + glands in main BOM)\n")
    f.write("- Mechanical endstops / limit switches — NO endstops on this machine: "
            "StallGuard4 sensorless homing via TMC5160. See .claude/CLAUDE.md 'Design Exclusions'.\n")
    f.write("- Leveling feet — using bed-probe leveling, not mechanical M16 feet (2026-04-21)\n")
    f.write("- Enclosure panels / HEPA / LED / carbon fiber — per Nick's explicit exclusions\n")
    f.write("- Power supply, electronics, wiring\n")

print(f"BOM generation complete:")
print(f"  Parts traversed:  {len(parts)}")
print(f"  C-beam joints:    {N_CBEAM_JOINTS}")
print(f"  Files written:    bom_structural.csv, bom_hardware.csv, BOM_README.md")
print()
print("M5 fastener totals:")
for k in sorted(m5_totals):
    print(f"  {k:20s}  {m5_totals[k]}")
