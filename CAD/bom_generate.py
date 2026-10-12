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
os.makedirs(os.path.join(HERE, "_preview"), exist_ok=True)
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
    if dims_sorted == (69.3, 69.3, 76.6):    return "motor"     # Y motor, turned ~19 deg on the rail face
    if dims_sorted == (10.2, 23.9, 23.9):    return "vwheel"
    if dims_sorted == (14.0, 15.0, 15.0):    return "pulley"
    if dims_sorted == (14.2, 18.0, 18.0):    return "idler"      # id 93 envelope (20T toothless, 10 mm belt)
    if dims_sorted == (3.0, 88.0, 127.0):    return "plate"
    if dims_sorted == (20.0, 20.0, 20.0):    return "splice"
    if dims_sorted == (6.0, 40.0, 80.0):     return "shim"       # center-spreader shims, 6 mm
    if dims_sorted == (4.0, 80.0, 97.0):     return "zmount"     # id 75 printed plate, at the 2 Y-motor positions
    if dims_sorted == (6.0, 80.0, 100.0):    return "botmount"   # Z-post bottom plate, 6 mm
    # ymount: TODO add signature when user provides 4mm spacer plate STEP geometry
    if dims_sorted == (4.0, 160.0, 280.0):   return "tbracket"
    if dims_sorted == (5.0, 80.0, 80.0):     return "connector"
    if dims_sorted == (5.0, 30.0, 30.0):     return "idlerbrk"
    if dims_sorted[0] == 1.5 and dims_sorted[1] == 6.0: return "belt"
    # Lead-screw Z (BOM v2.9.0)
    if dims_sorted == (68.0, 80.0, 86.5):    return "zmotormount"
    if dims_sorted == (28.1, 34.0, 45.0):    return "zholder"
    if dims_sorted == (8.0, 8.0, 1000.0):    return "leadscrew"
    if dims_sorted == (12.0, 20.0, 34.0):    return "nutblock"
    if dims_sorted == (19.0, 19.0, 20.0):    return "coupler"
    if dims_sorted == (7.0, 14.0, 14.0):     return "collar"
    if dims_sorted == (7.0, 22.0, 22.0):     return "brg608"
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
    # The 8x16x5 thrust bearings share their bbox with the X-carriage bolt
    # heads; the thrust bearings are the ones on the Z-post tops.
    if dims == (5.0, 16.0, 16.0) and bb.zmin > 900:
        nm = f"thrust_{i}"
    parts.append((nm, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

def tag_of(name):
    for p in ("zmotormount","zholder","leadscrew","nutblock","coupler","collar","brg608","thrust",
              "cbeam","connector","idlerbrk","zmount","zcap","botmount",
              "ymount","tbracket","bracket","motor","vwheel","pulley",
              "idler","plate","splice","belt","shim","part","rail"):
        if name.startswith(p): return p
    return "other"

inv = Counter(tag_of(p[0]) for p in parts)

# ---------- Detect C-beam joint pairs (5mm adjacency) ----------
cbeams = [p for p in parts if p[0].startswith("cbeam")]
# Joints are found by bbox adjacency; frame spacers are 6 mm (2026-10-12), so
# allow the spacer plus 1 mm (was 5 mm for the old 4 mm spacers).
def touches(a, b, tol=7.0):
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
    ("Printed Z motor mount / Y-spacer",  inv["zmount"],      "80 x 97 x 4",    "PETG / CCF", "id 75 plate, dropped (BOM v2.13.0): Y motors bolt straight to the C-beam face (owner, 2026-10-12)"),
    ("Printed Z-post bottom plate",       inv["botmount"],    "80 x 100 x 6",   "PETG / CCF", "Spacer between Z-post and bottom Y rail; the bottom holder rests on it"),
    ("Printed Z motor mount (lead screw)", inv["zmotormount"], "80 x 68 x 86.5", "PETG / CCF", "Z motor shaft-down on the post top; collars + thrust bearings on its floor"),
    ("Printed Z bottom holder / hard stop", inv["zholder"],   "34 x 28 x 45",   "PETG / CF-Nylon", "608ZZ seat at the screw bottom; top face is the Z hard stop"),
    ("Tr8x2 lead screw 1000 mm",          inv["leadscrew"],   "8 x 1000",       "Stainless", "Z drive, one per post"),
    ("Tr8x2 nut block",                   inv["nutblock"],    "34 x 20 x 12",   "POM / brass", "On each Z carriage plate, inside the post channel"),
    ("Shaft coupler 8 x 8 mm",            inv["coupler"],     "19 x 20",        "Aluminum", "Z motor to lead screw"),
    ("Lock collar 8 mm",                  inv["collar"],      "14 x 7",         "Aluminum / steel", "Above and below each Z motor-mount floor"),
    ("Thrust bearing 8 x 16 x 5",         inv["thrust"],      "16 x 5",         "Steel", "Between each lock collar and the Z motor-mount floor"),
    ("608ZZ bearing",                     inv["brg608"],      "22 x 7",         "Steel", "Z lead-screw bottom support, in the bottom holder"),
    ("Printed Y-motor 4mm spacer",        inv["ymount"],      "TBD",            "PETG / CCF", "Legacy 4mm Y-motor spacer (id 81, deprecated); should stay zero"),
    ("Printed center T-gusset",           inv["tbracket"],    "280 x 160 x 4",  "PETG / CCF", "Top spreader / X-rail junction reinforcement"),
    ("Legacy L-bracket NEMA23 / T-slot",  inv["bracket"],     "65 x 69 x 69",   "Aluminum / steel", "Should be zero; replaced by printed mounts"),
    ("Stepper motor NEMA23",              inv["motor"],       "56.4 x 56.4 x 76.6", "Steel", "4 Z + 2 Y; X (rack-and-pinion) TBD"),
    ("V-wheel (XL solid polycarbonate)",  inv["vwheel"],      "24 x 11",        "Polycarbonate / steel", "Gantry running on C-beam V-grooves"),
    ("GT2 timing pulley",                 inv["pulley"],      "16T 5mm bore",   "Aluminum",  "Drive pulleys"),
    ("Smooth idler pulley",               inv["idler"],       "18 x 14.2",      "Aluminum",  "Y belt return idlers, 20T toothless for the 10 mm belt"),
    ("Idler axle bracket",                inv["idlerbrk"],    "30 x 30 x 5",    "Steel",     "Support plate for each idler axle"),
    ("Z-corner gantry plate",             inv["plate"],       "127 x 88 x 3",   "Aluminum",  "Gantry carriage plates (six corners)"),
    ("Belt clamp / belt run",             inv["belt"] + inv["part"], "GT2 6mm", "Fiber-reinforced rubber", "Y belts (X TBD)"),
    ("Center-spreader 6mm shim",          inv["shim"],        "80 x 6 x 40",    "Aluminum / steel", "Spacer between flat C-beam end and Z-post"),
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
N_BOTMOUNT        = inv["botmount"]
N_SHIM            = inv["shim"]
N_ZMOTOR          = inv["zmotormount"]         # one Z motor per lead-screw mount
N_XMOTOR          = 1                          # rack-and-pinion X; its mount is not modeled
N_YMOTOR          = N_MOTOR - N_ZMOTOR - N_XMOTOR
N_NUTBLOCK        = inv["nutblock"]
N_ZHOLDER         = inv["zholder"]

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
    ("M5 SHCS",                                        N_XMOTOR * 4, "M5 x 10 mm", "NEMA23 face mounting, X motor (4 per motor)"),
    ("M5 SHCS",                                        N_ZMOTOR * 4, "M5 x 16 mm",     "Z motor through its flange and the mount's 8 mm top plate"),
    ("M5 nut",                                         N_ZMOTOR * 4, "M5",             "Z motor-mount nut traps"),

    # --- Lead-screw Z ---
    # Bolted in reverse (owner, test-fitted on SN 001): through the carriage
    # plate's holes into the nut block, with a nut inside the C-beam opening if needed.
    ("M5 SHCS",                                        N_NUTBLOCK * 2, "M5 x 20 mm",   "Z nut block, through the carriage plate into the block"),
    ("M5 nut",                                         N_NUTBLOCK * 2, "M5",           "Z nut block bolts, inside the C-beam opening if needed"),
    ("M5 SHCS",                                        N_ZHOLDER * 2, "M5 x 20 mm",    "Z bottom holder into the channel-floor slots"),
    ("M5 drop-in T-nut",                               N_ZHOLDER * 2, "M5, 4080 series", "Channel-floor T-nuts for the Z bottom holders"),

    # --- Printed motor mount / spacer plates ---
    # Y motor bolted straight to the C-beam face slots, no plate (owner,
    # 2026-10-12): turned ~19 deg so one diagonal hole pair lands on the two
    # face-slot centrelines, so 2 bolts per motor into T-nuts.
    ("M5 SHCS",                                        N_YMOTOR * 2, "M5 x 16 mm", "Y motor through its flange into the C-beam face slot"),
    ("M5 drop-in T-nut",                               N_YMOTOR * 2, "M5, 4080 series", "Mating T-nuts for the Y-motor bolts"),
    ("M5 SHCS",                                        N_BOTMOUNT * 2, "M5 x 16 mm", "Z-post bottom plate to Z-post"),
    ("M5 drop-in T-nut",                               N_BOTMOUNT * 2, "M5, 4080 series", "Mating T-nuts for Z-post bottom plates"),

    # --- Legacy L-brackets to rail (should remain zero) ---
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
    elif item == "M5 nut":
        m5_totals["M5 nut"] += qty
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
    f.write("### Motors / printed mounts\n\n")
    f.write(f"{N_XMOTOR} X motor × 4 NEMA23 face screws (M5×10) = {N_XMOTOR*4} screws.\n")
    f.write(f"{N_ZMOTOR} Z motors × 4 M5×16 + 4 M5 nuts in the lead-screw mount's nut traps.\n")
    f.write(f"{N_YMOTOR} Y motors, turned ~19° (one diagonal hole pair on the two face slots) and bolted straight to the C-beam face × 2 M5×16 + 2 T-nuts.\n")
    f.write(f"{N_BRACKET} brackets × 4 rail-face screws (M5×10) + T-nuts = {N_BRACKET*4} pairs.\n")
    f.write("Note: the rack-and-pinion X-motor mounting is not yet modeled, so it\n")
    f.write("gets no back-side nuts here — add them when the X-axis lands.\n\n")
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
