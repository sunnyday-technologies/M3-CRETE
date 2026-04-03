#!/usr/bin/env python3
"""
Deep geometry probe for M3-CRETE assembly precision.
Extracts bounding boxes, bolt hole positions, mounting faces, and V-groove geometry
from each STEP component. Output is used to compute exact face-mating positions.

Run: cad_venv/Scripts/python.exe CAD/deep_probe.py
"""
import cadquery as cq
import os
import json
from collections import defaultdict

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")

PARTS = {
    "2080": "V-Slot/V-Slot 20x80x1000 Linear Rail.step",
    "2040": "V-Slot/V-Slot 20x40x1000 Linear Rail.step",
    "gantry_plate": "Plates/V-Slot Gantry Plate 20-80mm.step",
    "motor_mount": "Plates/Motor Mount Plate Nema 23.step",
    "idler_plate": "Plates/Idler Pulley Plate.step",
    "cast_bracket": "Brackets/Cast Corner Bracket.step",
    "cube_connector": "Brackets/Cube Corner Connector.step",
    "nema23": "Electronics/Nema 23 Stepper Motor.step",
    "v_wheel": "Wheels/Xtreme Solid V Wheel.step",
    "gt2_pulley": "Pulleys/GT2 Timing Pulley 20 Tooth.step",
    "idler_pulley": "Pulleys/Smooth Idler Pulley Wheel.step",
    "eccentric_spacer": "Hardware/Eccentric Spacer 6mm.step",
    "limit_switch": "Electronics/Micro Limit Switch.step",
    "limit_switch_plate": "Electronics/Micro Limit Switch Plate.step",
}


def analyze(name, relpath):
    path = os.path.join(STEP_DIR, relpath)
    if not os.path.exists(path):
        print(f"  MISSING: {relpath}")
        return None

    shape = cq.importers.importStep(path)
    bb = shape.val().BoundingBox()

    print(f"\n{'='*60}")
    print(f"  {name}: {relpath}")
    print(f"{'='*60}")
    print(f"  BBox: X[{bb.xmin:.2f}, {bb.xmax:.2f}]  Y[{bb.ymin:.2f}, {bb.ymax:.2f}]  Z[{bb.zmin:.2f}, {bb.zmax:.2f}]")
    print(f"  Size: {bb.xmax-bb.xmin:.2f} x {bb.ymax-bb.ymin:.2f} x {bb.zmax-bb.zmin:.2f}")

    # Count face types
    try:
        all_faces = shape.faces().vals()
        face_types = defaultdict(int)
        for f in all_faces:
            face_types[f.geomType()] += 1
        print(f"  Faces: {dict(face_types)} (total {len(all_faces)})")
    except Exception as e:
        print(f"  Faces: error - {e}")
        all_faces = []

    # Find bolt holes (circular edges)
    try:
        circles = shape.edges("%CIRCLE").vals()
        hole_radii = defaultdict(list)
        for edge in circles:
            r = round(edge.radius(), 2)
            c = edge.arcCenter()
            hole_radii[r].append((round(c.x, 2), round(c.y, 2), round(c.z, 2)))

        if hole_radii:
            print(f"  Circular features ({len(circles)} total):")
            for r in sorted(hole_radii.keys()):
                centers = hole_radii[r]
                label = ""
                d = r * 2
                if 4.8 < d < 5.5: label = " [M5 clearance]"
                elif 3.0 < d < 3.5: label = " [M3 clearance]"
                elif 7.5 < d < 8.5: label = " [bearing bore 8mm]"
                elif 4.5 < d < 5.0: label = " [M5 tap / bearing 5mm]"
                elif 10.0 < d < 12.0: label = " [wheel OD ~11mm]"
                elif 22.0 < d < 25.0: label = " [V-wheel OD ~24mm]"
                print(f"    r={r:.2f}mm (d={d:.2f}mm){label}: {len(centers)} instances")
                # Show first few centers for small counts
                if len(centers) <= 8:
                    for cx, cy, cz in centers:
                        print(f"      center: ({cx}, {cy}, {cz})")
                else:
                    # Just show unique Z positions for extrusions
                    z_vals = sorted(set(cz for _, _, cz in centers))
                    if len(z_vals) <= 4:
                        print(f"      Z positions: {z_vals}")
                    else:
                        print(f"      Z range: [{min(z_vals)}, {max(z_vals)}] ({len(z_vals)} positions)")
        else:
            print(f"  No circular features found")
    except Exception as e:
        print(f"  Circles: error - {e}")

    # Key mounting faces (largest planar faces by area)
    try:
        plane_faces = shape.faces("%PLANE").vals()
        if plane_faces:
            face_data = []
            for f in plane_faces:
                c = f.Center()
                n = f.normalAt(c)
                face_data.append({
                    'area': f.Area(),
                    'center': (round(c.x, 2), round(c.y, 2), round(c.z, 2)),
                    'normal': (round(n.x, 3), round(n.y, 3), round(n.z, 3)),
                })
            # Sort by area, show top 6
            face_data.sort(key=lambda f: f['area'], reverse=True)
            print(f"  Top mounting faces (of {len(plane_faces)} planar):")
            for fd in face_data[:6]:
                a = fd['area']
                c = fd['center']
                n = fd['normal']
                print(f"    area={a:.1f}mm²  center=({c[0]}, {c[1]}, {c[2]})  normal=({n[0]}, {n[1]}, {n[2]})")
    except Exception as e:
        print(f"  Faces: error - {e}")

    return {
        'bbox': {
            'xmin': bb.xmin, 'xmax': bb.xmax,
            'ymin': bb.ymin, 'ymax': bb.ymax,
            'zmin': bb.zmin, 'zmax': bb.zmax,
        },
        'size': (bb.xmax-bb.xmin, bb.ymax-bb.ymin, bb.zmax-bb.zmin),
    }


if __name__ == "__main__":
    print("M3-CRETE Deep Geometry Probe")
    print("Extracting precision data from STEP components...\n")

    results = {}
    for name, relpath in PARTS.items():
        r = analyze(name, relpath)
        if r:
            results[name] = r

    print(f"\n\n{'='*60}")
    print("SUMMARY — Bounding boxes for assembly math")
    print(f"{'='*60}")
    for name, r in results.items():
        s = r['size']
        print(f"  {name:20s}: {s[0]:7.2f} x {s[1]:7.2f} x {s[2]:7.2f}")
