#!/usr/bin/env python3
"""
Generate parametric V-Slot extrusions at exact lengths by extracting
the cross-section profile from the OpenBuilds STEP files and extruding
to the specified length.

This preserves the exact V-groove geometry, fillet radii, and slot
dimensions from the original STEP while allowing any custom length.
"""
import cadquery as cq
import os

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components", "V-Slot")


def make_extrusion(step_file: str, length_mm: float):
    """
    Load a V-Slot STEP file, extract its end-face cross-section,
    and extrude it to the desired length.

    The STEP files have their length along Z, with end faces at Z=0 and Z=1000.
    We take the Z=0 face (bottom), extract its wire outline, and extrude along +Z.
    """
    path = os.path.join(STEP_DIR, step_file)
    stock = cq.importers.importStep(path)

    # Get the bottom end face (Z=0) — this is the cross-section profile
    # The end face is the one with minimum Z center
    end_face = stock.faces("<Z").val()

    # Create a workplane on that face and extrude
    result = (
        cq.Workplane("XY")
        .add(cq.Workplane(end_face))
        .wires()
        .toPending()
        .extrude(length_mm)
    )

    return result


def make_extrusion_simple(step_file: str, length_mm: float):
    """
    Simpler approach: load the STEP, get the solid, slice at Z=0 to get
    the cross-section, then extrude to length.
    """
    path = os.path.join(STEP_DIR, step_file)
    stock = cq.importers.importStep(path)

    # Get the cross-section by sectioning at Z near 0
    section = stock.section(0.5)  # Section at Z=0.5mm

    # Extrude the section profile
    result = section.extrude(length_mm)

    return result


def make_extrusion_scale(step_file: str, length_mm: float):
    """
    Scale approach: load 1000mm STEP and scale Z axis to get desired length.
    This scales the profile too, but at 1.2x the distortion is only in Z
    (length direction) which doesn't affect the cross-section.

    Actually, we need non-uniform scaling. CadQuery doesn't support this directly.
    Use OCP (OpenCascade) transform instead.
    """
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform

    path = os.path.join(STEP_DIR, step_file)
    stock = cq.importers.importStep(path)

    # Get the underlying OCC shape
    shape = stock.val().wrapped

    # Create non-uniform scale: X=1, Y=1, Z=length_mm/1000
    scale_z = length_mm / 1000.0
    gtrsf = gp_GTrsf()
    mat = gp_Mat(
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, scale_z
    )
    gtrsf.SetVectorialPart(mat)

    # Apply the transform
    builder = BRepBuilderAPI_GTransform(shape, gtrsf, True)
    builder.Build()
    scaled_shape = builder.Shape()

    # Wrap back into CadQuery
    return cq.Workplane().add(cq.Shape(scaled_shape))


if __name__ == "__main__":
    print("Testing parametric extrusion generation...\n")

    TARGET_LEN = 1200.0

    # Test the non-uniform scale approach (most reliable for STEP imports)
    for name, step_file in [
        ("2080", "V-Slot 20x80x1000 Linear Rail.step"),
        ("2040", "V-Slot 20x40x1000 Linear Rail.step"),
    ]:
        print(f"  {name} at {TARGET_LEN}mm...")
        try:
            result = make_extrusion_scale(step_file, TARGET_LEN)
            bb = result.val().BoundingBox()
            print(f"    BBox: X[{bb.xmin:.2f},{bb.xmax:.2f}] Y[{bb.ymin:.2f},{bb.ymax:.2f}] Z[{bb.zmin:.2f},{bb.zmax:.2f}]")
            print(f"    Size: {bb.xmax-bb.xmin:.2f} x {bb.ymax-bb.ymin:.2f} x {bb.zmax-bb.zmin:.2f}")

            # Export test
            out_path = os.path.join(os.path.dirname(__file__), f"Custom/{name}_{int(TARGET_LEN)}mm.step")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            cq.exporters.export(result, out_path)
            size_kb = os.path.getsize(out_path) / 1024
            print(f"    Exported: {out_path} ({size_kb:.0f} KB)")
        except Exception as e:
            print(f"    FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\nDone.")
