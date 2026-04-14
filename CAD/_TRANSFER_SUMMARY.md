# M3-CRETE CAD — Session Transfer Summary

**Source session:** `746b75e6-fe00-404a-9578-a5e590a7d0bb.jsonl`
**Last activity:** 2026-04-11 13:08 UTC
**Branch/HEAD:** `main` @ `e04d6c5` (pushed) + uncommitted C.3 refactor work

---

## Where we are

- **74 parts, 0 interferences, 290/290 invariants passing** (as of msg 645, before latest parametric refactor).
- Phases C.1 (Z-motors) + C.2 (Z-idlers) + C.3 (Z-belts) **complete and pushed** as `3f29c09` (v0.3.0) and `e04d6c5` (track `.f3d`).
- Nick moved the **RL Z-motor + belts outbound** (outside frame envelope) in `M3-2_Assembly_user.step` to free interior volume for the Y-motor in C.4. Claude mirrored this in `m3_2_assembly.py` via a signature-based loader + a `RELOCATED={"RL"}` relaxation set.
- Nick then (msg 649) asked to extend this fix to **all 4 corners**: move the RL idler outbound too, widen belt gap from ±3.5mm to ±6.5mm (pulley width) on all corners, then commit/push before C.4.
- Claude started a **full parametric C.1→C.3 refactor** (msgs 651–666) so belts & idlers derive from loaded pulley positions — auto-follows any manual moves, widened gap applies globally, RL special-case removed.
- After refactor: **0 interferences, 74 parts, 16 s gen time**, but **5 invariant failures** on the RL idler because axle rotated from X to Y (dims became 22×12.7×22 instead of 12.7×22×22).
- Claude updated [CAD/preview_assembly.py](CAD/preview_assembly.py) idler invariants (msg 671) to match the new axle orientation. **Self-check re-run was started in background** (task `b9wxmhwwu`) and **never retrieved** — session ended mid-`wait`. Check the temp file or just re-run the self-check.

---

## IMMEDIATE next steps (resume here)

1. **Confirm the background self-check passed.** Re-run:
   ```
   cad_venv/Scripts/python.exe CAD/preview_assembly.py 2>&1 | tail -15
   ```
   Expect `XXX/XXX invariants pass` and no failures. If failures remain, they are all on the newly parametric C.2/C.3 geometry — inspect and fix invariants (NOT the geometry — geometry was already interference-clean).

2. **Commit the refactor.** Suggested message:
   > `refactor(cad): parametric C.1-C.3 loaders; widen belt gap to ±6.5; relocate idlers to follow pulleys`
   Stage: `CAD/m3_2_assembly.py`, `CAD/preview_assembly.py`, `CAD/M3-2_Assembly.step` (regenerated, 14.4 MB).
   Do NOT stage `.pkl` debug files or `_preview/`.

3. **Push to origin/main.**

4. **Then start Phase C.4 — Y-axis motion.**

---

## Phase C.4 — Y-axis motion (AGREED plan, not yet started)

From msgs 648 (Claude proposal) + 649 (Nick confirmation) + 654 (Claude correction):

| # | Decision | Value |
|---|---|---|
| 1 | Y-motor count | **2** (one per Y-rail, dual-drive anti-racking) |
| 2 | Y-motor position along rail | **Rear** end of each Y-rail (near Y=1200) |
| 3 | Y-motor mount hardware | **Same OMC StepperOnline ST-M2 L-bracket** already used for Z-motors (BOM qty 4→6) |
| 4 | Y-motor orientation | **Shaft pointing DOWN**, rotation axis = **Z** (NOT X as Claude initially assumed) |
| 5 | Y-belt termination | Clamps to **X-beam carriage plate** (2 plates, one per rail). X-beam slides along Y; Z-corner plates stay Y-fixed relative to Y-rails |

**BOM update required:** Replace old "Nema 23 flat mounting plates" with the new L-brackets; qty rises to 6 total (4 Z + 2 Y).

**Phase C.8 note (future, not now):** X-motor will reuse the exact subassembly from `V Slot Belt and Pinion Actuator 500mm.step` (full V_Slot variant, NOT Mini V), scaled to full X-beam length. Probe that STEP file when C.8 starts.

---

## Design constraints (locked earlier, still binding)

- **Global envelope rule:** everything stays inside `X[40,2440], Y[20,1220], Z[40,1120]` — nothing may get sheared off during transport. (The RL Z-motor relocation violates this; covered by "safety boxes or something" per Nick msg 603. Flag for future cover design.)
- **Z-motors at TOP** of posts (mud/concrete splatter protection).
- **Motor mounting plates double as corner reinforcement** (structural role).
- Z-motor rotation axis parallel to X.
- Y-motors mounted inside frame envelope (except where the C.4 refactor forces exceptions).
- "Use all resources to the max" — design ethos for structural compromises.

---

## Standing self-verification harness

After **every** edit to [CAD/m3_2_assembly.py](CAD/m3_2_assembly.py):

1. `cad_venv/Scripts/python.exe CAD/m3_2_assembly.py` — must print `[OK] No solid interferences`. The `EXCLUDE_PAIRS` list inside the script declares intentional overlaps. Add to it only for documented butt-joints / wheel-rail engagements.
2. `cad_venv/Scripts/python.exe CAD/preview_assembly.py` — runs ~290 engineering invariants and writes orthographic PNGs to `CAD/_preview/view_xy.png|view_xz.png|view_yz.png`. Read the PNGs back with the Read tool to visually self-check.

Both must pass before declaring work done.

---

## Open questions / known issues carried forward

- **RL Z-motor protrudes outside envelope** (X<0) — needs a cover/safety box in a later phase. Not blocking C.4.
- **The C.3 parametric refactor is untested post-idler-invariant-fix** — that's item #1 above.
- **Possible 4.7° belt angle on other corners** if pulley auto-positioning doesn't perfectly match `M3-2_Assembly_user.step` — verify in `view_yz.png` after rebuild.

---

## Key files

- [CAD/m3_2_assembly.py](CAD/m3_2_assembly.py) — main assembly script (build123d/cadquery hybrid), ~74 parts, v0.3.0
- [CAD/preview_assembly.py](CAD/preview_assembly.py) — self-check harness (invariants + PNG render)
- [CAD/M3-2_Assembly.step](CAD/M3-2_Assembly.step) — generated output, 14.4 MB, **tracked in git** (users review without rebuilding)
- [CAD/M3-2_Assembly_user.step](CAD/M3-2_Assembly_user.step) — Nick's manually-edited source-of-truth for moved/reshaped parts; signature-loaded by the script
- [CAD/Vendor/StepperOnline/N23_angled_mount.STEP](CAD/Vendor/StepperOnline/N23_angled_mount.STEP) — the L-bracket used for both Z and Y motors
- [CAD/_preview/](CAD/_preview/) — bbox_table.txt + 3 orthographic PNGs (gitignored)
- [CAD/_preview/bbox_table.txt](CAD/_preview/bbox_table.txt) — authoritative bbox dump after last rebuild

---

## Memory pointers (already saved)

- `~/.claude/projects/y--SunnydayTech-M3-CRETE/memory/workflow_cad_selfcheck.md` — the self-check workflow
- `~/.claude/projects/y--SunnydayTech-M3-CRETE/memory/reference_ai_cad_ecosystem.md` — PartCAD/build123d ecosystem snapshot

No memory file exists yet for the C.4 plan or the parametric-loader refactor — worth creating one after C.4 lands.
