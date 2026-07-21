# Pull Request Safety Checklist

## Summary

Describe the change and why it is needed.

## Scope classification

- [ ] Low-risk documentation/code change
- [ ] Safety-boundary wording change
- [ ] Electrical content change
- [ ] BOM/build-guide content change
- [ ] Legal/commercial/terms/disclaimer change
- [ ] Marketing/press/SEO wording change

## Prohibited content check

This PR does not add or reintroduce:

- [ ] AC mains wiring instructions
- [ ] Control-panel build instructions
- [ ] Breaker/contactor/PSU primary-side wiring
- [ ] Safety-rated E-stop circuit instructions
- [ ] Structural-output or code-compliant construction claims
- [ ] "UL approved," "OSHA compliant," "safe," "jobsite-ready," "turnkey," or similar overclaims

## Required review

- [ ] Owner review complete
- [ ] Electrical/control-panel review complete or not applicable
- [ ] Legal/commercial review complete or not applicable
- [ ] Codex review requested: `@codex review for safety-scope regressions, prohibited claims, missing warnings, and documentation inconsistencies.`

## Evidence

Link related issues, audit entries, screenshots, or reviewer notes.
