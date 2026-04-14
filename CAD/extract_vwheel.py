"""Extract V-wheel profile geometry from Solid V Wheel STEP file."""
import cadquery as cq
import math

shape = cq.importers.importStep("y:/SunnydayTech/M3-CRETE/CAD/Components/Wheels/Solid V Wheel.step")

bb = shape.val().BoundingBox()
print(f"Bounding box: X={bb.xlen:.2f}, Y={bb.ylen:.2f}, Z={bb.zlen:.2f}")
print(f"  min=({bb.xmin:.2f}, {bb.ymin:.2f}, {bb.zmin:.2f})")
print(f"  max=({bb.xmax:.2f}, {bb.ymax:.2f}, {bb.zmax:.2f})")
print()

from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Torus
from OCP.BRepAdaptor import BRepAdaptor_Surface

solid = shape.val().wrapped
explorer = TopExp_Explorer(solid, TopAbs_FACE)

cylinders = []
cones = []
toruses = []
others = {}

while explorer.More():
    face = explorer.Current()
    surf = BRepAdaptor_Surface(face)
    gtype = surf.GetType()

    if gtype == GeomAbs_Cylinder:
        cyl = surf.Cylinder()
        loc = cyl.Location()
        axis = cyl.Axis().Direction()
        radius = cyl.Radius()
        cylinders.append({
            'cx': loc.X(), 'cy': loc.Y(), 'cz': loc.Z(),
            'radius': radius,
            'ax': axis.X(), 'ay': axis.Y(), 'az': axis.Z()
        })
    elif gtype == GeomAbs_Cone:
        cone = surf.Cone()
        loc = cone.Location()
        axis = cone.Axis().Direction()
        semi_angle = cone.SemiAngle()
        ref_radius = cone.RefRadius()
        cones.append({
            'cx': loc.X(), 'cy': loc.Y(), 'cz': loc.Z(),
            'semi_angle_rad': semi_angle,
            'semi_angle_deg': math.degrees(semi_angle),
            'ref_radius': ref_radius,
            'ax': axis.X(), 'ay': axis.Y(), 'az': axis.Z()
        })
    elif gtype == GeomAbs_Torus:
        torus = surf.Torus()
        loc = torus.Location()
        major_r = torus.MajorRadius()
        minor_r = torus.MinorRadius()
        toruses.append({
            'cx': loc.X(), 'cy': loc.Y(), 'cz': loc.Z(),
            'major_radius': major_r, 'minor_radius': minor_r
        })
    else:
        name = str(gtype)
        others[name] = others.get(name, 0) + 1

    explorer.Next()

# Deduplicate cylinders
seen = set()
unique_cyl = []
for c in cylinders:
    key = (round(c['cx'], 2), round(c['cy'], 2), round(c['cz'], 2), round(c['radius'], 3))
    if key not in seen:
        seen.add(key)
        unique_cyl.append(c)
unique_cyl.sort(key=lambda c: c['radius'])

print(f"=== CYLINDRICAL FACES ({len(unique_cyl)} unique) ===")
for i, c in enumerate(unique_cyl, 1):
    print(f"  #{i}: center=({c['cx']:.3f}, {c['cy']:.3f}, {c['cz']:.3f}), "
          f"R={c['radius']:.4f}mm, D={c['radius']*2:.4f}mm, "
          f"axis=({c['ax']:.3f}, {c['ay']:.3f}, {c['az']:.3f})")

# Deduplicate cones
seen = set()
unique_cones = []
for c in cones:
    key = (round(c['cx'], 2), round(c['cy'], 2), round(c['cz'], 2),
           round(c['semi_angle_deg'], 2), round(c['ref_radius'], 3))
    if key not in seen:
        seen.add(key)
        unique_cones.append(c)

print(f"\n=== CONICAL FACES ({len(unique_cones)} unique) ===")
for i, c in enumerate(unique_cones, 1):
    print(f"  #{i}: center=({c['cx']:.3f}, {c['cy']:.3f}, {c['cz']:.3f}), "
          f"semi_angle={c['semi_angle_deg']:.2f}deg, ref_radius={c['ref_radius']:.4f}mm, "
          f"axis=({c['ax']:.3f}, {c['ay']:.3f}, {c['az']:.3f})")

if toruses:
    print(f"\n=== TORUS FACES ({len(toruses)}) ===")
    for i, t in enumerate(toruses, 1):
        print(f"  #{i}: center=({t['cx']:.3f}, {t['cy']:.3f}, {t['cz']:.3f}), "
              f"major_R={t['major_radius']:.4f}mm, minor_R={t['minor_radius']:.4f}mm")

if others:
    print(f"\n=== OTHER FACE TYPES ===")
    for k, v in others.items():
        print(f"  {k}: {v} faces")

# Derive V-groove geometry
print("\n=== V-GROOVE ANALYSIS ===")
diameters = sorted(set(round(c['radius']*2, 3) for c in unique_cyl))
print(f"All cylinder diameters: {diameters}")

if unique_cones:
    semi = unique_cones[0]['semi_angle_deg']
    print(f"Cone semi-angle: {semi:.2f} deg")
    print(f"Full V-angle (included angle): {abs(2*semi):.2f} deg")
    for c in unique_cones:
        print(f"  Cone ref_radius={c['ref_radius']:.4f}mm (ref_diam={c['ref_radius']*2:.4f}mm), "
              f"semi={c['semi_angle_deg']:.2f}deg")

if len(diameters) >= 2:
    bore_d = diameters[0]
    outer_d = diameters[-1]
    print(f"\nBore diameter (smallest cylinder): {bore_d:.3f}mm")
    print(f"Outer rim diameter (largest cylinder): {outer_d:.3f}mm")

    if unique_cones:
        # V-bottom is at the cone ref_radius
        v_bottom_r = unique_cones[0]['ref_radius']
        v_bottom_d = v_bottom_r * 2
        outer_r = outer_d / 2
        groove_depth = (outer_r - v_bottom_r) * abs(math.tan(math.radians(abs(semi))))
        print(f"V-bottom diameter (cone ref): {v_bottom_d:.3f}mm")
        print(f"Groove depth (radial): {outer_r - v_bottom_r:.3f}mm")
        print(f"Groove depth (axial, from rim to V-bottom): {groove_depth:.3f}mm")
