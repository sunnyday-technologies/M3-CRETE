"""Strict saved-STEP checks for the bounded four-wheel reference placement."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import cadquery as cq
import OCP
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from cbeam_solids import bounds, face_signature
from x_carriage_placement import WHEEL_PAIRS

LABELS={(40.,80.,1000.):'cbeam',(56.4,56.4,76.6):'motor',
        (10.2,23.9,23.9):'vwheel',(14.,15.,15.):'pulley',(12.7,22.,22.):'idler',
        (3.,88.,127.):'plate',(4.,40.,80.):'shim',(4.,80.,96.):'zmount',
        (5.,40.,80.):'zcap',(4.,80.,100.):'bot-mount',(4.,80.,80.):'ymount',
        (5.,30.,30.):'idler-brk'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def center(shape):
    b=bounds(shape)
    return tuple((b[i]+b[i+3])/2 for i in range(3))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['before','candidate','generation','prior-findings','cadclaw','receipt']:
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    assert not args.receipt.exists(), 'Preserve previous receipts'
    sys.path.insert(0,str(args.cadclaw.resolve()))
    from cadclaw.assembly_compiler import SourceGeometryContext
    from cadclaw.compiler_adapter import qualify_source_groups, _compatible, _solid_metrics
    from cadclaw.project import ProjectSession
    from cadclaw.interference import _bb_overlap_bounds
    before_hash,candidate_hash=digest(args.before),digest(args.candidate)
    generation=json.loads(args.generation.read_text())
    prior=json.loads(args.prior_findings.read_text(encoding='utf-8-sig'))
    assert generation['candidate_sha256']==candidate_hash
    assert prior['source_sha256']==before_hash
    report={'status':'in_progress','cadquery':cq.__version__,'OCP':OCP.__version__,
            'before_sha256':before_hash,'candidate_sha256':candidate_hash,
            'reference_placement_status':'owner_confirmed',
            'physical_acceptance':'not_evaluated','whole_machine_interference_coverage':False,
            'occurrences':[]}
    def save():
        args.receipt.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save()
    old,new=cq.Assembly.importStep(str(args.before)),cq.Assembly.importStep(str(args.candidate))
    before={c.name:c for c in old.children}
    after={c.name:c for c in new.children}
    assert len(before)==len(old.children)==len(after)==len(new.children)==158
    assert before.keys()==after.keys()
    def world(c):
        return c.obj.moved(c.loc)
    midpoint=sum(center(world(before[n]))[1] for n in ['plate_85','plate_134'])/2
    changed=[]
    for name,b in after.items():
        a=before[name]
        original,actual=world(a),world(b)
        expected=original
        row={'name':name}
        if name in WHEEL_PAIRS:
            s=center(original)
            r=center(world(before[WHEEL_PAIRS[name]]))
            target=(r[0],2*midpoint-r[1],r[2])
            expected=original.translate(tuple(-v for v in s)).rotate((0,0,0),(0,0,1),-90).translate(target)
            assert max(abs(x-y) for x,y in zip(center(actual),target))<1e-6
            changed.append(name)
            row.update(proposed_target_center_mm=target,rotation_world_z_deg=-90)
        delta=max(abs(x-y) for x,y in zip(bounds(expected),bounds(actual)))
        assert delta<1e-6,(name,'unexpected placement',delta)
        assert Counter(face_signature(f) for f in expected.Faces())==Counter(face_signature(f) for f in actual.Faces()),(name,'unexpected surfaces')
        assert _compatible(_solid_metrics(expected),_solid_metrics(actual)),(name,'unexpected geometric metrics')
        assert len(actual.Solids())==1 and actual.isValid(),(name,'invalid or incomplete solid')
        assert (a.color.toTuple() if a.color else None)==(b.color.toTuple() if b.color else None)
        row.update(valid_solid=True,rigid_geometry_color_preserved=True,world_bounds_max_delta_mm=delta)
        report['occurrences'].append(row)
    counts={'total':len(after),'vwheels':sum(n.startswith('vwheel_') for n in after),
            'cbeams':sum(n.startswith('cbeam_') for n in after),
            'leadscrews':sum(n.startswith('leadscrew_') for n in after)}
    assert counts=={'total':158,'vwheels':32,'cbeams':17,'leadscrews':4}
    assert set(changed)==set(WHEEL_PAIRS)
    report.update(inventory=counts,changed_poses=changed,unchanged_poses=154,
                  plate_midpoint_y_mm=midpoint)
    save()
    print('PASS: all 158 solids valid; only four specified rigid poses changed',flush=True)
    context=SourceGeometryContext()
    context.load(args.candidate)
    instance={'id':'assembly','role':'authored','source_ref':args.candidate.name,
              'resolved_path':str(args.candidate.resolve()),'exists':True,
              'transform':{'translate_mm':[0.,0.,0.],'rotate_deg':[0.,0.,0.],
                           'scale':1.,'source_origin_mm':[0.,0.,0.]},
              'color_label':None,'connector_metadata':'not_checked'}
    qualification=qualify_source_groups([instance],context,ProjectSession())
    report['source_qualification']=qualification
    save()
    assert qualification['execution_status']=='completed',qualification
    for source in qualification['sources']:
        assert source['coverage_complete'] and source['flat_solids']==source['xcaf_solids']==158
    print('PASS: strict CADCLAW flat/XCAF source qualification covers 158/158 solids',flush=True)
    source={'id':'m3-proposal','path':str(args.candidate.resolve()),'sha256':candidate_hash,
            'revision':'dual-plate-proposal-20261022','geometry_units':'mm'}
    parts=[]
    for index,(path,shape) in enumerate(ProjectSession()._groups(source)):
        assert len(shape.Solids())==1
        solid=shape.Solids()[0]
        bb=bounds(solid)
        dims=tuple(sorted(round(bb[i+3]-bb[i],1) for i in range(3)))
        kind=LABELS.get(dims,'belt' if dims[:2]==(1.5,6.) else 'other')
        if kind not in {'belt','pulley','other'}:
            parts.append((path.rsplit('/',1)[-1],kind,solid,bb,index))
    findings=[]
    checked=0
    for i,(an,al,a,ab,ai) in enumerate(parts):
        for bn,bl,b,bb,bi in parts[i+1:]:
            if not _bb_overlap_bounds(ab,bb):
                continue
            checked+=1
            common=BRepAlgoAPI_Common(a.wrapped,b.wrapped)
            common.Build()
            assert common.IsDone(),(an,bn,'boolean failed')
            props=GProp_GProps()
            BRepGProp.VolumeProperties_s(common.Shape(),props)
            volume=props.Mass()
            if volume>1.:
                findings.append({'a':{'source_name':an,'label':al,'group_index':ai},
                                 'b':{'source_name':bn,'label':bl,'group_index':bi},'volume_mm3':volume})
    def key(r):
        return tuple(sorted((r['a']['source_name'],r['b']['source_name'])))
    fixed_before={key(r):r for r in prior['findings'] if not set(key(r))&set(WHEEL_PAIRS)}
    fixed_after={key(r):r for r in findings if not set(key(r))&set(WHEEL_PAIRS)}
    assert fixed_before.keys()==fixed_after.keys() and len(fixed_after)==29
    for pair,row in fixed_after.items():
        assert abs(row['volume_mm3']-fixed_before[pair]['volume_mm3'])<.001,pair
    report['interference']={'eligible_parts':len(parts),'checked_pairs':checked,'findings':findings,
                            'finding_count':len(findings),'threshold_mm3':1.,
                            'prior_criteria_unchanged':True,'unmoved_pair_findings_preserved':29,
                            'moved_wheel_findings':[r for r in findings if set(key(r))&set(WHEEL_PAIRS)]}
    assert digest(args.before)==before_hash and digest(args.candidate)==candidate_hash
    report['inputs_unchanged']=True
    report['design_acceptance']='NOT_ACCEPTED: reference placement approved; fastening fit not established, contact/preload and motor/plate disposition remain open'
    report['status']='PASS_BOUNDED_REFERENCE_GEOMETRY_VALIDATION'
    save()
    print(f'PASS: exact interference comparison complete; {len(findings)} remaining findings, none waived',flush=True)

if __name__=='__main__':
    main()
