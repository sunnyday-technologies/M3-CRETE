# Z motor mount reference files

The latest owner-supplied **open-access STL** and the motor mounts in the full
M3-2 STEP are different revisions. The STL is provided separately and has not
been placed or qualified in the reference assembly. Do not treat the older
STEP as an editable equivalent of the new STL.

| File | Revision and scope |
|---|---|
| [Open-access STL, 2026-10-22](Custom/Z_NEMA23_Leadscrew_Motor_Mount_Open_Access_2026-10-22.stl) | Latest owner-supplied printable mesh, with lateral access to the coupler. Preserved byte for byte. Fit, fastening, print settings and physical performance still require review. |
| [M3-2 mount STEP](Custom/Z_NEMA23_Leadscrew_Motor_Mount_M3-2.step) | Older boxed mount used in the full reference assembly. Its STEP geometry does not represent the new open-access STL. |
| [Full M3-2 assembly](https://media.githubusercontent.com/media/sunnyday-technologies/M3-CRETE/main/CAD/M3-2_Assembly.step) | Owner-approved dual-plate X-carriage reference placement; all four Z mounts remain the older boxed revision. |

The newer mesh's measured shaft-to-tab relationship differs from the assembled
M3-2 mount. This observation does not establish compatibility or incompatibility.
A matching authored STEP and a reviewed placement are needed before replacing
the four mounts in the full assembly. No mesh-to-STEP conversion or inferred
mounting geometry is supplied.

BOM item 24 remains **four mounts**. Its older STEP link is retained and labelled;
the newer STL is a separate download. Purchasing quantities, suppliers and prices
are unchanged. The assembly renders show the older boxed mount.

The 2026-10-22 filename records receipt/release date, not the original design date.

## File identity

- New STL: 3,181,384 bytes; SHA-256 `6188126a4883c11b4d997c93449d34c7c4d45f9db5427f7b43f63790dfb02be6`.
- Full STEP: 5,134,822 bytes; SHA-256 `5d47e7a30f8de56bfd48f221d8add15aa5c191b45dbb1ae017f6df1c7575cba7`.

The [X-carriage review](X_CARRIAGE_REFERENCE_PLACEMENT.md) records the bounded
software checks and remaining contact, fastening and motor/plate questions.
Reference placement approval is not physical validation.
