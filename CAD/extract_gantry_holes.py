"""Extract hole positions from V-Slot Gantry Plate 20-80mm STEP file."""
import cadquery as cq
from collections import defaultdict

shape = cq.importers.importStep("y:/SunnydayTech/M3-CRETE/CAD/Components/Plates/V-Slot Gantry Plate 20-80mm.step")

bb = shape.val().BoundingBox()
print(f"Bounding box: X={bb.xlen:.2f}, Y={bb.ylen:.2f}, Z={bb.zlen:.2f}")
print(f"  min=({bb.xmin:.2f}, {bb.ymin:.2f}, {bb.zmin:.2f})")
print(f"  max=({bb.xmax:.2f}, {bb.ymax:.2f}, {bb.zmax:.2f})")
print()

from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.BRepAdaptor import BRepAdaptor_Surface

solid = shape.val().wrapped
explorer = TopExp_Explorer(solid, TopAbs_FACE)

holes = []
seen = set()

while explorer.More():
    face = explorer.Current()
    surf = BRepAdaptor_Surface(face)
    if surf.GetType() == GeomAbs_Cylinder:
        cyl = surf.Cylinder()
        loc = cyl.Location()
        axis = cyl.Axis().Direction()
        radius = cyl.Radius()
        key = (round(loc.X(), 2), round(loc.Y(), 2), round(loc.Z(), 2), round(radius, 3))
        if key not in seen:
            seen.add(key)
            holes.append({
                'cx': loc.X(), 'cy': loc.Y(), 'cz': loc.Z(),
                'radius': radius,
                'ax': axis.X(), 'ay': axis.Y(), 'az': axis.Z()
            })
    explorer.Next()

holes.sort(key=lambda h: (round(h['cx'], 1), round(h['cz'], 1)))

print(f"Found {len(holes)} cylindrical faces (unique):")
print(f"{'#':>3}  {'CenterX':>8} {'CenterY':>8} {'CenterZ':>8}  {'Radius':>7} {'Diam':>7}  {'AxisX':>6} {'AxisY':>6} {'AxisZ':>6}")
print("-" * 85)
for i, h in enumerate(holes, 1):
    print(f"{i:3d}  {h['cx']:8.3f} {h['cy']:8.3f} {h['cz']:8.3f}  {h['radius']:7.3f} {h['radius']*2:7.3f}  {h['ax']:6.3f} {h['ay']:6.3f} {h['az']:6.3f}")

by_diam = defaultdict(list)
for h in holes:
    d = round(h['radius'] * 2, 2)
    by_diam[d].append(h)

print(f"\nHoles grouped by diameter:")
for d in sorted(by_diam.keys()):
    print(f"  Diameter {d:.2f}mm: {len(by_diam[d])} holes")
