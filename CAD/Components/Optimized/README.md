# Optimized OpenBuilds C-beam STEP

Original geometry: **OpenBuilds LLC and contributors**. The historical
[STEP Parts Library by Rob Stehlik](https://builds.openbuilds.com/projectresources/step-parts-library.162/)
is the upstream library reference; upstream availability may vary.

This directory and its modified STEP are distributed under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
See the [component attribution and license notice](../LICENSE.md).
No OpenBuilds endorsement or affiliation is implied.

## Direct downloads

- [Original supplier STEP, 708,294 bytes](https://raw.githubusercontent.com/sunnyday-technologies/M3-CRETE/main/CAD/Advanced/Linear%20Rail/C-Beam%2040x80x1000%20Linear%20Rail.step)
- [Optimized standalone STEP, 251,537 bytes](https://raw.githubusercontent.com/sunnyday-technologies/M3-CRETE/main/CAD/Components/Optimized/C-Beam_40x80x1000_optimized.step)

The optimized file is **64.4869% smaller** than the original supplier file.
It is the exact candidate used for the October 18, 2026 comparison, not a
replacement export created to match a published byte count.

## Changes and placement

Sunnyday Technologies omitted surface-parameter curve data, shared exact
duplicate geometric STEP records, and conservatively compacted whitespace.
No numeric precision reduction, profile simplification, topology merging,
hole removal, or cavity removal was applied.

The optimized file contains one 1000 mm C-beam in the assembly's
`cbeam_Xtop_0` world placement, rather than supplier-native coordinates.
Its geometry matches the supplier solid after the rigid `Xpositive`
orientation in `CAD/cbeam_solids.py` and a translation of approximately
(40, -6, 960) mm. It is a standalone component, not the complete assembly.

## Numerical verification, October 18, 2026

CadQuery 2.7.0 / OCP 7.8.1.1 reimport and supplier comparison passed:

- One valid solid, 294 faces, zero free edges and zero nonmanifold edges.
- Two end faces with eleven internal loops each.
- Matching face type, area and bounding-box fingerprints after rigid placement.
- Boolean difference: 0 mm3 added and 0 mm3 removed.

These are numerical CAD checks. Independent imports in other CAD applications
and physical validation have not been tested.

SHA-256:

| File | SHA-256 |
| --- | --- |
| Original supplier | `a29914be79093d6fb224c8031c35711afc8d3debebb535984c01d579f0bc3dc5` |
| Optimized standalone | `1c96606b54c88ae72ede0be6f2c8ba75f7bc8bbf17d0c002268e47f510b70919` |
