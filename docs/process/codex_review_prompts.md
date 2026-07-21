# Codex Review Prompts

## General safety-scope review

@codex review for safety-scope regressions, prohibited claims, missing warnings,
and documentation inconsistencies. Specifically flag any public AC mains
instructions, control-panel build guidance, 48 V high-current distribution,
E-stop power-circuit design, UL/NRTL/AHJ overclaims, structural-use claims,
jobsite-ready claims, consumer/hobby framing, or school-safe language.

## Documentation consistency review

@codex review for inconsistent M3-CRETE public-scope language. Confirm that
README, DISCLAIMER, safety page, terms page, build guide, BOM pages, and
metadata all describe the public project as an experimental reference design
for qualified technical teams, with no public AC mains/control-panel
instructions and no structural-output guarantee.

## CI/static guard review

@codex review the content-guard script and make sure it catches prohibited
certification, safety, structural, jobsite, and mains-wiring phrases without
blocking approved disclaimer contexts.
