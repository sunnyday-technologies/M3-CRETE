"""Restore complete supplier C-beams without changing assembly placements.

The frozen baseline swept only the supplier outer wire, producing uncapped
shells and omitting eleven internal loops. Use the original supplier solid,
with the same seven rigid orientations, instead of capping/filling that shell.
No sewing, healing, discretization, fusion or geometry scaling is performed.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json

import cadquery as cq
from step_compact import export_compact_assembly

HERE = Path(__file__).resolve().parent
SUPPLIER = HERE / "Advanced/Linear Rail/C-Beam 40x80x1000 Linear Rail.step"
SUPPLIER_SHA256 = "a29914be79093d6fb224c8031c35711afc8d3debebb535984c01d579f0bc3dc5"
CANDIDATE = HERE / "M3-2_Assembly_cbeam_candidate.step"
ORIGINALS = (HERE / "M3-2_V1.0_baseline.step", HERE / "M3-2_Assembly.step", SUPPLIER)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounds(shape):
    b = shape.BoundingBox()
    return tuple(getattr(b, k) for k in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"))


def face_signature(face):
    """Orientation-matching aid, not a substitute for geometric qualification."""
    return (face.geomType(), round(face.Area(), 5), *(round(v, 5) for v in bounds(face)))


def supplier_templates():
    if sha256(SUPPLIER) != SUPPLIER_SHA256:
        raise ValueError("Supplier STEP changed; review the profile before regeneration")
    imported = cq.importers.importStep(str(SUPPLIER)).val()
    solids = imported.Solids()
    if len(solids) != 1 or not solids[0].isValid():
        raise ValueError("Supplier must contain one valid solid")
    stock = solids[0]
    end = cq.Workplane().add(stock).faces("<Z").val()
    if len(end.innerWires()) != 11 or len(stock.Faces()) != 294:
        raise ValueError("Unexpected supplier cavities or face inventory")
    def rotation(axis, angle):
        return cq.Location(cq.Vector(), cq.Vector(*axis), angle)
    yr = rotation((1, 0, 0), -90)
    xp = rotation((1, 0, 0), 90) * rotation((0, 1, 0), 90)
    return stock, {
        "supplier_native": cq.Location(),  # already-instanced corrected input
        "Zrear": rotation((0, 0, 1), 90),
        "Zfront": rotation((0, 0, 1), -90),
        "Yright": yr,
        "Yleft": rotation((0, 1, 0), 180) * yr,
        "Yflat": rotation((0, 1, 0), 90) * yr,
        "Xpositive": xp,
        "Xnegative": rotation((1, 0, 0), 180) * xp,
    }


def restore_supplier_cbeams(assembly):
    """Replace only the 17 named beams, after matching all original side faces.

    Names, world placements, colors and all non-beam objects stay in place.
    Factor baked-in local orientations into locations so all 17 occurrences
    share ONE supplier solid definition, rather than seven rotated copies.
    Validate every replacement before changing any assembly object.
    """
    beams = [c for c in assembly.children if c.name.startswith("cbeam_")]
    if len(beams) != 17:
        raise ValueError(f"Expected 17 C-beams, found {len(beams)}")
    stock, orientations = supplier_templates()
    templates = {key: stock.moved(loc) for key, loc in orientations.items()}
    shared, pending, records = {}, [], []
    for child in beams:
        old = child.obj
        if old.ShapeType() not in ("Shell", "Solid"):
            raise ValueError(f"Unsupported C-beam shape: {child.name}")
        if len(old.Faces()) not in (224, 294):
            raise ValueError(f"Unexpected C-beam face inventory: {child.name}")
        ob = bounds(old)
        old_faces = Counter(face_signature(f) for f in old.Faces())
        matches = []
        for key, template in templates.items():
            tb = bounds(template)
            if any(abs((ob[i+3]-ob[i])-(tb[i+3]-tb[i])) > 1e-6 for i in range(3)):
                continue
            shift = tuple(ob[i]-tb[i] for i in range(3))
            # Tiny STEP numerical noise must not create a fresh definition per instance.
            shift = tuple(round(x, 8) for x in shift)
            cache_key = (key, shift)
            shape = shared.get(cache_key)
            if shape is None:
                shape = template if shift == (0., 0., 0.) else template.translate(shift)
                shared[cache_key] = shape
            if old_faces <= Counter(face_signature(f) for f in shape.Faces()):
                matches.append((key, shape, cq.Location(cq.Vector(*shift)) * orientations[key]))
        if len(matches) != 1:
            raise ValueError(f"C-beam orientation not uniquely matched: {child.name} ({len(matches)})")
        key, solid, local_placement = matches[0]
        if max(abs(a-b) for a,b in zip(ob, bounds(solid))) > 1e-6:
            raise ValueError(f"C-beam local bounds changed: {child.name}")
        new_location = child.loc * local_placement
        pending.append((child, new_location))
        records.append({"name": child.name, "template": key,
                        "old_location": child.loc.toTuple(), "new_location": new_location.toTuple(),
                        "old_type": old.ShapeType(),
                        "local_bounds": ob, "old_faces": len(old.Faces()),
                        "new_faces": len(solid.Faces()), "supplier_inner_loops": 11})
    for child, new_location in pending:
        child.obj = stock
        child.loc = new_location
    return records


def export_candidate(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output in [p.resolve() for p in ORIGINALS] or output == source:
        raise ValueError("Refusing to overwrite original/source geometry")
    if output.exists():
        raise FileExistsError("Candidate already exists; choose a new output path")
    hashes = {str(p): sha256(p) for p in (*ORIGINALS, source)}
    assembly = cq.Assembly.importStep(str(source))
    records = restore_supplier_cbeams(assembly)
    optimization = export_compact_assembly(assembly, output)
    if any(sha256(p) != digest for p, digest in hashes.items()):
        raise RuntimeError("An input changed during export")
    return {"source_hashes": hashes, "candidate_sha256": sha256(output),
            "write_pcurves": False,
            "step_compaction": optimization,
            "source_bytes": source.stat().st_size, "candidate_bytes": output.stat().st_size,
            "beam_occurrences": records, "assembly_children": len(assembly.children)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "M3-2_Assembly.step")
    parser.add_argument("--output", type=Path, default=CANDIDATE)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = export_candidate(args.source, args.output)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Exported {receipt['assembly_children']} occurrences, including 17 supplier-solid C-beams")
    print(f"STEP bytes: {receipt['source_bytes']} -> {receipt['candidate_bytes']}")
