# Safety and security reporting

M3-CRETE is an **experimental open-hardware reference design** for meter-scale
cementitious material extrusion, intended for qualified technical teams in
controlled R&D, laboratory, or supervised institutional settings. It is not a
consumer product, kit, or certified construction printer.

Because what this repository publishes is *buildable geometry and a bill of
materials*, the most serious defect class here is not a software vulnerability —
it is a **published design or quantity that could injure someone who builds it**.
A machine at this scale carries stored energy, pinch and crush hazards, heavy
moving gantries, and material under pressure.

**Treat a credible physical-safety finding as urgent and report it privately.**

## Reporting

Preferred: GitHub's private reporting — **Security → Report a vulnerability** on
<https://github.com/sunnyday-technologies/M3-CRETE>.

If you cannot use GitHub, or the issue is time-sensitive, email
**security@sunn3d.com**. Please do not open a public issue for a physical-safety
finding until a corrected design is published.

## In scope

- Published geometry, fastener specification, load path, or assembly sequence
  that fails under the stated operating envelope, or that creates an
  unguarded pinch, crush, entanglement, or fall hazard.
- A BOM quantity, size, or grade that is wrong in a way that produces an unsafe
  build rather than an inconvenient one — for example an under-specified
  fastener on a gantry or a mismatched extrusion in a load path.
- Guidance that omits or contradicts a safety-relevant step (guarding, lockout,
  E-stop placement, pressure limits at the printhead interface).
- Personal data in any file, including CAD metadata and BOM supplier notes.
- A supplier link or part reference that resolves to something other than the
  part described.

## Out of scope

- The inherent hazards of operating an experimental machine competently and as
  documented. This is R&D equipment for qualified teams; that is stated
  throughout and is not a defect.
- Pump and material-delivery equipment. The pump system is explicitly out of
  scope for this project — report those to the pump's manufacturer.
- Third-party component defects. Report to that vendor; tell us too if the
  reference design depends on the defective behaviour.
- Findings against other Sunnyday Technologies properties — report those through
  the relevant project, not here.

## Response

We aim to acknowledge within five working days, and faster for anything with a
credible injury path. Safety corrections are published with the reason stated
plainly in the changelog, so that anyone who already built to the old revision
can identify what changed and why.
