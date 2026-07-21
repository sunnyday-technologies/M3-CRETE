from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

INCLUDE_SUFFIXES = {
    ".cff",
    ".cjs",
    ".html",
    ".js",
    ".json",
    ".mjs",
    ".md",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".wrangler",
    ".cloudflare",
    "node_modules",
}

ALLOW_GLOBS = [
    "SAFETY_NOTICE.md",
    "ELECTRICAL_SCOPE_BOUNDARY.md",
    "DISCLAIMER.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "docs/audit/**",
    "docs/process/**",
    "docs/commercial/**",
    ".github/**",
]

TERMS = {
    "UL approved": "Avoid certification claims unless reviewed for the exact configuration.",
    "OSHA compliant": "Avoid compliance claims unless reviewed for the exact configuration.",
    "certified printer": "Do not imply the machine is certified.",
    "certified machine": "Do not imply the machine is certified.",
    "safe for schools": "Avoid school-safe claims.",
    "school-safe": "Avoid school-safe claims.",
    "jobsite ready": "Avoid jobsite-ready claims.",
    "jobsite-ready": "Avoid jobsite-ready claims.",
    "construction ready": "Avoid construction-ready claims.",
    "turnkey": "Avoid turnkey claims unless a reviewed commercial offer says so.",
    "plug and play": "Avoid plug-and-play claims.",
    "plug-and-play": "Avoid plug-and-play claims.",
    "code-compliant construction": "Avoid code-compliance claims.",
    "AC mains wiring instructions": "Use only in explicit disclaimers or process docs.",
    "wire line to neutral": "Remove public mains wiring guidance.",
    "120 VAC diagram": "Remove public mains wiring guidance.",
    "48 V power cabinet": "Remove public high-current power cabinet guidance.",
    "E-stop circuit diagram": "Remove public safety-rated circuit guidance.",
    "kills 24V": "Remove public emergency-stop power-circuit topology.",
    "via contactor": "Remove public emergency-stop power-circuit topology.",
    "via this contactor": "Remove public emergency-stop power-circuit topology.",
    "contactor coil": "Remove public emergency-stop power-circuit topology.",
    "NC contacts": "Remove public emergency-stop contact configuration.",
    "E-stop loop": "Remove public emergency-stop power-circuit topology.",
    "E-stop signal loop": "Remove public emergency-stop power-circuit topology.",
    "contacts minimum": "Remove public contactor/relay sizing.",
    "AWG handles": "Remove public conductor ampacity sizing.",
    "max draw at": "Remove public conductor ampacity sizing.",
}

NEGATION_MARKERS = (
    "not ",
    "does not ",
    "do not ",
    "no public ",
    "is not ",
    "are not ",
    "without ",
    "excluded",
    "excludes",
    "superseded",
)


def is_allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in ALLOW_GLOBS)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in INCLUDE_SUFFIXES:
            files.append(path)
    return files


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    if is_allowed(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [(0, "read-error", f"Could not read file: {exc}")]

    # JavaScript and JSON may escape non-ASCII (e.g. an em dash in an item
    # name) as \uXXXX, which hides the surrounding text from a plain scan.
    text = re.sub(
        r"\\u([0-9a-fA-F]{4})",
        lambda match: chr(int(match.group(1), 16)),
        text,
    )
    lines = text.splitlines()

    findings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        number = index + 1
        lower = line.lower()
        boundary_context = " ".join(lines[max(0, index - 2) : index + 1]).lower()
        for term, recommendation in TERMS.items():
            if re.search(re.escape(term), line, flags=re.IGNORECASE):
                if any(marker in lower or marker in boundary_context for marker in NEGATION_MARKERS):
                    continue
                findings.append((number, term, recommendation))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Warn on risky public-scope terms.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when findings exist.")
    args = parser.parse_args()

    total = 0
    for path in iter_files():
        findings = scan_file(path)
        for line, term, recommendation in findings:
            total += 1
            rel = path.relative_to(ROOT)
            print(f"{rel}:{line}: {term} - {recommendation}")

    if total:
        print(f"\npublic-scope guard: {total} warning(s)")
    else:
        print("public-scope guard: no warnings")

    return 1 if args.strict and total else 0


if __name__ == "__main__":
    sys.exit(main())
