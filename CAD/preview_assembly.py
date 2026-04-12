#!/usr/bin/env python3
"""
M3-CRETE Assembly Self-Check + Auto Preview

Runs the assembly build, then:
  1. Prints a sorted bbox/position table per part (for quick visual diff)
  2. Runs a set of engineering sanity checks (butt-joint gaps, frame closure,
     wheel alignment, beam span, etc.) — fails LOUDLY on any mismatch
  3. Renders 3-view orthographic wireframe PNGs from the part bboxes
     using matplotlib (no OpenGL/VTK needed, works headless)

Usage:
    cad_venv/Scripts/python.exe CAD/preview_assembly.py
Outputs:
    CAD/_preview/bbox_table.txt
    CAD/_preview/sanity_report.txt
    CAD/_preview/view_xy.png     (top-down)
    CAD/_preview/view_xz.png     (front)
    CAD/_preview/view_yz.png     (right side)
"""
import os, sys, importlib.util, math
from pathlib import Path

HERE = Path(__file__).parent
OUT  = HERE / "_preview"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------
# 1) Import the assembly module and bake part locations
# ----------------------------------------------------------
# Loading m3_2_assembly.py runs its body; we grab the `assy` global.
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("m3_asm", HERE / "m3_2_assembly.py")
mod = importlib.util.module_from_spec(spec)
# Stash sys.argv so the __main__ interference block doesn't re-run the
# (slow) pairwise solid intersection — preview doesn't need it
saved_argv = sys.argv
sys.argv = ["m3_2_assembly.py"]
# Redirect stdout to swallow assembly-print output
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    spec.loader.exec_module(mod)
sys.argv = saved_argv

assy = mod.assy
from cadquery import Location

def flatten(a, parent=Location()):
    """Yield (name, shape_with_baked_location) for every leaf object."""
    loc = parent * a.loc if a.loc else parent
    if a.obj is not None:
        sh = a.obj
        if hasattr(sh, "val"):
            sh = sh.val()
        try:
            yield (a.name, sh.moved(loc))
        except Exception:
            pass
    for ch in a.children:
        yield from flatten(ch, loc)

parts = list(flatten(assy))
bboxes = {}
for name, sh in parts:
    bb = sh.BoundingBox()
    bboxes[name] = (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)

print(f"Loaded {len(parts)} parts from assembly")

# ----------------------------------------------------------
# 2) Dump sorted bbox table
# ----------------------------------------------------------
lines = [f"{'name':<22} {'X_min':>8} {'X_max':>8} {'Y_min':>8} {'Y_max':>8} {'Z_min':>8} {'Z_max':>8}"]
lines.append("-" * 80)
for name in sorted(bboxes.keys()):
    x0, x1, y0, y1, z0, z1 = bboxes[name]
    lines.append(f"{name:<22} {x0:8.1f} {x1:8.1f} {y0:8.1f} {y1:8.1f} {z0:8.1f} {z1:8.1f}")
bbox_txt = "\n".join(lines)
(OUT / "bbox_table.txt").write_text(bbox_txt)
print(f"  Wrote {OUT / 'bbox_table.txt'}")

# ----------------------------------------------------------
# 3) Sanity checks — engineering invariants
# ----------------------------------------------------------
checks = []
def check(label, cond, detail=""):
    checks.append((label, cond, detail))

def has(name):
    return name in bboxes

def bb(name):
    return bboxes[name]

# Frame envelope
W, D, H = mod.W, mod.D, mod.H
check("Frame W = 2480mm", W == 2480, f"W={W}")
check("Frame D = 1240mm", D == 1240, f"D={D}")
check("Frame H = 1200mm", H == 1200, f"H={H}")

# 4 posts + top ring (4 X-rails + 2 Y-rails) + 2 bottom skids = 12 frame parts
frame_parts = [n for n in bboxes if n.startswith(("post_","topX_","topY_","botY_"))]
check("Phase A = 12 frame parts", len(frame_parts) == 12, f"got {len(frame_parts)}")

# Z-corner plate butt-joint gaps: plate rail-facing face must sit 2mm off post
TOL = 0.01
for nm in ("FL", "FR"):
    p = f"zpl_{nm}"
    if has(p):
        _, _, y0, y1, _, _ = bb(p)
        check(f"{p} front seats 2mm off post", abs(y0 - 22) < TOL, f"y0={y0}")
        check(f"{p} is 3mm thick in Y",        abs((y1-y0) - 3) < TOL, f"dy={y1-y0}")
for nm in ("RL", "RR"):
    p = f"zpl_{nm}"
    if has(p):
        _, _, y0, y1, _, _ = bb(p)
        check(f"{p} rear seats 2mm off post",  abs(y1 - 1218) < TOL, f"y1={y1}")

# Z-corner plate dimensions: 88(X) x 3(Y) x 127(Z) after ry=90
for nm in ("FL","FR","RL","RR"):
    p = f"zpl_{nm}"
    if has(p):
        x0,x1,y0,y1,z0,z1 = bb(p)
        check(f"{p} X span = 88", abs((x1-x0)-88) < TOL, f"{x1-x0}")
        check(f"{p} Z span = 127",abs((z1-z0)-127) < TOL, f"{z1-z0}")

# Y-rails: 1200mm C-beams (40x80), loaded from _userYY.step, snapped to Z=400.
# Span Y[20, 1220] (butt-joined to post inner faces at front/rear).
for side in ("L","R"):
    r = f"zpY_{side}"
    if has(r):
        x0,x1,y0,y1,z0,z1 = bb(r)
        check(f"{r} length 1200",      abs((y1-y0)-1200) < TOL, f"{y1-y0}")
        check(f"{r} front at Y=20",    abs(y0-20) < TOL, f"y0={y0}")
        check(f"{r} rear at Y=1220",   abs(y1-1220) < TOL, f"y1={y1}")
        check(f"{r} width 40 in X (C-beam)", abs((x1-x0)-40) < TOL, f"{x1-x0}")
        check(f"{r} height 80 in Z",         abs((z1-z0)-80) < TOL, f"{z1-z0}")
        check(f"{r} Z bottom at 400",        abs(z0-400) < TOL, f"z0={z0}")

# X-beam: 2 segments, each 1200mm, total span 2400mm with butt-joints at 40/2440
g1 = bb("gantry_1") if has("gantry_1") else None
g2 = bb("gantry_2") if has("gantry_2") else None
if g1 and g2:
    lo = min(g1[0], g2[0])
    hi = max(g1[1], g2[1])
    check("X-beam span = 2400mm",      abs((hi-lo)-2400) < TOL, f"{hi-lo}")
    check("X-beam left end at X=40",   abs(lo-40)  < TOL, f"{lo}")
    check("X-beam right end at X=2440",abs(hi-2440)< TOL, f"{hi}")

# X-beam carriage plates: butt-join X-beam ends at X=40 / X=2440
# Orientation: 3(X) x 88(Y, travel) x 127(Z, spans rail height)
if has("xcar_L") and has("xcar_R"):
    for name in ("xcar_L", "xcar_R"):
        x0,x1,y0,y1,z0,z1 = bb(name)
        check(f"{name} thickness 3 in X",  abs((x1-x0)-3)   < TOL, f"{x1-x0}")
        check(f"{name} 88 in Y (travel)",  abs((y1-y0)-88)  < TOL, f"{y1-y0}")
        check(f"{name} 127 in Z (rail)",   abs((z1-z0)-127) < TOL, f"{z1-z0}")
    lx0,lx1,_,_,_,_ = bb("xcar_L")
    rx0,rx1,_,_,_,_ = bb("xcar_R")
    check("xcar_L +X face meets X-beam at X=40",    abs(lx1 - 40) < TOL, f"{lx1}")
    check("xcar_R -X face meets X-beam at X=2440",  abs(rx0 - 2440) < TOL, f"{rx0}")
    check("xcar_L clears left Y-rail (+X side)",    lx0 - 35 >= 2 - TOL, "gap < 2mm")
    check("xcar_R clears right Y-rail (-X side)",   2445 - rx1 >= 2 - TOL,"gap < 2mm")

# V-wheel placement: wheel X center = rail X center, Z centers at ±50, Y ±33
wheels = [n for n in bboxes if n.startswith("vw_xc_")]
check("8 X-carriage V-wheels", len(wheels) == 8, f"got {len(wheels)}")
for name in wheels:
    x0,x1,y0,y1,z0,z1 = bb(name)
    cx = (x0+x1)/2; cy = (y0+y1)/2; cz = (z0+z1)/2
    side = "L" if "_L_" in name else "R"
    expected_cx = 25 if side == "L" else 2455
    expected_cy = 620 + (-33 if "_fr_" in name else +33)
    expected_cz = 440 + (+50 if "_top" in name else -50)
    check(f"{name} X center", abs(cx - expected_cx) < 0.1, f"cx={cx} vs {expected_cx}")
    check(f"{name} Y center", abs(cy - expected_cy) < 0.1, f"cy={cy} vs {expected_cy}")
    check(f"{name} Z center", abs(cz - expected_cz) < 0.1, f"cz={cz} vs {expected_cz}")

# Z-carriage wheels: 4 per post (16 total). Wheel X = post_cx ± 30,
# wheel Y = POST Y-center (10 front, 1230 rear) — V-groove rides the post's
# narrow X-face V-rail at the post centerline, not the plate mid-thickness.
# wheel Z = ZP ± 33.
zwheels = [n for n in bboxes if n.startswith("vw_zc_")]
check("16 Z-carriage V-wheels", len(zwheels) == 16, f"got {len(zwheels)}")
POST_CX = {"FL": 20, "FR": 2460, "RL": 20, "RR": 2460}
for name in zwheels:
    x0,x1,y0,y1,z0,z1 = bb(name)
    cx = (x0+x1)/2; cy = (y0+y1)/2; cz = (z0+z1)/2
    parts_ = name.split("_")  # vw, zc, FL, lt, top
    post_nm = parts_[2]
    xside = parts_[3]
    zside = parts_[4]
    expected_cx = POST_CX[post_nm] + (-30 if xside == "lt" else +30)
    expected_cy = 10 if post_nm.startswith("F") else 1230
    expected_cz = 440 + (+33 if zside == "top" else -33)
    check(f"{name} X center", abs(cx - expected_cx) < 0.1, f"cx={cx} vs {expected_cx}")
    check(f"{name} Y center", abs(cy - expected_cy) < 0.1, f"cy={cy} vs {expected_cy}")
    check(f"{name} Z center", abs(cz - expected_cz) < 0.1, f"cz={cz} vs {expected_cz}")
    # Wheel must engage (overlap by ~2mm) the post narrow face V-slot
    if xside == "lt":
        # Wheel touches post X=cx-20 face (post left narrow face)
        post_face = POST_CX[post_nm] - 20
        check(f"{name} engages post left V-slot",  x1 > post_face + 1.5 and x1 < post_face + 2.5, f"x1={x1}")
    else:
        post_face = POST_CX[post_nm] + 20
        check(f"{name} engages post right V-slot", x0 < post_face - 1.5 and x0 > post_face - 2.5, f"x0={x0}")

# ----------------------------------------------------------
# Phase C.1 — Z-motors, angled L-brackets, pulleys
# (per 2026-04-11 revision: stock Motor Mount Plate replaced with
#  custom N23 angled L-bracket; motor sits on top of frame.)
# ----------------------------------------------------------
Z_BELT_Y = {"F": 60, "R": D - 60}          # front 60, rear 1180
Z_MOTOR_CZ = 1170   # updated 2026-04-11 — all 4 brackets at z1=1202.5, motor cz=1170
POST_IS_LEFT  = {"FL": True, "FR": False, "RL": True, "RR": False}
POST_IS_FRONT = {"FL": True, "FR": True,  "RL": False,"RR": False}

z_brackets = [n for n in bboxes if n.startswith("z_bracket_")]
z_motors   = [n for n in bboxes if n.startswith("z_motor_")]
z_pulls    = [n for n in bboxes if n.startswith("z_pulley_")]
check("4 Z-motor L-brackets", len(z_brackets) == 4, f"got {len(z_brackets)}")
check("4 Z-motors",           len(z_motors)   == 4, f"got {len(z_motors)}")
check("4 Z-motor pulleys",    len(z_pulls)    == 4, f"got {len(z_pulls)}")

# As of 2026-04-11, ALL 4 Z-motor assemblies have been relocated OUTSIDE the
# frame envelope by Nick to make room for the Y-axis motors in Phase C.4.
# Tight "inside frame" position checks are relaxed for every corner; the
# loader in m3_2_assembly.py picks up the Fusion-edited positions verbatim.
RELOCATED = {"FL", "FR", "RL", "RR"}

for post_nm in ("FL", "FR", "RL", "RR"):
    is_left  = POST_IS_LEFT[post_nm]
    is_front = POST_IS_FRONT[post_nm]
    ty = Z_BELT_Y["F" if is_front else "R"]
    relocated = post_nm in RELOCATED

    # --- L-bracket: 69 x 69 x 65 (sorted) ---
    b = f"z_bracket_{post_nm}"
    if has(b):
        x0,x1,y0,y1,z0,z1 = bb(b)
        dims = sorted([x1-x0, y1-y0, z1-z0])
        check(f"{b} sorted dims 65/69/69", all(abs(d-t) < 0.2 for d,t in zip(dims,[65,69,69])), f"{dims}")
        # Bracket top can protrude ~2.5mm above H=1200 with motors outboard;
        # that is accepted (a cover/safety box will handle it later).
        check(f"{b} Z inside frame top",   z1 <= H + 3 + TOL, f"z1={z1}")
        check(f"{b} Z above top X-rail bot", z0 >= 1120 - 0.5, f"z0={z0}")
        if not relocated:
            if is_front:
                check(f"{b} flange at Y=20", abs(y0 - 20) < 0.1, f"y0={y0}")
            else:
                check(f"{b} flange at Y=1220", abs(y1 - 1220) < 0.1, f"y1={y1}")
            if is_left:
                check(f"{b} X inside, post-side at 60",  abs(x0 - 60)  < 0.1, f"x0={x0}")
            else:
                check(f"{b} X inside, post-side at 2420", abs(x1 - 2420) < 0.1, f"x1={x1}")

    # --- Motor: 56.4 x 56.4 x 76.6 (sorted) ---
    m = f"z_motor_{post_nm}"
    if has(m):
        x0,x1,y0,y1,z0,z1 = bb(m)
        dims = sorted([x1-x0, y1-y0, z1-z0])
        check(f"{m} sorted dims 56.4/56.4/76.6",
              all(abs(d-t) < 0.1 for d,t in zip(dims,[56.4, 56.4, 76.6])), f"{dims}")
        check(f"{m} Z center = motor height", abs((z0+z1)/2 - Z_MOTOR_CZ) < TOL, f"cz={(z0+z1)/2}")
        check(f"{m} Z inside frame top",      z1 <= H + TOL, f"z1={z1}")
        if not relocated:
            if is_front:
                check(f"{m} Y clears post front",  y0 >= 20 - TOL, f"y0={y0}")
            else:
                check(f"{m} Y clears post rear",   y1 <= 1220 + TOL, f"y1={y1}")
            check(f"{m} X inside frame", x0 >= 0 - TOL and x1 <= W + TOL, f"X[{x0},{x1}]")
            check(f"{m} Y center at belt", abs((y0+y1)/2 - ty) < TOL, f"cy={(y0+y1)/2}")

    # --- Pulley: 14/15/15 (sorted) ---
    pl = f"z_pulley_{post_nm}"
    if has(pl):
        x0,x1,y0,y1,z0,z1 = bb(pl)
        dims = sorted([x1-x0, y1-y0, z1-z0])
        check(f"{pl} sorted dims 14/15/15",
              all(abs(d-t) < 0.1 for d,t in zip(dims,[14,15,15])), f"{dims}")
        check(f"{pl} Z center = motor", abs((z0+z1)/2 - Z_MOTOR_CZ) < TOL, f"cz={(z0+z1)/2}")
        if not relocated:
            check(f"{pl} Y center = belt",  abs((y0+y1)/2 - ty) < TOL, f"cy={(y0+y1)/2}")
            if is_left:
                check(f"{pl} X center near shaft", abs((x0+x1)/2 - 52.9) < 0.2, f"cx={(x0+x1)/2}")
            else:
                check(f"{pl} X center near shaft", abs((x0+x1)/2 - 2427.1) < 0.2, f"cx={(x0+x1)/2}")

# ----------------------------------------------------------
# Phase C.3 — Z-belts + L-tabs
# ----------------------------------------------------------
z_belts = [n for n in bboxes if n.startswith("z_belt_")]
check("8 Z-belt strands (4 loops x 2)", len(z_belts) == 8, f"got {len(z_belts)}")
check("no L-tabs (removed)", not any(n.startswith("z_ltab_") for n in bboxes), "found stray ltab")

for post_nm in ("FL", "FR", "RL", "RR"):
    is_front = POST_IS_FRONT[post_nm]
    # Use the pulley's actual loaded center as the reference — tolerates
    # Nick's manual moves without code edits.
    pulley_name = f"z_pulley_{post_nm}"
    if not has(pulley_name):
        continue
    pbb = bb(pulley_name)
    px = (pbb[0] + pbb[1]) / 2
    py = (pbb[2] + pbb[3]) / 2
    psx = pbb[1] - pbb[0]
    psy = pbb[3] - pbb[2]
    # Derive axis: 14mm dim is along the shaft
    if abs(psx - 14) < 0.5:
        pax = "X"
    elif abs(psy - 14) < 0.5:
        pax = "Y"
    else:
        pax = "Z"

    # Belt strands: both 1.5 x 6 x 1088 (sorted), Z span idler→motor tangent
    for tag in ("fr", "bk"):
        bn = f"z_belt_{post_nm}_{tag}"
        if has(bn):
            x0,x1,y0,y1,z0,z1 = bb(bn)
            dims = sorted([x1-x0, y1-y0, z1-z0])
            check(f"{bn} sorted dims 1.5/6/1131",
                  all(abs(d-t) < 0.5 for d,t in zip(dims,[1.5, 6, 1131])), f"{dims}")
            check(f"{bn} Z bottom tangent", abs(z0 - 33) < 0.5, f"z0={z0}")
            check(f"{bn} Z top tangent",    abs(z1 - 1164) < 0.5, f"z1={z1}")
            cx = (x0+x1)/2; cy = (y0+y1)/2
            if pax == "X":
                # Strands separated in Y, both at pulley X
                check(f"{bn} X at pulley", abs(cx - px) < 0.5, f"cx={cx} vs px={px}")
                exp_dy = -6.5 if tag == "fr" else +6.5
                check(f"{bn} Y offset ±6.5", abs((cy - py) - exp_dy) < 0.5,
                      f"dy={cy - py}")
            else:  # Y-axis pulley
                check(f"{bn} Y at pulley", abs(cy - py) < 0.5, f"cy={cy} vs py={py}")
                exp_dx = -6.5 if tag == "fr" else +6.5
                check(f"{bn} X offset ±6.5", abs((cx - px) - exp_dx) < 0.5,
                      f"dx={cx - px}")

    # L-tab removed 2026-04-11: belts clamp directly to Z-corner plate.

# ----------------------------------------------------------
# Phase C.2 — Z-idlers at post bottoms
# ----------------------------------------------------------
IDLER_Z = 22   # lowered 2026-04-11 for full Z-travel (bottom at 11, top at 33)
z_idlers = [n for n in bboxes if n.startswith("z_idler_")]
check("4 Z-axis idlers", len(z_idlers) == 4, f"got {len(z_idlers)}")
for post_nm in ("FL", "FR", "RL", "RR"):
    is_front = POST_IS_FRONT[post_nm]
    relocated = post_nm in RELOCATED
    idn = f"z_idler_{post_nm}"
    pulley_name = f"z_pulley_{post_nm}"
    if has(idn) and has(pulley_name):
        x0,x1,y0,y1,z0,z1 = bb(idn)
        cx = (x0+x1)/2; cy = (y0+y1)/2; cz = (z0+z1)/2
        # Dimensions checked on sorted basis — idler axle can be X or Y
        dims = sorted([x1-x0, y1-y0, z1-z0])
        check(f"{idn} sorted dims 12.7/22/22",
              all(abs(d-t) < 0.1 for d,t in zip(dims,[12.7, 22, 22])), f"{dims}")
        # Idler must sit directly below its pulley in X and Y
        pbb = bb(pulley_name)
        ppx = (pbb[0] + pbb[1]) / 2
        ppy = (pbb[2] + pbb[3]) / 2
        check(f"{idn} X under pulley", abs(cx - ppx) < 0.5, f"cx={cx} vs ppx={ppx}")
        check(f"{idn} Y under pulley", abs(cy - ppy) < 0.5, f"cy={cy} vs ppy={ppy}")
        check(f"{idn} Z center = {IDLER_Z}", abs(cz - IDLER_Z) < TOL, f"cz={cz}")
        # Idlers sit outboard of the bottom Y-braces in X, so they are allowed
        # below Z=40 (brace top). Only require they stay above the frame floor.
        check(f"{idn} above frame floor",    z0 >= 0 - TOL,            f"z0={z0}")
        if not relocated:
            check(f"{idn} X inside frame", x0 >= 0 - TOL and x1 <= W + TOL, f"X[{x0},{x1}]")
            check(f"{idn} Y inside frame", y0 >= 0 - TOL and y1 <= D + TOL, f"Y[{y0},{y1}]")

# ----------------------------------------------------------
# 4) Report checks
# ----------------------------------------------------------
passed = sum(1 for _,c,_ in checks if c)
failed = [x for x in checks if not x[1]]
report = [f"Sanity check: {passed}/{len(checks)} passed"]
if failed:
    report.append("\nFAILED CHECKS:")
    for label, _, detail in failed:
        report.append(f"  [FAIL] {label:45s} {detail}")
else:
    report.append("\n[OK] All invariants hold")
report_txt = "\n".join(report)
(OUT / "sanity_report.txt").write_text(report_txt)
print(report_txt)

# ----------------------------------------------------------
# 5) 3-view orthographic wireframe PNGs via matplotlib
# ----------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
except ImportError:
    print("matplotlib not installed — skipping view renders")
    sys.exit(0 if not failed else 1)

# Color lookup by part-name prefix (mirrors assembly colors)
COLOR = {
    "post_": "#c0c0c0",
    "topX_": "#c0c0c0",
    "topY_": "#c0c0c0",
    "botY_": "#c0c0c0",
    "zpl_":  "#707075",
    "zpY_":  "#707075",
    "xcar_": "#707075",
    "gantry_":"#202020",
    "vw_":   "#e0e0c8",
}
def color_for(name):
    for k,v in COLOR.items():
        if name.startswith(k):
            return v
    return "#a0a0a0"

def render_view(axes_xy, title, fname):
    """axes_xy = ('X','Y') etc — which two axes to project onto."""
    IDX = {"X":(0,1), "Y":(2,3), "Z":(4,5)}
    a, b = axes_xy
    ia0, ia1 = IDX[a]
    ib0, ib1 = IDX[b]
    fig, ax = plt.subplots(figsize=(14, 7), dpi=110)
    all_mn_a = all_mx_a = all_mn_b = all_mx_b = None
    # Draw taller things first so they are overwritten by higher-priority parts
    order = sorted(bboxes.keys(), key=lambda n: -((bboxes[n][1]-bboxes[n][0])*(bboxes[n][3]-bboxes[n][2])))
    for name in order:
        bbv = bboxes[name]
        a0, a1 = bbv[ia0], bbv[ia1]
        b0, b1 = bbv[ib0], bbv[ib1]
        w = a1-a0; h = b1-b0
        rect = Rectangle((a0, b0), w, h, fill=True,
                         facecolor=color_for(name), edgecolor="black",
                         linewidth=0.3, alpha=0.55)
        ax.add_patch(rect)
        if all_mn_a is None:
            all_mn_a, all_mx_a = a0, a1
            all_mn_b, all_mx_b = b0, b1
        else:
            all_mn_a = min(all_mn_a, a0); all_mx_a = max(all_mx_a, a1)
            all_mn_b = min(all_mn_b, b0); all_mx_b = max(all_mx_b, b1)
    pad = 50
    ax.set_xlim(all_mn_a - pad, all_mx_a + pad)
    ax.set_ylim(all_mn_b - pad, all_mx_b + pad)
    ax.set_aspect("equal")
    ax.set_xlabel(f"{a} (mm)")
    ax.set_ylabel(f"{b} (mm)")
    ax.set_title(f"M3-CRETE v0.3.0  —  {title}")
    ax.grid(True, alpha=0.3, linewidth=0.3)
    fig.tight_layout()
    fig.savefig(OUT / fname)
    plt.close(fig)
    print(f"  Wrote {OUT / fname}")

render_view(("X","Y"), "TOP view (looking -Z)",    "view_xy.png")
render_view(("X","Z"), "FRONT view (looking +Y)",  "view_xz.png")
render_view(("Y","Z"), "RIGHT view (looking -X)",  "view_yz.png")

print(f"\nDone. Preview at {OUT}")
sys.exit(0 if not failed else 1)
