"""Compact our OCCT STEP exports without rounding or merging topology.

Only exact duplicate geometric records are shared. Quoted text, comments,
numeric tokens, units and assembly records are preserved. Validate the saved
candidate with verify_cbeam_candidate.py and self_check.py before promotion.
"""
from pathlib import Path
import re


GEOMETRY = frozenset({
    'CARTESIAN_POINT', 'DIRECTION', 'VECTOR', 'LINE', 'CIRCLE',
    'AXIS2_PLACEMENT_3D', 'AXIS2_PLACEMENT_2D', 'PLANE', 'CYLINDRICAL_SURFACE',
})
PROTECTED = re.compile(r"('(?:''|[^'])*'|/\*.*?\*/)", re.S)
RECORD = re.compile(r"#(\d+)\s*=\s*([A-Z_0-9]+)\s*(\((?:'(?:''|[^'])*'|[^';])*?\));", re.S)


def outside_strings(text, transform):
    return ''.join(part if i % 2 else transform(part)
                   for i, part in enumerate(PROTECTED.split(text)))


def validate_references(text):
    code = PROTECTED.sub('', text)
    ids = re.findall(r'#(\d+)\s*=', code)
    if len(ids) != len(set(ids)) or not set(re.findall(r'#(\d+)', code)) <= set(ids):
        raise ValueError('Duplicate definitions or dangling STEP references')


def compact_step_text(text):
    """Return compact text and an audit of removed geometry records."""
    removed, passes = {}, []
    validate_references(text)
    # Fail closed on embedded record-like literals rather than rewriting them.
    if any(RECORD.search(p) for p in PROTECTED.findall(text)):
        raise ValueError('Record-like literal is unsupported; preserve source')
    for _ in range(20):
        seen, mapping = {}, {}
        for match in RECORD.finditer(text):
            kind = match[2]
            if kind not in GEOMETRY:
                continue
            key = (kind, outside_strings(match[3], lambda s: re.sub(r'\s+', '', s)))
            number = int(match[1])
            if key in seen:
                mapping[number] = seen[key]
                removed[kind] = removed.get(kind, 0) + 1
            else:
                seen[key] = number
        if not mapping:
            break
        passes.append(len(mapping))
        text = RECORD.sub(lambda m: '' if int(m[1]) in mapping else m[0], text)
        text = outside_strings(text, lambda s: re.sub(
            r'#(\d+)', lambda m: '#' + str(mapping.get(int(m[1]), int(m[1]))), s))
    else:
        raise ValueError('Geometry deduplication did not converge')
    compact = outside_strings(text, lambda s: re.sub(
        r'\s*([=(),;])\s*', r'\1', re.sub(r'\s+', ' ', s)))
    strip = lambda s: outside_strings(s, lambda part: re.sub(r'\s+', '', part))
    if strip(text) != strip(compact):
        raise ValueError('Compaction changed non-whitespace text')
    validate_references(compact)
    return compact, {'removed_geometry_records': removed, 'passes': passes}


def export_compact_assembly(assembly, output):
    """Create a new candidate; never replace an existing export."""
    output = Path(output)
    if output.exists():
        raise FileExistsError('Candidate exists; choose a new output path')
    assembly.save(str(output), write_pcurves=False)
    text = output.read_text(encoding='ascii')
    compact, audit = compact_step_text(text)
    output.write_text(compact, encoding='ascii')
    return audit
