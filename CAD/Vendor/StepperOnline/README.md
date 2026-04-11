# Vendor-Provided CAD — OMC StepperOnline

This directory holds STEP files downloaded from third-party suppliers for
reference geometry in the M3-CRETE assembly model. These files are **not**
distributed under the M3-CRETE project license (CERN-OHL-W-2.0 for hardware,
CC BY-SA 4.0 for `CAD/Components/`). They remain the property of their
respective manufacturers and are redistributed here for the practical reason
that the assembly script needs the exact geometry to place the parts
correctly.

## Parts

### N23_angled_mount.STEP

- **Supplier:** OMC StepperOnline — <https://www.omc-stepperonline.com/>
- **Part number:** `ST-M2`
- **Product page:** <https://www.omc-stepperonline.com/nema-23-bracket-for-stepper-motor-and-geared-stepper-motor-alloy-steel-bracket-st-m2>
- **Material:** alloy steel
- **Use in M3-CRETE:** mounts each Z-axis NEMA23 stepper on top of the
  M3-2 frame at the four corners, with the motor shaft oriented parallel to
  the X-axis. Quantity: 4 per M3-2 build.

If OMC StepperOnline objects to redistribution of this STEP file, replace it
with a link-only reference in `bom/data.json` and delete this file from the
repository.
