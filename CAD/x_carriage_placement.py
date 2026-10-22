"""Owner-approved reference placement of the second X-carriage wheel set.

The owner approved this rigid reference placement on 2026-10-22.
It does not establish hole mating, preload, spacer dimensions, or acceptance.
No wheel, plate, or fastening geometry is generated here.
"""
from collections import Counter
import cadquery as cq

WHEEL_PAIRS = {
    'vwheel_123': 'vwheel_64',
    'vwheel_124': 'vwheel_65',
    'vwheel_125': 'vwheel_63',
    'vwheel_126': 'vwheel_66',
}
PLATES = ('plate_85', 'plate_134')


def _bounds(child):
    b = child.obj.moved(child.loc).BoundingBox()
    return (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)


def _centre(bounds):
    return tuple((bounds[i]+bounds[i+3])/2 for i in range(3))


def derive_x_carriage_proposal(children):
    """Validate raw identities before dedup, then return four rigid transforms.

    Target X/Z uses the corresponding existing motor-side wheel. Target Y
    reflects its centre through the midpoint of the two authored plate centres.
    Rotation is -90 degrees about world Z, taking the existing X wheel axis
    parallel to the Y motor-side axis. The plate midpoint is an explicit review
    convention; it is not a proven mating or contact datum.
    """
    children = list(children)
    required = set(WHEEL_PAIRS) | set(WHEEL_PAIRS.values()) | set(PLATES)
    counts = Counter(c.name for c in children)
    invalid = {name: counts[name] for name in sorted(required) if counts[name] != 1}
    if invalid:
        raise ValueError(f'X-carriage proposal requires unique raw occurrences: {invalid}')
    selected = {c.name: c for c in children if c.name in required}
    bounds = {name: _bounds(child) for name, child in selected.items()}
    for name in PLATES:
        dims = tuple(bounds[name][i+3]-bounds[name][i] for i in range(3))
        if any(abs(a-b)>1e-6 for a,b in zip(dims, (88., 3., 127.))):
            raise ValueError(f'Authored X-carriage plate orientation changed: {name}')
    if any(abs(bounds[PLATES[0]][i]-bounds[PLATES[1]][i])>1e-6 for i in (0,2,3,5)):
        raise ValueError('Authored X-carriage plates do not share X/Z bounds')
    midpoint = sum(_centre(bounds[name])[1] for name in PLATES)/2
    poses, records = {}, []
    for name, reference in WHEEL_PAIRS.items():
        for wheel, expected in ((name, (10.2,23.9,23.9)), (reference, (23.9,10.2,23.9))):
            dims = tuple(bounds[wheel][i+3]-bounds[wheel][i] for i in range(3))
            if any(abs(a-b)>1e-6 for a,b in zip(dims, expected)):
                raise ValueError(f'Authored X-carriage wheel orientation changed: {wheel}')
        source = _centre(bounds[name])
        ref = _centre(bounds[reference])
        target = (ref[0], 2*midpoint-ref[1], ref[2])
        transform = (cq.Location(cq.Vector(*target)) *
                     cq.Location(cq.Vector(0,0,0), cq.Vector(0,0,1), -90) *
                     cq.Location(cq.Vector(*(-v for v in source))))
        poses[name] = transform * selected[name].loc
        records.append({'name':name, 'reference_wheel':reference,
                        'source_center_mm':source, 'target_center_mm':target,
                        'rotation_world_z_deg':-90,
                        'plate_midpoint_y_mm':midpoint,
                        'status':'reference_placement_owner_confirmed'})
    return poses, records
