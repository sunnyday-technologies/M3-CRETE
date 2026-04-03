#!/usr/bin/env python3
"""Probe STEP file bounding boxes and orientations for assembly planning."""
import cadquery as cq
import os

STEP_DIR = os.path.join(os.path.dirname(__file__), "Components")

parts = [
    "V-Slot/V-Slot 20x80x1000 Linear Rail.step",
    "V-Slot/V-Slot 20x40x1000 Linear Rail.step",
    "Plates/V-Slot Gantry Plate 20-80mm.step",
    "Plates/Motor Mount Plate Nema 23.step",
    "Brackets/Cast Corner Bracket.step",
    "Electronics/Nema 23 Stepper Motor.step",
    "Electronics/Nema 23 High Torque Stepper Motor.STEP",
    "Wheels/Xtreme Solid V Wheel.step",
    "Pulleys/GT2 Timing Pulley 20 Tooth.step",
    "Pulleys/Smooth Idler Pulley Wheel.step",
    "Hardware/Eccentric Spacer 6mm.step",
    "Brackets/Cube Corner Connector.step",
    "Brackets/L Bracket Double.step",
    "Plates/Idler Pulley Plate.step",
    "Plates/Threaded Rod Plate Nema 23.step",
]

for relpath in parts:
    full = os.path.join(STEP_DIR, relpath)
    if not os.path.exists(full):
        print(f"MISSING: {relpath}")
        continue
    shape = cq.importers.importStep(full)
    bb = shape.val().BoundingBox()
    print(f"\n{relpath}")
    print(f"  BBox: X[{bb.xmin:.1f}, {bb.xmax:.1f}] Y[{bb.ymin:.1f}, {bb.ymax:.1f}] Z[{bb.zmin:.1f}, {bb.zmax:.1f}]")
    print(f"  Size: {bb.xmax-bb.xmin:.1f} x {bb.ymax-bb.ymin:.1f} x {bb.zmax-bb.zmin:.1f}")
    print(f"  Center: ({bb.center.x:.1f}, {bb.center.y:.1f}, {bb.center.z:.1f})")
