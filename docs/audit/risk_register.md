# M3-CRETE Public-Scope Risk Register

Opened: 2026-07-03 · Last updated: 2026-07-21

This register tracks public-scope cleanup risks. It is a working remediation
record, not a legal conclusion.

| ID | Severity | Risk | Affected paths | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R-001 | P0 | Public control-panel planner could be interpreted as control-panel build guidance despite disclaimers. | `control-panel/index.html`, `control-panel/tool.html`, `blog/control-panel-layout-tool/index.html`, `images/control-panel-tool.png` | Planner removed; announcement post replaced with a supersession notice; nav links and blog card removed; screenshot deleted. | **Closed 2026-07-21** — live-verified |
| R-002 | P0 | Homepage/README/build guide imply broad replication by anyone, jobsite/field use, or school/student use. | `index.html`, `README.md`, `build-guide/**` | Reframe as experimental reference for qualified teams in controlled R&D, lab, or supervised institutional settings. | **OPEN** — rewrite drafted, not landed. Owner review required |
| R-003 | P0 | Public BOM can look like a shopping list for high-current or professional electrical scope. | `bom/data.json`, `bom/index.html`, `config.js` | Power/safety items replaced with professional/private scope placeholders; conductor sizing removed; static table and variant config synced. | **Closed 2026-07-21** — live-verified |
| R-004 | P1 | SEO/social/press/blog metadata promotes control-panel planner or DIY framing. | `blog/**`, `press/**`, `sitemap.xml`, `.zenodo.json`, `llms.txt` | Planner navigation and promotion removed. Sitemap never listed the planner route. | **Closed 2026-07-21** for planner promotion. DIY-framing metadata rides with R-002 |
| R-005 | P1 | Contributors or agents may reintroduce prohibited claims or power-control guidance. | repo-wide | AGENTS rules, PR/issue templates, CODEOWNERS, review policy, and a warning-only static content guard. | **Closed 2026-07-21** — guard strengthened, see below |
| R-006 | Release blocker | Owner/legal/electrical review cannot be completed by an agent. | release package | Human sign-off. | **Reduced** — electrical arm closed by withdrawal; owner arm open |

## R-005: the original guard did not work

The guard as first written was verified against the pre-remediation tree on
2026-07-21 and reported **"no warnings"** on content that provably contained
`E-stop cuts 24V`, `30A contacts`, and `12AWG handles 25A`. It was a
marketing-claim linter (`UL approved`, `turnkey`, `jobsite ready`), not an
electrical-content check, and it would have given false assurance.

Three defects were fixed:

1. `.js` was not in the scanned suffixes, so `config.js` — which carries a copy
   of every BOM item name — was invisible to it.
2. `control-panel/**` and `blog/control-panel-layout-tool/**` were on the
   allow-list, exempting exactly the paths under remediation.
3. No term matched circuit-design or conductor-sizing phrasing.

The guard now also decodes `\uXXXX` escapes before scanning, because escaped
non-ASCII (an em dash in an item name) hid text from the plain scan. Re-run
against the pre-remediation tree it produces **15 warnings** across
`bom/data.json`, `bom/index.html`, and the planner post. It is still
warning-only and still not a substitute for reading the diff.

## R-006: scope after 2026-07-21

R-006 has three arms. One is closed, one is open, one is conditional.

**Electrical review — CLOSED, not applicable.** The drafts that required a
qualified electrical/control-panel reviewer were **withdrawn rather than
reviewed** (see below). No public M3-CRETE content now defines low-voltage
connector values, current limits, fuse behaviour, or professional power/control
scope, so there is nothing for an electrical reviewer to sign off. Re-opens
automatically if any such content is proposed again.

**Owner review — OPEN.** R-002 is the remaining public-scope risk. The rewrite
of `index.html`, `build-guide/**`, `press/**`, and `blog/index.html` is drafted
but not landed, and is a positioning decision, not a safety fix.

**Counsel review — CONDITIONAL.** Required only if the professional-user
acknowledgement, revised terms, or new disclaimer language ships. The
disclaimer and boundary text currently on `main`
(`DISCLAIMER.md`, `SAFETY_NOTICE.md`, `ELECTRICAL_SCOPE_BOUNDARY.md`) is
unchanged from before this remediation and is not gated by R-006.

## Withdrawn 2026-07-21 — electrical drafts

The following were drafted during the 2026-07-03 pass and are **withdrawn, not
published**:

- `docs/electrical/24v_low_voltage_interface.md`
- `docs/electrical/controller_enclosure_outline.md`
- `docs/electrical/professional_power_control_scope.md`
- `docs/electrical/electrical_scope_boundary.md`
- `docs/commercial/professional_user_acknowledgement_draft.md`

Rationale: every rating in the 24 V interface draft was `TBD by electrical
reviewer` — voltage range, maximum current, connector family, pinout, branch
fuse, reverse-polarity protection. Publishing an interface specification whose
values are all unresolved implies an interface is defined when it is not, which
is worse than publishing nothing. `ELECTRICAL_SCOPE_BOUNDARY.md` is already
public on `main` and already states what is and is not provided, which is the
job these drafts were written to do.

Withdrawing them removes the only content that required a licensed reviewer.

The drafts are preserved in the retired `safety/public-scope-freeze` bundle and
can be revived, but must not be published without qualified electrical review
and owner sign-off. The branch was never pushed to origin, so the bundle is the
only copy:

```
_cleanup-quarantine\m3-crete-public-scope-freeze-20260721.bundle   (25 MB, commit c04fe6e)
git init restore && cd restore && git fetch <bundle> "refs/heads/*:refs/heads/*"
```

Restore was tested on 2026-07-21 before the local branch was deleted: 262 files,
complete history, all five withdrawn documents recoverable.

## Release blockers

- Owner review required for all public-scope changes (R-002 outstanding).
- Counsel review required for disclaimer, terms, commercial, acknowledgement,
  and supersession language **if any of it changes**.
- Qualified electrical/control-panel review required for any future public text
  defining low-voltage connector values, current limits, fuse or
  current-limiting behaviour, operator interface boundaries, motor-driver
  enclosure constraints, or professional power/control scope.
