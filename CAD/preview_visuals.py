"""Render an explode view and a 360 rotating GIF of the assembly.

Outputs:
  CAD/_preview/explode.png    (~3MB, single isometric frame, parts displaced)
  CAD/_preview/rotate_360.gif (~5-10MB, 24 frames, full assembly)

Bbox-based: each part rendered as its colored bounding-box solid.
Headless via matplotlib Agg + Pillow GIF assembly. No VTK, no GL.
"""
import os, sys, importlib.util, io, contextlib
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "_preview"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Load assembly (silent)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("m3_asm", HERE / "m3_2_assembly.py")
mod = importlib.util.module_from_spec(spec)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    spec.loader.exec_module(mod)

from cadquery import Location

def flatten(a, parent=Location()):
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

parts_data = []
for name, sh in flatten(mod.assy):
    bb = sh.BoundingBox()
    parts_data.append((name, (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)))
print(f"Loaded {len(parts_data)} parts")

# Frame bounds
Xs = [b[0] for _, b in parts_data] + [b[1] for _, b in parts_data]
Ys = [b[2] for _, b in parts_data] + [b[3] for _, b in parts_data]
Zs = [b[4] for _, b in parts_data] + [b[5] for _, b in parts_data]
CX = (min(Xs) + max(Xs)) / 2
CY = (min(Ys) + max(Ys)) / 2
CZ = (min(Zs) + max(Zs)) / 2
SPAN = max(max(Xs) - min(Xs), max(Ys) - min(Ys), max(Zs) - min(Zs))

# ---------------------------------------------------------------------------
# Colors by part-name prefix
# ---------------------------------------------------------------------------
def color_for(name):
    n = name.lower()
    if "cbeam" in n:    return "#1a1a1a"
    if "motor" in n:    return "#0d0d0d"
    if "pulley" in n:   return "#c9a227"
    if "idler" in n and "brk" not in n: return "#9aa0a6"
    if "wheel" in n:    return "#9bd72a"
    if "zmount" in n or "ymount" in n: return "#9bd72a"
    if "bot" in n and "mount" in n:    return "#9bd72a"
    if "shim" in n:     return "#d97706"
    if "tbracket" in n or "gusset" in n: return "#9bd72a"
    if "belt" in n:     return "#84cc16"
    if "xcarr" in n:    return "#7a7a7a"
    if "bracket" in n:  return "#5b8def"
    return "#a3a3a3"

def bbox_faces(bb):
    x0, x1, y0, y1, z0, z1 = bb
    return [
        [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],
        [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
        [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
        [(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
        [(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],
        [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],
    ]

# ---------------------------------------------------------------------------
# Render one frame
# ---------------------------------------------------------------------------
def render(parts_data, azim, elev=22, explode=0.0, size=(8, 8), zoom=1.0):
    fig = plt.figure(figsize=size, facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#f5f5f5")
    for name, bb in parts_data:
        x0, x1, y0, y1, z0, z1 = bb
        if explode > 0:
            mx, my, mz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
            dx = (mx - CX) * explode
            dy = (my - CY) * explode
            dz = (mz - CZ) * explode
            x0 += dx; x1 += dx
            y0 += dy; y1 += dy
            z0 += dz; z1 += dz
        polys = bbox_faces((x0, x1, y0, y1, z0, z1))
        col = color_for(name)
        coll = Poly3DCollection(polys, facecolor=col, edgecolor="#1a1a1a",
                                linewidth=0.25, alpha=0.92)
        ax.add_collection3d(coll)
    ax.view_init(elev=elev, azim=azim)
    half = SPAN / 2 / zoom
    ax.set_xlim(CX - half, CX + half)
    ax.set_ylim(CY - half, CY + half)
    ax.set_zlim(CZ - half, CZ + half)
    ax.set_box_aspect([1, 1, 1])
    ax.axis("off")
    fig.tight_layout(pad=0.1)
    return fig

def fig_to_image(fig):
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    arr = np.asarray(buf)
    return Image.fromarray(arr).convert("RGB")

# ---------------------------------------------------------------------------
# 1) Explode view (single frame, 30% outward)
# ---------------------------------------------------------------------------
print("Rendering explode view...")
fig = render(parts_data, azim=-60, elev=22, explode=0.30, size=(10, 10), zoom=0.95)
fig.savefig(OUT / "explode.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"  Wrote {OUT / 'explode.png'}")

# ---------------------------------------------------------------------------
# 2) 360 rotating GIF (24 frames, 15 deg each)
# ---------------------------------------------------------------------------
print("Rendering 360 GIF (24 frames)...")
N_FRAMES = 24
frames = []
for i in range(N_FRAMES):
    azim = (360.0 / N_FRAMES) * i - 60   # start at -60 to match explode view
    fig = render(parts_data, azim=azim, elev=22, explode=0.0, size=(7, 7), zoom=1.0)
    frames.append(fig_to_image(fig))
    plt.close(fig)
    print(f"  frame {i+1}/{N_FRAMES} (azim={azim:.0f})")

gif_path = OUT / "rotate_360.gif"
frames[0].save(
    gif_path,
    save_all=True,
    append_images=frames[1:],
    duration=80,    # ms per frame -> ~12 fps, ~2 second loop
    loop=0,
    optimize=True,
)
print(f"  Wrote {gif_path}")
print(f"  Size: {os.path.getsize(gif_path) / 1024:.0f} KB")
