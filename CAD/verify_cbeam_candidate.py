"""Verify a saved C-beam candidate against originals and existing CADCLAW rules.

Writes an explicit receipt outside source geometry. No healing or acceptance
rule changes. Requires the installed CadQuery/OCP and a CADCLAW source checkout.
"""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import sys
import zipfile

import cadquery as cq
import OCP
from OCP.BRep import BRep_Tool
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS

from cbeam_solids import ORIGINALS, SUPPLIER, CANDIDATE, bounds, face_signature, sha256


def topology(shape):
    edge_faces = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, edge_faces)
    free, nonmanifold = 0, 0
    for i in range(1, edge_faces.Extent()+1):
        edge = TopoDS.Edge_s(edge_faces.FindKey(i))
        faces = []
        for face in edge_faces.FindFromIndex(i):
            if not any(face.IsSame(f) for f in faces):
                faces.append(face)
        if len(faces) == 1 and not BRep_Tool.IsClosed_s(edge, TopoDS.Face_s(faces[0])):
            free += 1
        nonmanifold += len(faces) > 2
    b = bounds(shape)
    axis = max(range(3), key=lambda i: b[i+3]-b[i])
    ends = [f for f in shape.Faces() if abs(bounds(f)[axis+3]-bounds(f)[axis]) < 1e-6
            and min(abs(bounds(f)[axis]-b[axis]), abs(bounds(f)[axis]-b[axis+3])) < 1e-6]
    return {"type": shape.ShapeType(), "solids": len(shape.Solids()),
            "faces": len(shape.Faces()), "free_edges": free, "nonmanifold_edges": nonmanifold,
            "valid": shape.isValid(), "end_faces": len(ends),
            "end_inner_loops": [len(f.innerWires()) for f in ends]}


def zipped_bytes(path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('assembly.step', path.read_bytes())
    return len(buf.getvalue())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, default=CANDIDATE)
    p.add_argument('--original', type=Path, required=True,
                   help='Preserved pre-correction STEP with the historical open C-beam shells')
    p.add_argument('--cadclaw', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.cadclaw.resolve()))
    from cadclaw.assembly_compiler import SourceGeometryContext
    from cadclaw.compiler_adapter import qualify_source_groups, _compatible, _solid_metrics
    from cadclaw.characterization import characterize_solid
    from cadclaw.project import ProjectSession

    original = args.original.resolve()
    candidate = args.candidate.resolve()
    protected = {str(x): sha256(x) for x in (*ORIGINALS, original)}
    report = {'python': sys.version, 'cadquery': cq.__version__, 'OCP': OCP.__version__,
              'original_hashes': protected, 'candidate_sha256': sha256(candidate),
              'cadclaw_code': {name: sha256(args.cadclaw/'cadclaw'/name) for name in
                              ['compiler_adapter.py', 'characterization.py', 'project.py']},
              'status': 'in_progress'}
    def save():
        args.receipt.write_text(json.dumps(report, indent=2), encoding='utf-8')
    save()
    old = cq.Assembly.importStep(str(original))
    new = cq.Assembly.importStep(str(candidate))
    before = {c.name: c for c in old.children}
    after = {c.name: c for c in new.children}
    assert len(before) == len(old.children) == len(new.children) == len(after) == 158
    assert before.keys() == after.keys(), 'Occurrence names changed'
    stock = cq.importers.importStep(str(SUPPLIER)).val().Solids()[0]
    stock_volume = stock.Volume()
    report['occurrences'] = []
    for name, a in before.items():
        b = after[name]
        aw, bw = a.obj.moved(a.loc), b.obj.moved(b.loc)
        delta = max(abs(x-y) for x,y in zip(bounds(aw), bounds(bw)))
        assert delta < 1e-6, (name, 'world bounds changed', delta)
        ca = a.color.toTuple() if a.color else None
        cb = b.color.toTuple() if b.color else None
        assert ca == cb, (name, 'color changed')
        row = {'name': name, 'world_bounds_max_delta_mm': delta, 'color_preserved': True}
        old_faces = Counter(face_signature(f) for f in aw.Faces())
        new_faces = Counter(face_signature(f) for f in bw.Faces())
        if name.startswith('cbeam_'):
            assert old_faces <= new_faces, (name, 'original exterior faces changed')
            topo = topology(bw)
            assert topo == {'type':'Solid','solids':1,'faces':294,'free_edges':0,
                            'nonmanifold_edges':0,'valid':True,'end_faces':2,'end_inner_loops':[11,11]}, (name, topo)
            assert abs(bw.Volume()-stock_volume) < stock_volume*1e-9
            result = characterize_solid(bw, source_scale_to_m=.001)
            assert result['execution_status'] == 'completed', (name, result['error_code'])
            row.update(topology=topo, volume_mm3=bw.Volume(), cadclaw_solid=result)
        else:
            assert old_faces == new_faces, (name, 'non-beam faces changed')
            assert _compatible(_solid_metrics(aw), _solid_metrics(bw)), (name, 'non-beam metrics changed')
            row['non_beam_geometry_preserved'] = True
        report['occurrences'].append(row)
    report['beam_count'] = sum(x['name'].startswith('cbeam_') for x in report['occurrences'])
    assert report['beam_count'] == 17
    save()
    print('All 158 occurrences preserved; 17 closed supplier solids with 11 inner loops at each end', flush=True)

    def qualify(path):
        context = SourceGeometryContext()
        context.load(path)
        # Supply the ordinary compiler-instance contract to the unchanged gate.
        # No mock geometry/session or altered tolerance/limit is supplied.
        instance = {'id':'assembly', 'role':'authored', 'source_ref':path.name,
                    'resolved_path':str(path.resolve()), 'exists':True,
                    'transform':{'translate_mm':[0.,0.,0.], 'rotate_deg':[0.,0.,0.],
                                 'scale':1., 'source_origin_mm':[0.,0.,0.]},
                    'color_label':None, 'connector_metadata':'not_checked'}
        return qualify_source_groups([instance], context, ProjectSession())
    report['original_qualification'] = qualify(original)
    save()
    print('Original gate:', report['original_qualification']['execution_status'],
          report['original_qualification']['error_code'], flush=True)
    report['candidate_qualification'] = qualify(candidate)
    save()
    assert report['original_qualification']['error_code'] == 'non_solid_source_geometry'
    assert report['candidate_qualification']['execution_status'] == 'completed', report['candidate_qualification']
    for x in report['candidate_qualification']['sources']:
        assert x['coverage_complete'] and x['flat_solids'] == x['xcaf_solids'] == 158
    report['size'] = {'original_step_bytes':original.stat().st_size,
                      'candidate_step_bytes':candidate.stat().st_size,
                      'original_zip_bytes':zipped_bytes(original), 'candidate_zip_bytes':zipped_bytes(candidate)}
    assert report['size']['candidate_step_bytes'] < report['size']['original_step_bytes']
    report['source_hashes_unchanged'] = all(sha256(path) == digest for path,digest in protected.items())
    assert report['source_hashes_unchanged']
    report['status'] = 'PASS'
    save()
    print('PASS: unchanged CADCLAW whole-source gate; originals unchanged; size', report['size'], flush=True)


if __name__ == '__main__':
    main()
