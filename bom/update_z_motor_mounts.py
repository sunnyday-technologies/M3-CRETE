#!/usr/bin/env python3
"""
BOM update — 2026-04-11

Revise the "Z-Axis Motor Mounts" entry (id=24) to reflect Nick's decision to
use the OMC StepperOnline ST-M2 alloy steel NEMA23 L-bracket instead of a
stock flat plate. This bracket mounts on top of the frame and doubles as
corner reinforcement for the top X-rail / Y-brace / post junction.

Run this script once to apply the update. Verify by reloading
m3-crete.com/bom and checking the Z-Axis Motor Mounts entry.
"""
import json
from pathlib import Path

BOM = Path(__file__).parent / "data.json"

with BOM.open(encoding="utf-8") as f:
    d = json.load(f)

# Find the Z-Axis Motor Mounts entry
target = next(p for p in d["parts"] if p["id"] == 24)

target["name"] = "Z-Axis Motor Mount (NEMA23 Angled L-Bracket)"
target["description"] = (
    "NEMA 23 alloy steel angled L-bracket, mounted on top of the M3-2 frame "
    "at each post corner with the motor shaft oriented parallel to the X-axis. "
    "Replaces the flat motor mount plate used in earlier revisions. Doubles as "
    "corner reinforcement for the top X-rail / post junction. Cannot be easily "
    "3D-printed at this load rating, so single source from OMC StepperOnline."
)
target["mfg_type"] = "buy"
target["mpn"] = "ST-M2"
target["substitute_ok"] = True   # any equivalent NEMA23 angled bracket works
target["suppliers"] = [
    {
        "id": 72,
        "supplier_name": "OMC StepperOnline",
        "product_url": (
            "https://www.omc-stepperonline.com/nema-23-bracket-for-stepper-"
            "motor-and-geared-stepper-motor-alloy-steel-bracket-st-m2"
        ),
        "notes": (
            "ST-M2 NEMA 23 alloy steel bracket. 4 per M3-2 build. Mounts on top "
            "of frame; motor shaft parallel to X-axis."
        ),
        "sku": "ST-M2",
        "step_url": (
            "https://github.com/sunnyday-technologies/M3-CRETE/raw/main/"
            "CAD/Vendor/StepperOnline/N23_angled_mount.STEP"
        ),
        "approved": True,
    },
    {
        "id": 73,
        "supplier_name": "Amazon",
        "product_url": "https://www.amazon.com/s?k=NEMA+23+L+bracket+stepper",
        "notes": (
            "Generic NEMA23 alloy steel L-brackets are widely available. "
            "Verify dimensions match ST-M2 (65 x 69 x 69 mm)."
        ),
        "sku": None,
        "step_url": None,
        "approved": True,
    },
]

# Re-serialize with the same formatting style as the existing file
with BOM.open("w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Updated BOM id=24 'Z-Axis Motor Mounts'")
print(f"  name    : {target['name']}")
print(f"  mfg_type: {target['mfg_type']}")
print(f"  mpn     : {target['mpn']}")
print(f"  suppliers: {len(target['suppliers'])}")
