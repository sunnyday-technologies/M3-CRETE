"""
Test C-beam Z-post profile — standalone file to verify the cross-section
before applying to all 4 posts in the main assembly.

Approach:
  1. Load the OpenBuilds C-Beam 40x80x1000 stock
  2. Extract its end face (at Z=0)
  3. Identify the TRUE outer envelope wire (not what OCCT's outerWire() returns —
     that picks a small inner cavity on this face)
  4. Identify the central C-channel opening (wire[4] in our probe)
  5. Build a face with outer wire + central channel as a hole
  6. Extrude to 1200mm in Z → solid with open ends showing the profile
  7. Save standalone STEP for review
"""
import cadquery as cq
from OCP.gp import gp_Pnt, gp_Vec
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge,
                                 BRepBuilderAPI_MakeFace)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_TangentialDeflection
import os

STEP_DIR = os.path.join(os.path.dirname(__file__), "Advanced", "Linear Rail")
STOCK = os.path.join(STEP_DIR, "C-Beam 40x80x1000 Linear Rail.step")
OUT = os.path.join(os.path.dirname(__file__), "test_cbeam_post.step")
LENGTH = 1200.0

def discretize_wire(wire, deflection=1.0):
    """Convert a wire's curves to straight-line segments for compact STEP."""
    pts = []
    for edge in cq.Wire(wire).Edges():
        adaptor = BRepAdaptor_Curve(edge.wrapped)
        disc = GCPnts_TangentialDeflection(adaptor, deflection, 0.1)
        for i in range(1, disc.NbPoints() + 1):
            p = disc.Value(i)
            pts.append((p.X(), p.Y(), p.Z()))
    clean = [pts[0]]
    for p in pts[1:]:
        if any(abs(p[j] - clean[-1][j]) > 1e-6 for j in range(3)):
            clean.append(p)
    wb = BRepBuilderAPI_MakeWire()
    for i in range(len(clean)):
        p1 = gp_Pnt(*clean[i])
        p2 = gp_Pnt(*clean[(i + 1) % len(clean)])
        wb.Add(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
    return wb.Wire()

print(f"Loading {STOCK}...")
stock = cq.importers.importStep(STOCK)
face = stock.faces("<Z").val()
wires = face.Wires()
print(f"End face has {len(wires)} wires")

# Find the TRUE outer envelope by bbox area (largest)
def wire_area(w):
    bb = w.BoundingBox()
    return (bb.xmax - bb.xmin) * (bb.ymax - bb.ymin)

outer_idx = max(range(len(wires)), key=lambda i: wire_area(wires[i]))
outer_wire_raw = wires[outer_idx]
print(f"Outer wire is wire[{outer_idx}]: bbox area = {wire_area(outer_wire_raw):.0f}")

# Find the CENTRAL CHANNEL (the one on -X side, extending through most of the depth)
# Channel is ~16mm X-extent, 12mm Y-extent, centered on Y=0, at negative X
channel_idx = None
for i, w in enumerate(wires):
    if i == outer_idx:
        continue
    bb = w.BoundingBox()
    cx = (bb.xmin + bb.xmax) / 2
    cy = (bb.ymin + bb.ymax) / 2
    dx = bb.xmax - bb.xmin
    dy = bb.ymax - bb.ymin
    # Central channel: center Y near 0, center X negative (left side), width 10-20
    if abs(cy) < 3 and cx < -5 and 10 < dx < 20 and 10 < dy < 15:
        channel_idx = i
        print(f"Central channel: wire[{i}]  ctr=({cx:.1f},{cy:.1f})  {dx:.1f}x{dy:.1f}")
        break

if channel_idx is None:
    print("WARNING: Could not identify central channel — building without it")

# Discretize the outer wire (preserves V-slot detail but converts NURBS to lines)
print("Discretizing outer wire...")
outer_wire = discretize_wire(outer_wire_raw.wrapped, deflection=0.5)

# Build face with outer wire + optional central channel hole
if channel_idx is not None:
    channel_wire = discretize_wire(wires[channel_idx].wrapped, deflection=0.5)
    face_builder = BRepBuilderAPI_MakeFace(outer_wire)
    face_builder.Add(channel_wire)
    solid_face = face_builder.Face()
    print("Face built: outer V-slot profile + central C-channel cavity")
else:
    solid_face = BRepBuilderAPI_MakeFace(outer_wire).Face()
    print("Face built: outer V-slot profile only (no channel)")

# Extrude to 1200mm along +Z
prism = BRepPrimAPI_MakePrism(solid_face, gp_Vec(0, 0, LENGTH))
beam = cq.Workplane().add(cq.Shape(prism.Shape()))

# Count faces for verification
n_faces = len(beam.val().Faces())
bb = beam.val().BoundingBox()
print(f"\nResult:")
print(f"  bbox: X[{bb.xmin:.1f},{bb.xmax:.1f}] Y[{bb.ymin:.1f},{bb.ymax:.1f}] Z[{bb.zmin:.1f},{bb.zmax:.1f}]")
print(f"  faces: {n_faces}")

# Save standalone
from cadquery import Assembly, Color
assy = Assembly("test_cbeam_post")
assy.add(beam, name="cbeam_post", color=Color(0.20, 0.20, 0.22))
assy.save(OUT)
mb = os.path.getsize(OUT) / 1024 / 1024
print(f"\nWrote {OUT}  ({mb:.2f} MB)")
